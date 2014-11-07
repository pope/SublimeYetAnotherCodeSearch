import sublime

import unittest

import os
import os.path

class CommandTestCase(unittest.TestCase):

  def setUp(self):
    self.project_data = {
        'code_search': {'csearchindex': 'test_csearchindex'},
        'folders': [{'path': '.'}]}
    sublime.active_window().run_command('new_window')
    self.window = sublime.active_window()
    self.window.set_project_data(self.project_data)
    self.view = self.window.new_file()

  def tearDown(self):
    self.view.set_scratch(True)
    self.window.focus_view(self.view)
    self.window.run_command('close_file')
    self.window.run_command('close_window')

    if os.path.isfile('test_csearchindex'):
      os.remove('test_csearchindex')
