# -*- coding: utf-8 -*-
# Copyright (c) 2013, Maxim Grechkin
# This file is licensed under GNU General Public License version 3
# See COPYING for details.

import sublime
import sublime_plugin
import ipy_connection
import threading

global_lock = threading.Lock()


def create_kernel(baseurl, notebook_id):
    return ipy_connection.Kernel(notebook_id, baseurl)

output_draw_style = sublime.HIDDEN
input_draw_style = sublime.HIDDEN


class CellView(object):
    def __init__(self, index, view, cell):
        self.index = index
        self.view = view
        self.running = False
        self.cell_lock = threading.Lock()
        self.cell = cell
        self.cell.cell_view = self

    def run(self, regions, kernel):
        if self.running:
            print "Warning"
            print "Cell is already running"
            return
        self.running = True
        code = self.get_code(regions)
        self.cell.code = code

        self.cell.run(kernel)

    def update_output(self):
        def run_command():
            self.view.run_command("inb_insert_output", {"cell_index": self.index})
        sublime.set_timeout(run_command, 0)

    def on_execute_reply(self, msg_id, content):
        self.running = False

    def output_result(self, edit):
        with self.cell_lock:
            self.do_output_result(edit, self.cell.output)

    def do_output_result(self, edit, result):
        if not result or (len(result) == 0):
            result = "\n"

        if not result.endswith("\n"):
            result += "\n"

        with global_lock:
            regs = self.view.get_regions("inb_output")
            n = self.index
            reg = regs[n]

            self.view.set_read_only(False)
            start = reg.a
            end = start + len(result)
            self.view.erase(edit, reg)
            self.view.insert(edit, start, result)
            regs = self.view.get_regions("inb_output")
            regs[n] = sublime.Region(start, end)
            self.view.add_regions("inb_output", regs, "string", "", output_draw_style)

    def redraw(self, edit):
        self.view.set_read_only(False)
        regions = self.view.get_regions("inb_input")
        reg = regions[self.index]
        start = reg.a
        code = self.cell.code
        if len(code) == 0:
            code = "\n"
        elif (len(code) > 0) and not code.endswith("\n"):
            code += "\n"
        end = start + len(code) + 1
        self.view.replace(edit, reg, "\n" + code)
        regs = self.view.get_regions("inb_input")
        regs[self.index] = sublime.Region(start, end)
        self.view.add_regions("inb_input", regs, "string", "", input_draw_style)
        self.output_result(edit)

    def get_code(self, regions):
        region = regions[self.index]
        code = self.view.substr(region)
        return code[1:]  # remove first \n

    def update_code(self, regions):
        self.cell.code = self.get_code(regions)

    def select(self, pos=0):
        regions = self.view.get_regions("inb_input")
        reg = regions[self.index]
        if pos < 0:
            pos = pos + reg.size() - 1
        pos = reg.begin() + 1 + pos
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(pos, pos))
        self.view.show_at_center(pos)


