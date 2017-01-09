# -*- coding: utf-8 -*-
# Copyright (c) 2013, Maxim Grechkin
# This file is licensed under GNU General Public License version 3
# See COPYING for details.
import json
import uuid

from time import sleep
import threading
import queue

from collections import defaultdict

import re
import sys
import _thread
from .external import nbformat
from .external.websocket import websocket3 as websocket
from .external.websocket.websocket3 import *
from urllib.request import urlopen, Request, ProxyHandler, build_opener, install_opener, HTTPCookieProcessor
from urllib.parse import urlparse, urlencode
from http.cookiejar import CookieJar

def install_proxy_opener():
    global cookies
    cookies=CookieJar()
    proxy = ProxyHandler({})
    opener = build_opener(proxy, HTTPCookieProcessor(cookies))
    install_opener(opener)

def create_uid():
    return str(uuid.uuid4())

def get_notebooks(baseurl, psswd=None):
    try:
        if psswd!=None:
            target_url=baseurl+'''/login?next=%2F'''
            urlopen(target_url, data=urlencode({'password': psswd}).encode('utf8'))
        target_url = baseurl + "/api/contents"
        req = urlopen(target_url)
        encoding = req.headers.get_content_charset()
        if encoding is None:
            encoding  = "utf8"
        body = req.readall().decode(encoding)
        if '<input type="password" name="password" id="password_input">' in body:
            return 'psswd'
        data = json.loads(body)
        return data
    except Exception as e:
        print("Error during loading notebook list from ", target_url)
        print(e)
        return None

def create_new_notebook(baseurl):
    try:
        req = urlopen(baseurl + "/new")
        encoding = req.headers.get_content_charset()
        body = req.readall().decode(encoding)
        import re
        match =  re.search("data-notebook-id=(.*)", body)
        nbid = match.groups()[0]
        return nbid
    except :
        raise
    return None

def convert_mime_types(obj, content):
    if not content:
        return obj

    if "text/plain" in content:
        obj.text = content["text/plain"]

    if "text/html" in content:
        obj.html = content["text/html"]

    if "image/svg+xml" in content:
        obj.svg = content["image/svg+xml"]

    if "image/png" in content:
        obj.png = content["image/png"]

    if "image/jpeg" in content:
        obj.jpeg = content["image/jpeg"]

    if "text/latex" in content:
        obj.latex = content["text/latex"]

    if "application/json" in content:
        obj.json = content["application/json"]

    if "application/javascript" in content:
        obj.javascript = content["application/javascript"]

    return obj


class Notebook(object):
    def __init__(self, s, path):
        data = json.loads(s)["content"]
        self._notebook = nbformat.to_notebook(data)
        self._cells = self._notebook.cells
        self.notebook_view = None
        self.path = path

    def __str__(self):
        return nbformat.writes_json(self._notebook)

    def get_cell(self, cell_index):
        return Cell(self._cells[cell_index])

    @property
    def cell_count(self):
        return len(self._cells)

    def create_new_cell(self, position, cell_type):
        if cell_type == "code":
            new_cell = nbformat.new_code_cell(input="")
        elif (cell_type == "markdown") or (cell_type == "raw"):
            new_cell = nbformat.new_text_cell(cell_type, source="")

        if position < 0:
            position = len(self._cells)
        self._cells.insert(position, new_cell)
        return Cell(new_cell)

    def delete_cell(self, cell_index):
        del self._cells[cell_index]

    def name():
        doc = "The name property."

        def fget(self):
            return self.path # elf._notebook.metadata.name
        def fset(self, value):
            pass
            #self._notebook.metadata.name = value
        return locals()
    name = property(**name())


MAX_OUTPUT_SIZE = 5000


