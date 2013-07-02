# -*- coding: utf-8 -*-
# Copyright (c) 2013, Maxim Grechkin
# This file is licensed under GNU General Public License version 3
# See COPYING for details.

import sublime
import sublime_plugin
try:
    from SublimeIPythonNotebook import ipy_view, ipy_connection
except ImportError:
    import ipy_view, ipy_connection


manager = ipy_view.manager



class SublimeINListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        nbview = manager.get_nb_view(view)
        if nbview:
            nbview.on_sel_modified()

    def on_modified(self, view):
        nbview = manager.get_nb_view(view)
        if nbview:
            nbview.on_modified()

    def on_close(self, view):
    	manager.on_close(view)


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
        if nbs is None:
            print ("Cannot get a list of notebooks")
            return
        self.nbs = nbs
        lst = ["0: Create New Notebook\n"]
        for i, nb in enumerate(nbs):
            lst.append(str(i+1) + ":  " + nb["name"] + "\n")

        self.window.show_quick_panel(lst, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return

        view = self.window.new_file()
        if picked > 0:
            manager.create_nb_view(view, self.nbs[picked-1]["notebook_id"], self.baseurl)
        else:
            new_nb_id = ipy_connection.create_new_notebook(self.baseurl)
            if new_nb_id is None:
                return
            manager.create_nb_view(view, new_nb_id, self.baseurl)

        view.run_command("inb_render_notebook")


class SetPagerTextCommand(sublime_plugin.TextCommand):
    """command to set the text in the pop-up pager"""
    def run(self, edit, text):
        pager_view = self.view.window().get_output_panel("help")
        pager_view.insert(edit, 0, text)
        self.view.window().run_command("show_panel", {"panel": "output.help"})


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
    def run(self, edit, inplace):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.run_cell(edit, inplace)


class InbDeleteCurrentCellCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.delete_current_cell(edit)


class InbInsertCellAboveCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.insert_cell_above(edit)


class InbInsertCellBelowCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.insert_cell_below(edit)


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
            new_view.run_command('inb_insert_string', {'s': s})
            new_view.set_name(nbview.name + ".ipynb")

class InbInsertStringCommand(sublime_plugin.TextCommand):
    def run(self, edit, s):
        self.view.insert(edit, 0, s)


class InbMoveToCell(sublime_plugin.TextCommand):
    def run(self, edit, up):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.move_to_cell(up)


class InbChangeCellTypeCommand(sublime_plugin.TextCommand):
    def run(self, edit, new_type):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            nbview.change_current_cell_type(edit, new_type)

class InbRenameNotebookCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        nbview = manager.get_nb_view(self.view)
        if nbview:
            self.nbview = nbview
            sublime.active_window().show_input_panel("Notebook name", nbview.get_name(),
                                                            self.on_done, None, None)

    def on_done(self, line):
        self.nbview.set_name(line)