class NotebookView(object):
    def __init__(self, view, notebook_id, notebook_name, baseurl):
        self.view = view
        self.baseurl = baseurl
        self.name = notebook_name
        view.set_name("IPy Notebook - " + notebook_name)
        view.set_scratch(True)
        view.set_syntax_file("Packages/Python/Python.tmLanguage")
        view.settings().set("ipython_notebook", True)
        self.cells = []
        self.notebook_id = notebook_id
        self.name = notebook_name
        self.kernel = create_kernel(baseurl, notebook_id)
        self.kernel.status_callback = self.on_status
        self.on_status({"execution_state": "idle"})
        self.notebook = self.kernel.get_notebook()

    def on_modified(self):
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

    def highlight_cell(self, input_region):
        reg = self.view.line(input_region.begin()-2)
        reg2 = self.view.line(input_region.end()+2)
        self.view.add_regions("inb_highlight", [reg, reg2], "comment", "", sublime.DRAW_EMPTY)

    def on_backspace(self):
        s = self.view.sel()[0]

        regset = self.view.get_regions("inb_input")
        for reg in regset:
            reg = sublime.Region(reg.begin()+2, reg.end())
            if reg.contains(s):
                self.view.run_command("left_delete")
                return
            elif (s.begin() == reg.begin() - 1) and (self.view.substr(s.begin()) == "\n"):
                self.view.run_command("left_delete")
                self.view.run_command("move", {"by": "characters", "forward": True})
                return

    def add_input_field(self, n, start=-1):
        view = self.view
        edit = view.begin_edit()
        try:
            if start < 0:
                start = view.size()

            self.view.set_read_only(False)
            if n == 1:
                start = start + view.insert(edit, start, "<>"*40 + "\n")

            start = start + view.insert(edit, start, "#Input[%d]" % n)
            end = start + view.insert(edit, start, "\n\n")

            reg = sublime.Region(start, end)
            regs = view.get_regions("inb_input")
            regs.append(reg)
            view.add_regions("inb_input", regs, "string", "", input_draw_style)
            self.view.set_read_only(False)

            end = end + view.insert(edit, end, "#/Input\n\n\n#Output[%d]\n" % n)

            start = end
            end = start + view.insert(edit, start, "\n")

            reg = sublime.Region(start, end)
            regs = view.get_regions("inb_output")
            regs.append(reg)
            view.add_regions("inb_output", regs, "string", "", output_draw_style)
            self.view.set_read_only(False)

            end = end + view.insert(edit, end, "#/Output\n")
            end = end + view.insert(edit, end, "\n" + "<>"*40 + "\n\n")

        except Exception as e:
            print(e)
        view.end_edit(edit)

    def find_cell_by_selection(self, sel, regions):
        for i, reg in enumerate(regions):
            if reg.contains(sel):
                return i
        return -1

    def run_cell(self):
        sel = self.view.sel()
        if len(sel) > 1:
            return
        sel = self.view.sel()[0]
        regions = self.view.get_regions("inb_input")
        cell_index = self.find_cell_by_selection(sel, regions)
        if cell_index < 0:
            return
        cell = self.get_cell_by_index(cell_index)
        if not cell:
            raise Exception("Cell not found")
        if cell_index == len(regions) - 1:
            new_cell = self.notebook.create_new_cell()
            new_view = CellView(cell_index + 1, self.view, new_cell)
            self.cells.append(new_view)
            self.add_input_field(cell_index + 2)
        cell.run(regions, self.kernel)

    def get_cell_by_index(self, cell_index):
        res = self.cells[cell_index]
        res.view = self.view
        return res

    def save_notebook(self):
        self.kernel.save_notebook(self.notebook)

    def render_notebook(self, edit):
        self.cells = []
        for i in xrange(self.notebook.cell_count):
            self.add_input_field(i+1)
            cell = self.notebook.get_cell(i)
            cell_view = CellView(i, self.view, cell)
            self.cells.append(cell_view)

        for cell in self.cells:
            cell.redraw(edit)

    def update_notebook_from_buffer(self):
        regions = self.view.get_regions("inb_input")
        for cell in self.cells:
            cell.update_code(regions)

    def on_status(self, content):
        def set_status():
            status = "kernel: " + content["execution_state"]
            self.view.set_status("ExecutionStatus", status)
        sublime.set_timeout(set_status, 0)

    def handle_completions(self, view, prefix, locations):
        sel = view.sel()
        if len(sel) > 1:
            return []
        sel = sel[0]
        line = view.substr(view.line(sel))
        row, col = view.rowcol(sel.begin())
        if line[col-1] != ".":
            return []
        compl = self.kernel.get_completitions(line, col)
        c2 = [s[col:] for s in compl]
        return ([(s + "\t (IPython)", s) for s in c2], sublime.INHIBIT_EXPLICIT_COMPLETIONS | sublime.INHIBIT_WORD_COMPLETIONS)

    def get_current_cell_index(self):
        sel = self.view.sel()
        if len(sel) > 1:
            return -1
        sel = self.view.sel()[0]
        regions = self.view.get_regions("inb_input")
        return self.find_cell_by_selection(sel, regions)

    def delete_current_cell(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return
        self.update_notebook_from_buffer()
        self.notebook.delete_cell(cell_index)
        self.view.run_command("inb_render_notebook")
        new_cell_index = cell_index - 1 if cell_index > 0 else 0
        self.cells[new_cell_index].select()

    def insert_cell_below(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return
        self.update_notebook_from_buffer()
        self.notebook.create_new_cell(cell_index + 1)
        self.view.run_command("inb_render_notebook")
        self.cells[cell_index+1].select()

    def insert_cell_above(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return
        self.update_notebook_from_buffer()
        self.notebook.create_new_cell(cell_index)
        self.view.run_command("inb_render_notebook")
        self.cells[cell_index].select()

    def move_up(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            regions = self.view.get_regions("inb_input")
            reg = regions[cell_index]
            if self.view.line(reg.begin()+1) == self.view.line(sel):
                if cell_index > 0:
                    self.cells[cell_index-1].select(-1)
                return True
        return False

    def move_down(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            regions = self.view.get_regions("inb_input")
            reg = regions[cell_index]
            if self.view.line(reg.end()-1) == self.view.line(sel):
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
            regions = self.view.get_regions("inb_input")
            reg = regions[cell_index]
            if sel == reg.begin() + 1:
                return True
        return False

    def move_right(self):
        cell_index = self.get_current_cell_index()
        if cell_index < 0:
            return False
        else:
            sel = self.view.sel()[0].begin()
            regions = self.view.get_regions("inb_input")
            reg = regions[cell_index]
            if sel == reg.end()-1:
                return True
        return False


class NotebookViewManager(object):
    def __init__(self):
        self.views = {}

    def create_nb_view(self, view, nb, baseurl):
        id = view.id()
        nbview = NotebookView(view, nb["notebook_id"], nb["name"], baseurl)
        self.views[id] = nbview
        return nbview

    def get_nb_view(self, view):
        id = view.id()
        if id not in self.views:
            return None
        nbview = self.views[id]
        nbview.view = view
        return nbview

manager = NotebookViewManager()


class SublimeINListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        nbview = manager.get_nb_view(view)
        if nbview:
            nbview.on_modified()


class InbPromptListNotebooksCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel("Notebook host:port : ", "127.0.0.1:8888",
                                     self.on_done, None, None)

    def on_done(self, line):
        self.window.run_command("inb_list_notebooks", {"baseurl": line})


class InbListNotebooksCommand(sublime_plugin.WindowCommand):
    def run(self, baseurl):
        self.baseurl = baseurl
        nbs = ipy_connection.get_notebooks(baseurl)
        self.nbs = nbs
        lst = []
        for i, nb in enumerate(nbs):
            lst.append(str(i) + ":  " + nb["name"] + "\n")
        self.window.show_quick_panel(lst, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return

        view = self.window.new_file()
        manager.create_nb_view(view, self.nbs[picked], self.baseurl)

        view.run_command("inb_render_notebook")


class InbRestartKernelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview and nbview.kernel:
            nbview.kernel.restart_kernel()


class InbInterruptKernelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview and nbview.kernel:
            nbview.kernel.interrupt_kernel()


class InbSaveNotebookCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.update_notebook_from_buffer()
            nbview.save_notebook()

    def description(self):
        return "Save IPython notebook"


class InbBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.on_backspace()


class InbClearBufferCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))


class InbRenderNotebookCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            self.view.set_read_only(False)
            self.view.erase(edit, sublime.Region(0, self.view.size()))
            nbview.render_notebook(edit)


class InbInsertOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, cell_index):
        nbview = manager.get_nb_view(self.view)
        if not nbview:
            raise Exception("Failed to get NBView")

        cell = nbview.get_cell_by_index(cell_index)
        if not cell:
            raise Exception("Failed to get cell")

        cell.output_result(edit)


class InbRunInNotebookCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.run_cell()


class InbDeleteCurrentCellCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.delete_current_cell()


class InbInsertCellAboveCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.insert_cell_above()


class InbInsertCellBelowCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.insert_cell_below()


class InbComplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        nbview = manager.get_nb_view(view)
        if nbview:
            return nbview.handle_completions(view, prefix, locations)


class InbMoveUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if not nbview or not nbview.move_up():
            self.view.run_command("move", {"by": "lines", "forward": False})


class InbMoveDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if not nbview or not nbview.move_down():
            self.view.run_command("move", {"by": "lines", "forward": True})


class InbMoveLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if not nbview or not nbview.move_left():
            self.view.run_command("move", {"by": "characters", "forward": False})


class InbMoveRightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if not nbview or not nbview.move_right():
            self.view.run_command("move", {"by": "characters", "forward": True})


class InbOpenAsIpynbCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        nbview = manager.get_nb_view(view)
        if nbview:
            s = str(nbview.notebook)
            new_view = self.window.new_file()
            edit = new_view.begin_edit()
            new_view.insert(edit, 0, s)
            new_view.end_edit(edit)
            new_view.set_name(nbview.name + ".ipynb")
