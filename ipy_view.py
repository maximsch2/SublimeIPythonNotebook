# -*- coding: utf-8 -*-
# Copyright (c) 2013, Maxim Grechkin
# This file is licensed under GNU General Public License version 3
# See COPYING for details.
from __future__ import print_function
import sublime
try:
    from . import ipy_connection
except:
    import ipy_connection
import re



def create_kernel(baseurl, notebook_id):
    return ipy_connection.Kernel(notebook_id, baseurl)

output_draw_style = sublime.HIDDEN
input_draw_style = sublime.HIDDEN
cell_draw_style = sublime.HIDDEN


class BaseCellView(object):
    def __init__(self, index, view, cell):
        self.index = index
        self.view = view
        self.cell = cell
        self.cell.cell_view = self
        self.buffer_ready = False
        self.owned_regions = ["inb_input"]

    def get_cell_region(self):
        try:
            reg = self.view.get_regions("inb_cells")[self.index]
            return sublime.Region(reg.a+1, reg.b)
        except IndexError:
            return None

    def run(self, kernel, region):
        pass

    def get_region(self, regname):
        cell_reg = self.get_cell_region()
        if cell_reg is None:
            return None
        all_regs = self.view.get_regions(regname)
        for reg in all_regs:
            if cell_reg.contains(reg):
                res = sublime.Region(reg.a+1, reg.b-1)
                return res
        return None

    def get_input_region(self):
        return self.get_region("inb_input")

    def write_to_region(self, edit, regname, text):
        if text is None:
            return
        if text.endswith("\n"):
            text = text[:-1]
        region = self.get_region(regname)
        self.view.set_read_only(False)
        self.view.replace(edit, region, text)

    def select(self, last_line=False):
        input_region = self.get_input_region()
        if input_region is None:
            return

        if last_line:
            pos = self.view.line(input_region.b).a
        else:
            pos = input_region.a

        self.view.sel().clear()
        self.view.sel().add(sublime.Region(pos, pos))
        self.view.show_at_center(pos)

    def setup(self, edit):
        self.buffer_ready = True

    def teardown(self, edit):
        cell_reg = self.get_cell_region()
        for regname in self.owned_regions:
            all_regs = self.view.get_regions(regname)
            all_regs = [reg for reg in all_regs if not cell_reg.contains(reg)]
            self.view.add_regions(regname, all_regs, "source.python", "", input_draw_style)
        self.view.erase(edit, sublime.Region(cell_reg.a, cell_reg.b-1))

    def draw(self, edit):
        if not self.buffer_ready:
            self.setup(edit)

    def get_input_content(self):
        input_region = self.get_input_region()
        if input_region:
            return self.view.substr(input_region)
        else:
            return ""

    def check_R(self):
        pass


