import sublime

import os
import os.path
import unittest


class CommandTestCase(unittest.TestCase):

  def setUp(self):
    path = '{0}/YetAnotherCodeSearch'.format(sublime.packages_path())
    self.index = '{0}/test_csearchindex'.format(path)
    self.project_data = {
        'code_search': {'csearchindex': self.index},
        'folders': [{'path': path}]}
    sublime.active_window().run_command('new_window')
    self.window = sublime.active_window()
    self.window.set_project_data(self.project_data)
    self.view = self.window.new_file()

  def tearDown(self):
    self.view.set_scratch(True)
    self.window.focus_view(self.view)
    self.window.run_command('close_file')
    self.window.run_command('close_window')

    if os.path.isfile(self.index):
      os.remove(self.index)
