import sublime, sublime_plugin

import functools
import os
import os.path
import subprocess
import threading

from YetAnotherCodeSearch import query_parser


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
    settings = sublime.load_settings('YetAnotherCodeSearch.sublime-settings')
    path_csearch = settings.get("path_csearch")

    project_data = self.window.project_data()
    index_filename = None
    if ('code_search' in project_data and
        'csearchindex' in project_data['code_search']):
      raw_index_filename = project_data['code_search']['csearchindex']
      index_filename = os.path.expanduser(raw_index_filename)

    _CsearchThread(query_parser.parse(result),
                   self,
                   path_csearch=path_csearch,
                   index_filename=index_filename).start()

  def _finish(self, output, err=None):
    self._is_running = False
    if err:
      sublime.error_message(str(err))
      return
    if output is None:
      return
    # TODO(pope): Parse this output
    print(output)

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
    self._index_filename = None
    if index_filename:
        self._index_filename = os.path.abspath(index_filename)

  def run(self):
    try:
      self._check_index_file()
      output = self._do_search()
      self._listener.on_finished(output)
    except Exception as e:
      self._listener.on_finished(None, err=e)

  def _check_index_file(self):
    if self._index_filename and not os.path.isfile(self._index_filename):
      raise Exception(
          'The index file, {}, does not exist'.format(self._index_filename))

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
