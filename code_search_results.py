import sublime, sublime_plugin

import bisect


class CodeSearchResultsGoToFileCommand(sublime_plugin.WindowCommand):

  def run(self):
    view = self.window.active_view()
    if 'Code Search Results' not in view.settings().get('syntax'):
      return

    line = view.line(view.sel()[0])

    line_nums = view.find_by_selector(
        'constant.numeric.line-number.match.csearch')
    i = bisect.bisect(line_nums, line)
    if not i or not line.contains(line_nums[i]):
      return
    linenum = view.substr(line_nums[i])

    file_names = view.find_by_selector('entity.name.filename.csearch')
    i = bisect.bisect_left(file_names, line)
    if not i:
      return
    filename = view.substr(file_names[i-1])

    matches = view.get_regions('YetAnotherCodeSearch')
    col = 0
    i = bisect.bisect(matches, line)
    if i and line.contains(matches[i]):
      col = matches[i].a - line.a - 6  # 6 is the amount of padding

    self.window.open_file('{0}:{1}:{2}'.format(filename, linenum, col),
                          sublime.ENCODED_POSITION)
    # TODO(pope): Consider highlighting the match
