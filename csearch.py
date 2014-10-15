import sublime, sublime_plugin

from YetAnotherCodeSearch import query_parser

class CsearchCommand(sublime_plugin.WindowCommand):
  def run(self, quick=False):
    self.window.show_input_panel('csearch', '', self.on_done, None, None)

  def on_done(self, result):
    print(query_parser.parse(result));
