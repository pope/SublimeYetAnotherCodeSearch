import sublime, sublime_plugin

import functools
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

  def _on_search(self, result):
    self._last_search = result
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
      sublime.error_message(str(err))
      return
    if output is None:
      return
    try:
      result = '\n\n'.join((str(f) for f in parser.parse_search_output(output)))
      v = self.window.create_output_panel('YetAnotherCodeSearch')
      v.run_command('erase_view')
      v.run_command('append', {'characters': result})
      v.set_syntax_file('Packages/Default/Find Results.hidden-tmLanguage')
      self.window.run_command('show_panel', {'panel': 'output.YetAnotherCodeSearch'})
    except Exception as err:
      sublime.error_message(str(err))

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
                            stderr=subprocess.STDOUT,
                            env=env, startupinfo=startupinfo)
    output, unused_err = proc.communicate()
    retcode = proc.poll()
    if retcode and output:
      error = subprocess.CalledProcessError(retcode, cmd)
      error.output = output
      raise error
    return output.decode('utf-8')
