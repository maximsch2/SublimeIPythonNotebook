- Opening empty new notebooks doesn't work. Should also support creating new notebooks from ST
- Support set_next_input
- Correctly handle 'dead' message from the kernel
- Add support for creating/renaming notebooks
- Add an option of saving a backup copy of notebook json file (use git to have all copies?):
    - For now it is possible to use inb_open_as_ipynb command
- Use scopes to highlight python code only inside input cells

Bugs:

Traceback (most recent call last):
  File "./sublime_plugin.py", line 337, in run_
  File "./subl_ipy_notebook.py", line 584, in run
  File "./ipy_connection.py", line 26, in get_notebooks
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 126, in urlopen
    return _opener.open(url, data, timeout)
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 391, in open
    response = self._open(req, data)
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 409, in _open
    '_open', req)
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 369, in _call_chain
    result = func(*args)
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 1181, in http_open
    return self.do_open(httplib.HTTPConnection, req)
  File "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/urllib2.py", line 1156, in do_open
    raise URLError(err)
urllib2.URLError: <urlopen error [Errno 61] Connection refused>
Unhandled exception in thread started by <bound method Kernel.process_messages of <ipy_connection.Kernel object at 0x10d694a50>>
Traceback (most recent call last):
  File "./ipy_connection.py", line 308, in process_messages
    cb(msg_type, content)
  File "./ipy_connection.py", line 365, in callback
    matches[:] = content["matches"][:]
KeyError: 'matches'


Completion for directories works bad