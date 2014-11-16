import sublime

import os
import os.path
import unittest


def _get_project_path():
    return os.path.dirname(os.path.realpath(__file__))


def _get_index_path():
    return '{0}/test_csearchindex'.format(_get_project_path())


class CommandTestCase(unittest.TestCase):

    def setUp(self):
        self.index = _get_index_path()
        self.project_path = _get_project_path()
        project_data = {
            'code_search': {'csearchindex': self.index},
            'folders': [{'path': self.project_path}]}
        sublime.active_window().run_command('new_window')
        self.window = sublime.active_window()
        self.window.set_project_data(project_data)
        self.view = self.window.new_file()

    def tearDown(self):
        self.view.set_scratch(True)
        for view in self.window.views():
            self.window.focus_view(view)
            self.window.run_command('close_file')
        self.window.run_command('close_window')

    @classmethod
    def tearDownClass(cls):
        index = _get_index_path()
        if os.path.isfile(index):
            os.remove(index)