class CodeCellView(BaseCellView):
    def __init__(self, nbview, index, view, cell):
        BaseCellView.__init__(self, index, view, cell)
        self.running = False
        self.nbview = nbview
        self.owned_regions.append("inb_output")
        self.old_is_R = self.is_R_cell()
        self.old_prompt_number = -1

    @property
    def prompt(self):
        return self.cell.prompt

    def run(self, kernel):
        if self.running:
            print("Warning")
            print("Cell is already running")
            return

        self.running = True
        code = self.get_code()
        self.cell.source = code
        self.cell.run(kernel)

    def setup(self, edit):
        BaseCellView.setup(self, edit)
        region = self.get_cell_region()
        start = region.a

        view = self.view

        self.view.set_read_only(False)

        start = start + view.insert(edit, start, self.get_input_prompt() % self.prompt)
        end = start + view.insert(edit, start, "\n\n")

        reg = sublime.Region(start, end)
        regs = view.get_regions("inb_input")
        regs.append(reg)
        view.add_regions("inb_input", regs, "source.python", "", input_draw_style)
        self.view.set_read_only(False)

        end = end + view.insert(edit, end, "#/Input[%s]\n\n#Output[%s]" % (self.prompt, self.prompt))

        start = end
        end = start + view.insert(edit, start, "\n\n")

        reg = sublime.Region(start, end)
        regs = view.get_regions("inb_output")
        regs.append(reg)
        view.add_regions("inb_output", regs, "string", "", output_draw_style)
        self.view.set_read_only(False)

        end = end + view.insert(edit, end, "#/Output")

    def update_output(self):
        def run_command():
            self.view.run_command("inb_insert_output", {"cell_index": self.index})
        sublime.set_timeout(run_command, 0)

    def on_execute_reply(self, msg_id, content):
        self.running = False
        self.update_prompt_number()
        if "payload" in content:
            for p in content["payload"]:
                if (p["source"] == "IPython.zmq.page.page") or (p["source"] == "IPython.kernel.zmq.page.page"):
                    self.nbview.on_pager(p["text"])

    def update_prompt_number(self):
        def do_set():
            self.view.run_command('rewrite_prompt_number', {"cell_index": self.index})

        try:
            self.view.run_command('rewrite_prompt_number', {"cell_index": self.index})
        except:
            sublime.set_timeout(do_set, 0)

    def get_input_prompt(self):
        if self.is_R_cell():
            return "#Input-R[%s]"
        else:
            return "#Input[%s]"

    def is_R_cell(self):
        code = self.get_input_content()
        if code == "":
            code = self.cell.source
        return (len(code) >= 3) and (code[:3] == '%%R')

    def check_R(self):
    	if self.old_is_R != self.is_R_cell():
    		self.update_prompt_number()

    def rewrite_prompt_number(self, edit):
        if (self.prompt == self.old_prompt_number) and (self.old_is_R == self.is_R_cell()):
            return

        self.old_prompt_number = self.prompt
        self.old_is_R = self.is_R_cell()

        inp_reg = self.get_input_region()
        line = self.view.line(inp_reg.begin() - 1)
        self.view.replace(edit, line, self.get_input_prompt() % self.prompt)

        inp_reg = self.get_input_region()
        line = self.view.line(inp_reg.end() + 2)
        self.view.replace(edit, line, "#/Input[%s]" % self.prompt)

        out_reg = self.get_region("inb_output")
        line = self.view.line(out_reg.begin() - 1)
        self.view.replace(edit, line, "#Output[%s]" % self.prompt)



    def output_result(self, edit):
        output = self.cell.output
        output = "\n".join(map(lambda s: " " + s, output.splitlines()))
        self.write_to_region(edit, "inb_output", output)

    def draw(self, edit):
        BaseCellView.draw(self, edit)
        self.write_to_region(edit, "inb_input", self.cell.source)
        self.output_result(edit)

    def get_code(self):
        return self.get_input_content()

    def update_code(self):
        self.cell.source = self.get_code()


class TextCell(BaseCellView):
    def run(self, kernel):
        print("Cannot run Markdown cell")

    def get_cell_title(self):
        if self.cell.cell_type == "markdown":
            return "Markdown"
        elif self.cell.cell_type == "raw":
            return "Raw text"
        elif self.cell.cell_type == "heading":
            return "Heading"
        else:
            print("Unknwon cell type: " + str(self.cell.cell_type))
            return "Unknown"

    def setup(self, edit):
        BaseCellView.setup(self, edit)
        region = self.get_cell_region()
        start = region.a

        view = self.view

        self.view.set_read_only(False)

        start = start + view.insert(edit, start, "#" + self.get_cell_title())
        end = start + view.insert(edit, start, "\n\n")

        reg = sublime.Region(start, end)
        regs = view.get_regions("inb_input")
        regs.append(reg)
        view.add_regions("inb_input", regs, "source.python", "", input_draw_style)
        self.view.set_read_only(False)

        end = end + view.insert(edit, end, "#/" + self.get_cell_title())

    def on_execute_reply(self, msg_id, content):
        raise Exception("Shouldn't get this")

    def draw(self, edit):
        BaseCellView.draw(self, edit)
        self.write_to_region(edit, "inb_input", self.cell.source)

    def get_source(self):
        return self.get_input_content()

    def update_code(self):
        self.cell.source = self.get_source()