class Cell(object):
    def __init__(self, obj):
        self._cell = obj
        self.runnig = False
        self.cell_view = None

    @property
    def cell_type(self):
        return self._cell.cell_type

    def source():
        doc = "The source property."

        def fget(self):
            return "".join(self._cell.source)

        def fset(self, value):
            self._cell.source = value
        return locals()
    source = property(**source())

    @property
    def output(self):
        result = []
        for output in self._cell.outputs:
            if "text" in output:
                result.append(output.text)
            elif "traceback" in output:
                data = "\n".join(output.traceback)
                data = re.sub("\x1b[^m]*m", "", data)  # remove escape characters
                result.append(data)
                if not data.endswith("\n"):
                    result.append("\n")
        result = "".join(result)
        if len(result) > MAX_OUTPUT_SIZE:
            result = result[:MAX_OUTPUT_SIZE] + "..."
        return result

    def on_output(self, msg_type, content):
        output = None
        content = defaultdict(lambda: None, content)  # an easy way to avoid checking all parameters
        if msg_type == "stream":
            output = nbformat.new_output(msg_type, content["data"], stream=content["name"])
        elif msg_type == "pyerr":
            output = nbformat.new_output(msg_type, traceback=content["traceback"], ename=content["ename"], evalue=content["evalue"])
        elif msg_type == "pyout":
            output = nbformat.new_output(msg_type, prompt_number=content["prompt_number"])
            convert_mime_types(output, content["data"])
        elif msg_type == "display_data":
            output = nbformat.new_output(msg_type, prompt_number=content["prompt_number"])
            convert_mime_types(output, content["data"])
        else:
            raise Exception("Unknown msg_type")

        if output:
            self._cell.outputs.append(output)
            if self.cell_view:
                self.cell_view.update_output()

    def on_execute_reply(self, msg_id, content):
        self.running = False
        if 'execution_count' in content:
            self._cell.prompt_number = content['execution_count']
        self.cell_view.on_execute_reply(msg_id, content)

    @property
    def prompt(self):
        if 'prompt_number' in self._cell:
            return str(self._cell.prompt_number)
        else:
            return " "

    def run(self, kernel):
        if self.cell_type != "code":
            return

        self._cell.prompt_number = '*'
        self._cell.outputs = []
        if self.cell_view:
            self.cell_view.update_output()
            self.cell_view.update_prompt_number()

        kernel.run(self.source, output_callback=self.on_output,
                   execute_reply_callback=self.on_execute_reply)


output_msg_types = set(["stream", "display_data", "pyout", "pyerr"])


