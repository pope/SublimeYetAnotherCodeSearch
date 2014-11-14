import sublime, sublime_plugin

import bisect
import functools
import operator
import os
import subprocess
import threading

from YetAnotherCodeSearch import parser
from YetAnotherCodeSearch import settings


class _CsearchListener(object):
  """A listener interface for handling callbacks while processing csearch."""

  def on_finished(self, output, err=None):
    """Callback for when everything is finished.

    Args:
      output: The raw output of the csearch command.
      err: An optional error object if something unexpected happened.
    """
    pass


class CsearchCommand(sublime_plugin.WindowCommand, _CsearchListener):
  """A window command to run the search command."""

  def __init__(self, *args, **kwargs):
    super(CsearchCommand, self).__init__(*args, **kwargs)
    self._is_running = False
    self._last_search = ''

  def run(self, quick=False):
    """Runs the search command.

    Args:
      quick: Whether or not to show the found files in the "quick" command
          window. If False, then results are placed in dedicated buffer.
    """
    if self._is_running:
      return
    self._is_running = True
    self.window.show_input_panel('csearch',
                                 self._last_search,
                                 self._on_search,
                                 None,
                                 functools.partial(self._finish, None))

  def _get_results_view(self):
    view = next((view for view in self.window.views()
                if view.name() == 'Code Search Results'), None)
    if not view:
      view = self.window.new_file()
      view.set_name('Code Search Results')
      view.set_scratch(True)
      settings = view.settings()
      settings.set('line_numbers', False)
      settings.set('gutter', False)
      settings.set('spell_check', False)
      view.set_syntax_file(('Packages/YetAnotherCodeSearch/'
                            'Code Search Results.hidden-tmLanguage'))
    return view

  def _on_search(self, result):
    self._last_search = result

    self._write_message('Searching for "{0}"\n\n'.format(result), erase=True)
    try:
      s = settings.get_project_settings(self.window.project_data())
      _CsearchThread(parser.parse_query(result), self,
                     path_csearch=s.csearch_path,
                     index_filename=s.index_filename).start()
    except Exception as e:
      self._finish(None, err=e)

  def _finish(self, output, err=None):
    self._is_running = False
    if err:
      self._print_error(err, output)
      return

    if not output:
      self._write_message('No matches found')
      return

    try:
      query = parser.parse_query(self._last_search)
      matches = parser.parse_search_output(output)
      result = '\n\n'.join((str(f) for f in matches))
      num_files = len(matches)
      num_matches = functools.reduce(operator.add,
                                     (len(r.matches) for r in matches))
      result += '\n\n{0} matches across {1} files'.format(num_matches,
                                                          num_files)
      view = self._get_results_view()
      self._write_message(result, view=view)

      flags = 0
      if not query.case:
        flags = sublime.IGNORECASE
      reg = view.find_all(query.query_re(), flags)
      reg = reg[1:]  # Skip the first match, it's the "title"
      view.add_regions('YetAnotherCodeSearch', reg, 'text.csearch', '',
                       sublime.HIDE_ON_MINIMAP | sublime.DRAW_NO_FILL)
      self.window.focus_view(view)
    except Exception as err:
      self._print_error(err, output)

  def _print_error(self, err, output):
    if isinstance(err, subprocess.CalledProcessError):
      output = err.output
    view = self._get_results_view()
    msg = '{0}\n\n{1}\n'.format(str(err), output)
    self._write_message(msg, view=view)
    self.window.focus_view(view)

  def _write_message(self, msg, view=None, erase=False):
    if view is None:
      view = self._get_results_view()
    view.set_read_only(False)
    if erase:
      view.run_command('select_all')
      view.run_command('right_delete')
    view.run_command('append', {'characters': msg})
    view.set_read_only(True)

  def on_finished(self, output, err=None):
    sublime.set_timeout(functools.partial(self._finish, output, err=err))


class _CsearchThread(threading.Thread):
  """Runs the csearch command in a thread."""

  def __init__(self, search, listener, path_csearch='csearch',
               index_filename=None):
    super(_CsearchThread, self).__init__()
    self._search = search
    self._listener = listener
    self._path_csearch = path_csearch
    self._index_filename = index_filename

  def run(self):
    try:
      output = self._do_search()
      self._listener.on_finished(output)
    except Exception as e:
      self._listener.on_finished(None, err=e)

  def _do_search(self):
    env = os.environ.copy()
    if self._index_filename:
      env['CSEARCHINDEX'] = self._index_filename
    try:
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
      startupinfo = None
    cmd = [self._path_csearch, '-n']
    cmd.extend(self._search.args())
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env, startupinfo=startupinfo)
    output, stderr = proc.communicate()
    retcode = proc.poll()
    if retcode and stderr:
      error = subprocess.CalledProcessError(retcode, cmd)
      error.output = stderr
      raise error
    return output.decode('utf-8')


class CodeSearchResultsGoToFileCommand(sublime_plugin.WindowCommand):
  """Window command to open the file from the search results."""

  def run(self):
    view = self.window.active_view()
    if 'Code Search Results' not in view.settings().get('syntax'):
      return

    line = view.line(view.sel()[0])

    line_nums = view.find_by_selector(
        'constant.numeric.line-number.match.csearch')
    i = bisect.bisect(line_nums, line)
    if not line.contains(line_nums[i]):
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
    if line.contains(matches[i]):
      col = matches[i].a - line.a - 6  # 6 is the amount of padding

    self.window.open_file('{0}:{1}:{2}'.format(filename, linenum, col),
                          sublime.ENCODED_POSITION)
    # TODO(pope): Consider highlighting the match

