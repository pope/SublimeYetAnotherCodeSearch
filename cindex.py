import sublime, sublime_plugin
import os
import os.path
import functools
import subprocess
import threading
import time


class CindexListener(object):
  """A listener interface for handling callbacks while processing cindex."""

  def on_files_processed(self, count):
    """Callback when some files are processed.

    Args:
      count: The number of files that have been processed since last called.
    """
    pass

  def on_finished(self, err=None):
    """Callback for when everything is finished.

    Args:
      err: An optional error object if something unexpected happened.
    """
    pass


class CindexCommand(sublime_plugin.WindowCommand, CindexListener):
  """A window command to run the cindex command."""

  def __init__(self, *args, **kwargs):
    super(CindexCommand, self).__init__(*args, **kwargs)
    self._is_running = False

  def run(self):
    if self._is_running:
      return
    self._is_running = True
    self.window.active_view().set_status('YetAnotherCodeSearch',
                                         'cindex (starting)')
    self._total_indexed = 0

    settings = sublime.load_settings('YetAnotherCodeSearch.sublime-settings')
    path_cindex = settings.get("path_cindex")

    project_data = self.window.project_data()
    index_filename = None
    if ('code_search' in project_data and
        'csearchindex' in project_data['code_search']):
      raw_index_filename = project_data['code_search']['csearchindex']
      index_filename = os.path.expanduser(raw_index_filename)

    _CindexListThread(self,
                      path_cindex=path_cindex,
                      index_filename=index_filename).start()

  def _increment_total_indexed(self, count):
    if not self._is_running:
      return
    self._total_indexed += count
    self.window.active_view().set_status(
        'YetAnotherCodeSearch', 'cindex ({} files)'.format(self._total_indexed))

  def _finish(self, err=None):
    self._is_running = False
    for view in self.window.views():
      view.erase_status('YetAnotherCodeSearch')
    if err:
      sublime.error_message(str(err))

  def on_files_processed(self, count):
    sublime.set_timeout(functools.partial(self._increment_total_indexed, count),
                        0)

  def on_finished(self, err=None):
    sublime.set_timeout(functools.partial(self._finish, err=err),
                        0)


class _CindexListThread(threading.Thread):
  """Runs the cindex command in a thread."""

  def __init__(self, listener, path_cindex='cindex', index_filename=None):
    super(_CindexListThread, self).__init__()
    self._listener = listener
    self._path_cindex = path_cindex
    self._index_filename = os.path.abspath(index_filename)

  def run(self):
    try:
      self._check_index_file()
      self._start_indexing()
      self._listener.on_finished()
    except Exception as e:
      self._listener.on_finished(err=e)

  def _check_index_file(self):
    if not self._index_filename:
      return
    if not os.path.isfile(self._index_filename):
      raise Exception(
          'The index file, {}, does not exist'.format(self._index_filename))

  def _get_proc(self, cmd):
    env = os.environ.copy()
    if self._index_filename:
      env['CSEARCHINDEX'] = self._index_filename
    try:
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
      startupinfo = None
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            env=env, startupinfo=startupinfo)

  def _start_indexing(self):
    cmd = [self._path_cindex, '-verbose']
    proc = self._get_proc(cmd)
    start = time.time()
    count = 0
    for line in iter(proc.stdout.readline, b''):
      # TODO(pope): Only count the lines that are ACTUALLY for files. This is a
      # little too loose, but good for now.
      count += 1
      # Call the listener every so often with an update on what was processed.
      tick = time.time()
      if tick - start > .1:
        self._listener.on_files_processed(count)
        count = 0
        start = tick
    self._listener.on_files_processed(count)
    proc.stdout.close()
    retcode = proc.poll()
    if retcode:
      error = subprocess.CalledProcessError(retcode, cmd)
      raise error