class Kernel(object):
    def __init__(self, notebook_id, baseurl):
        self.notebook_id = notebook_id
        self.session_id = create_uid()
        self.baseurl = baseurl
        self.shell = None
        self.iopub = None

        self.shell_messages = []
        self.iopub_messages = []
        self.running = False
        self.message_queue = queue.Queue()
        self.message_callbacks = dict()
        #self.start_kernel()
        _thread.start_new_thread(self.process_messages, ())
        self.status_callback = lambda x: None
        self.encoding = 'utf-8'

    @property
    def kernel_id(self):
        id = self.get_kernel_id()
        if id is None:
            self.start_kernel()
            return self.get_kernel_id()
        return id

    def get_kernel_id(self):
        notebooks = get_notebooks(self.baseurl)
        for nb in notebooks:
            if nb["notebook_id"] == self.notebook_id:
                return nb["kernel_id"]
        raise Exception("notebook_id not found")

    def start_kernel(self):
        url = self.baseurl + "/kernels?notebook=" + self.notebook_id
        req = urlopen(url, data=b"")  # data="" makes it POST request
        req.read()
        self.create_websockets()

    def restart_kernel(self):
        url = self.baseurl + "/kernels/" + self.kernel_id + "/restart"
        req = urlopen(url, data=b"")
        req.read()
        self.create_websockets()
        self.status_callback("idle")

    def interrupt_kernel(self):
        url = self.baseurl + "/kernels/" + self.kernel_id + "/interrupt"
        req = urlopen(url, data=bytearray(b""))
        req.read()

    def shutdown_kernel(self):
        url = self.baseurl + "/kernels/" + self.kernel_id
        req = Request(url)
        req.add_header("Content-Type", "application/json")
        req.get_method = lambda: "DELETE"
        data = urlopen(req)
        data.read()
        self.status_callback("closed")

    def get_notebook(self):
        url = self.notebook_url
        print("URL: " + url)
        req = urlopen(url)
        data = req.readall().decode(self.encoding)
        return Notebook(data, self.notebook_id)
        try:
            return Notebook(req.readall().decode(self.encoding))
        except AttributeError:
            return Notebook(req.read())

    @property
    def notebook_url(self):
        return self.baseurl + "/api/contents/" + self.notebook_id

    def save_notebook(self, notebook):
        request = Request(self.notebook_url, str(notebook).encode(self.encoding))
        request.add_header("Content-Type", "application/json")
        request.get_method = lambda: "PUT"
        data = urlopen(request)
        data.read()

    def on_iopub_msg(self, msg):
        m = json.loads(msg)
        self.iopub_messages.append(m)
        self.message_queue.put(m)

    def on_shell_msg(self, msg):
        m = json.loads(msg)
        self.shell_messages.append(m)
        self.message_queue.put(m)

    def register_callbacks(self, msg_id, output_callback,
                           clear_output_callback=None,
                           execute_reply_callback=None,
                           set_next_input_callback=None):
        callbacks = {"output": output_callback}
        if clear_output_callback:
            callbacks["clear_output"] = clear_output_callback
        if execute_reply_callback:
            callbacks["execute_reply"] = execute_reply_callback
        if set_next_input_callback:
            callbacks["set_next_input"] = set_next_input_callback

        self.message_callbacks[msg_id] = callbacks

    def process_messages(self):
        while True:
            m = self.message_queue.get()
            content = m["content"]
            msg_type = m["header"]["msg_type"]

            if ("parent_header" in m) and ("msg_id" in m["parent_header"]):
                parent_id = m["parent_header"]["msg_id"]
            else:
                parent_id = None

            if msg_type == "status":
                if "execution_state" in content:
                    self.status_callback(content["execution_state"])

            elif parent_id in self.message_callbacks:
                callbacks = self.message_callbacks[parent_id]
                cb = None
                if msg_type in output_msg_types:
                    cb = callbacks["output"]
                elif (msg_type == "clear_output") and ("clear_output" in callbacks):
                    cb = callbacks["clear_output"]
                elif (msg_type == "execute_reply") and ("execute_reply" in callbacks):
                    cb = callbacks["execute_reply"]
                elif (msg_type == "set_next_input") and ("set_next_input" in callbacks):
                    cb = callbacks["set_next_input"]
                elif (msg_type == "complete_reply") and ("complete_reply" in callbacks):
                    cb = callbacks["complete_reply"]

                if cb:
                    cb(msg_type, content)

            self.message_queue.task_done()

    def create_get_output_callback(self, callback):
        def grab_output(msg_type, content):
            if msg_type == "stream":
                callback(content["data"])
            elif msg_type == "pyerr":
                data = "\n".join(content["traceback"])
                data = re.sub("\x1b[^m]*m", "", data)  # remove escape characters
                callback(data)
            elif msg_type == "pyout":
                callback(content["data"]["text/plain"])
            elif msg_type == "display_data":
                callback(content["data"]["text/plain"])

        return grab_output

    def create_websockets(self):
        if self.shell is not None:
            self.shell.close()

        if self.iopub is not None:
            self.iopub.close()

        url = self.baseurl.replace('http', 'ws') + "/kernels/" + self.kernel_id + "/"
        auth=''.join([c.name+'='+c.value for c in cookies])
        self.shell = websocket.WebSocketApp(url=url + "shell",
                                            on_message=lambda ws, msg: self.on_shell_msg(msg),
                                            on_open=lambda ws: ws.send(auth),
                                            on_error=lambda ws, err: print(err))
        self.iopub = websocket.WebSocketApp(url=url + "iopub",
                                            on_message=lambda ws, msg: self.on_iopub_msg(msg),
                                            on_open=lambda ws: ws.send(auth),
                                            on_error=lambda ws, err: print(err))

        _thread.start_new_thread(self.shell.run_forever, ())
        _thread.start_new_thread(self.iopub.run_forever, ())
        sleep(1)
        self.running = True

    def create_message(self, msg_type, content):
        msg = dict(
            header=dict(
                msg_type=msg_type,
                username="username",
                session=self.session_id,
                msg_id=create_uid()),
            content=content,
            parent_header={},
            metadata={})
        return msg

    def send_shell(self, msg):
        if not self.running:
            self.create_websockets()
        self.shell.send(json.dumps(msg))

    def get_completitions(self, line, cursor_pos, text="", timeout=1):
        msg = self.create_message("complete_request",
                                  dict(line=line, cursor_pos=cursor_pos, text=text))
        msg_id = msg["header"]["msg_id"]
        ev = threading.Event()
        matches = []

        def callback(msg_id, content):
            if "matches" in content:
                matches[:] = content["matches"][:]
            ev.set()
        callbacks = {"complete_reply": callback}
        self.message_callbacks[msg_id] = callbacks
        self.send_shell(msg)
        ev.wait(timeout)
        del self.message_callbacks[msg_id]
        return matches

    def run(self, code, output_callback,
            clear_output_callback=None,
            execute_reply_callback=None,
            set_next_input_callback=None):
        msg = self.create_message("execute_request",
                                  dict(code=code, silent=False,
                                  user_variables=[], user_expressions={},
                                  allow_stdin=False))

        msg_id = msg["header"]["msg_id"]
        self.register_callbacks(msg_id,
                                output_callback,
                                clear_output_callback,
                                execute_reply_callback,
                                set_next_input_callback)
        self.send_shell(msg)