class NotebookView(object):
    def __init__(self, view, notebook_id, baseurl):
        self.view = view
        self.baseurl = baseurl
        view.set_scratch(True)
        #view.set_syntax_file("Packages/Python/Python.tmLanguage")
        view.set_syntax_file("Packages/IPython Notebook/SublimeIPythonNotebook.tmLanguage")
        view.settings().set("ipython_notebook", True)
        self.cells = []
        self.notebook_id = notebook_id
        self.kernel = create_kernel(baseurl, notebook_id)
        self.kernel.status_callback = self.on_status
        self.on_status("idle")
        self.notebook = self.kernel.get_notebook()
        self.modified = False
        self.show_modified_status(False)

        self.set_name(self.notebook.name)


    def get_name(self):
        return self.notebook.name

    def set_name(self, new_name):
        self.notebook.name = new_name
        self.view.set_name("IPy Notebook - " + self.notebook.name)

    def get_cell_separator(self):
        return "\n\n"

    def on_sel_modified(self):
        readonly = True
        regset = self.view.get_regions("inb_input")

        first_cell_index = -1
        for s in self.view.sel():
            readonly = True
            for i, reg in enumerate(regset):
                reg = sublime.Region(reg.begin()+1, reg.end()-1)
                if reg.contains(s):
                    if first_cell_index < 0:
                        first_cell_index = i
                    readonly = False
                    break
            if readonly:
                break

        if first_cell_index >= 0:
            self.highlight_cell(regset[first_cell_index])
        else:
            self.view.erase_regions("inb_highlight")

        self.view.set_read_only(readonly)

    def show_modified_status(self, val):
        if val:
            state = "modified"
        else:
            state = "saved"

        def set_status():
            self.view.set_status("NotebookStatus", "notebook: " + state)
        sublime.set_timeout(set_status, 0)

    def set_modified(self, new_val):
        if self.modified != new_val:
            self.show_modified_status(new_val)
        self.modified = new_val

    def on_modified(self):
        self.set_modified(True)

        regset = self.view.get_regions("inb_input")

        for s in self.view.sel():
            for i, reg in enumerate(regset):
                reg = sublime.Region(reg.begin()+1, reg.end()-1)
                if reg.contains(s) and (i < len(self.cells)):
                    self.cells[i].check_R()
                    break

    def highlight_cell(self, input_region):
        reg = self.view.line(input_region.begin()-2)
        reg2 = self.view.line(input_region.end()+2)
        self.view.add_regions("inb_highlight", [reg, reg2], "ipynb.source.highlight", "", sublime.DRAW_EMPTY)

    def on_backspace(self):
        s = self.view.sel()[0]

        regset = self.view.get_regions("inb_input")
        for reg in regset:
            reg = sublime.Region(reg.begin()+2, reg.end())
            if reg.contains(s):
                self.view.run_command("left_delete")
                return
            elif (reg.size() > 2) and (s.begin() == reg.begin() - 1) and (self.view.substr(s.begin()) == "\n"):
                self.view.run_command("left_delete")
                self.view.run_command("move", {"by": "characters", "forward": True})
                return

    def add_cell(self, edit, start=-1):
        view = self.view
        if start < 0:
            start = view.size()

        self.view.set_read_only(False)
        start = start + view.insert(edit, start, self.get_cell_separator())
        end = start + view.insert(edit, start, "\n\n")

        reg = sublime.Region(start, end)
        regs = view.get_regions("inb_cells")
        regs.append(reg)
        view.add_regions("inb_cells", regs, "", "", cell_draw_style)

        return reg

    def insert_cell_field(self, edit, pos=0):
        cell_regions = self.view.get_regions("inb_cells")
        assert len(self.cells) == len(cell_regions)

        if (pos < 0) or (pos > len(self.cells)):
            raise Exception("Wrong position to insert cell field")

        if pos > 0:
            pos = cell_regions[pos-1].b

        self.add_cell(edit, start=pos)

    def run_cell(self, edit, inplace):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        cell = self.get_cell_by_index(cell_index)
        if not cell:
            raise Exception("Cell not found")
        if not inplace:
            if cell_index == len(self.cells) - 1:
                self.insert_cell_at_position(edit, cell_index + 1)
        cell.run(self.kernel)
        if not inplace:
            self.move_to_cell(False)

    def get_cell_by_index(self, cell_index):
        res = self.cells[cell_index]
        res.view = self.view
        return res

    def get_current_cell_index(self):
        sel = self.view.sel()
        if len(sel) > 1:
            return -1
        sel = self.view.sel()[0]
        regions = self.view.get_regions("inb_cells")
        return self.find_cell_by_selection(sel, regions)

    def find_cell_by_selection(self, sel, regions):
        for i, reg in enumerate(regions):
            if reg.contains(sel):
                return i
        return -1

    def save_notebook(self):
        self.kernel.save_notebook(self.notebook)
        self.set_modified(False)

    def render_notebook(self, edit):
        self.cells = []
        self.view.erase_regions("inb_cells")
        self.view.erase_regions("inb_input")
        self.view.erase_regions("inb_output")
        for i in range(self.notebook.cell_count):
            self.insert_cell_field(edit, i)
            cell = self.notebook.get_cell(i)
            cell_view = self.create_cell_view(i, self.view, cell)
            self.cells.append(cell_view)

        regions = self.view.get_regions("inb_cells")
        assert len(self.cells) == len(regions)

        for cell in self.cells:
            cell.draw(edit)

        if len(self.cells) > 0:
            self.cells[0].select()

        sublime.set_timeout(lambda : self.set_modified(False), 0)

    def update_notebook_from_buffer(self):
        for cell in self.cells:
            cell.update_code()

    def restart_kernel(self):
        for cell in self.cells:
            if isinstance(cell, CodeCellView):
                cell.running = False
        self.kernel.restart_kernel()


    def on_status(self, execution_state):
        def set_status():
            self.view.set_status("ExecutionStatus", "kernel: " + execution_state)
        sublime.set_timeout(set_status, 0)

    def handle_completions(self, view, prefix, locations):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return None
        if not isinstance(self.cells[cell_index], CodeCellView):
            return None
        sel = view.sel()
        if len(sel) > 1:
            return []
        sel = sel[0]
        line = view.substr(view.line(sel))
        row, col = view.rowcol(sel.begin())
        compl = self.kernel.get_completitions(line, col, timeout=0.7)


        if len(compl) > 0:
            def get_last_word(s): # needed for file/directory completion
                if s.endswith("/"):
                    s = s[:-1]
                res = s.split("/")[-1]
                return res

            return ([(s + "\t (IPython)", get_last_word(s)) for s in compl], sublime.INHIBIT_EXPLICIT_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS)
        else:
            return None

    def delete_current_cell(self, edit):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        self.update_notebook_from_buffer()
        self.notebook.delete_cell(cell_index)
        del self.cells[cell_index]
        for cell in self.cells:
            if cell.index >= cell_index:
                cell.index -= 1

        regions = self.view.get_regions("inb_cells")
        reg = regions[cell_index]
        self.view.erase(edit, self.view.full_line(sublime.Region(reg.a, reg.b-1)))
        regions = self.view.get_regions("inb_cells")
        del regions[cell_index]
        self.view.add_regions("inb_cells", regions, "", "", cell_draw_style)
        new_cell_index = cell_index - 1 if cell_index > 0 else 0
        self.cells[new_cell_index].select()

    def insert_cell_below(self, edit):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        self.insert_cell_at_position(edit, cell_index + 1)

    def insert_cell_above(self, edit):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        self.insert_cell_at_position(edit, cell_index)

    def insert_cell_at_position(self, edit, cell_index):
        self.update_notebook_from_buffer()
        for cell in self.cells:
            if cell.index >= cell_index:
                cell.index += 1

        new_cell = self.notebook.create_new_cell(cell_index, "code")
        new_view = self.create_cell_view(cell_index, self.view, new_cell)
        self.insert_cell_field(edit, cell_index)
        self.cells.insert(cell_index, new_view)
        new_view.draw(edit)
        new_view.select()

    def move_up(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            reg = self.cells[cell_index].get_input_region()
            if self.view.line(reg.begin()) == self.view.line(sel):
                if cell_index > 0:
                    self.cells[cell_index-1].select(last_line=True)
                return True
        return False

    def move_down(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            reg = self.cells[cell_index].get_input_region()
            if self.view.line(reg.end()) == self.view.line(sel):
                if cell_index < len(self.cells) - 1:
                    self.cells[cell_index+1].select()
                return True
        return False

    def move_left(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            reg = self.cells[cell_index].get_input_region()
            if sel == reg.begin():
                return True
        return False

    def move_right(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            reg = self.cells[cell_index].get_input_region()
            if sel == reg.end():
                return True
        return False

    def change_current_cell_type(self, edit, new_type):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        if self.cells[cell_index].cell.cell_type == new_type:
            return

        src = self.cells[cell_index].get_input_content()
        self.notebook.delete_cell(cell_index)
        new_cell = self.notebook.create_new_cell(cell_index, new_type)
        new_cell.source = src
        new_view = self.create_cell_view(cell_index, self.view, new_cell)
        self.cells[cell_index].teardown(edit)
        self.cells[cell_index] = new_view
        new_view.draw(edit)
        new_view.select()

    def create_cell_view(self, index, view, cell):
        if cell.cell_type == "code":
            return CodeCellView(self, index, view, cell)
        else:
            return TextCell(index, view, cell)

    def on_pager(self, text):
        text = re.sub("\x1b[^m]*m", "", text)
        def do_run():
            self.view.run_command('set_pager_text', {'text': text})
        try:
            self.view.run_command('set_pager_text', {'text': text})
        except:
            sublime.set_timeout(do_run, 0)


    def move_to_cell(self, up):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return

        if up and cell_index > 0:
            self.cells[cell_index - 1].select(True)
        elif not up and (cell_index < len(self.cells) - 1):
            self.cells[cell_index + 1].select()


class NotebookViewManager(object):
    def __init__(self):
        self.views = {}

    def create_nb_view(self, view, notebook_id, baseurl):
        id = view.id()
        nbview = NotebookView(view, notebook_id, baseurl)
        self.views[id] = nbview
        return nbview

    def get_nb_view(self, view):
        id = view.id()
        if id not in self.views:
            return None
        nbview = self.views[id]
        nbview.view = view
        return nbview

    def on_close(self, view):
        id = view.id()
        if id in self.views:
        	del self.views[id]

manager = NotebookViewManager()
