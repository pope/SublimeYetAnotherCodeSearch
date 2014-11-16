import sublime
import sublime_plugin

import functools
import os
import re
import subprocess
import threading
import time

from YetAnotherCodeSearch import settings

# Matches a verbose file name line, like:
#     2014/10/11 19:26:32 3556 1018 file.name
_FILE_LINE_RE = re.compile(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \d+ \d+ .+')


class _CindexListener(object):
    """A listener interface for handling callbacks while processing cindex."""

    def on_files_processed(self, count):
        """Callback when some files are processed.

        Args:
            count: The number of files that have been processed since last
                called.
        """
        pass

    def on_finished(self, err=None):
        """Callback for when everything is finished.

        Args:
            err: An optional error object if something unexpected happened.
        """
        pass


class CindexCommand(sublime_plugin.WindowCommand, _CindexListener):
    """A window command to run the cindex command."""

    def __init__(self, *args, **kwargs):
        super(CindexCommand, self).__init__(*args, **kwargs)
        self._is_running = False

    def run(self, index_project=False):
        """Runs the cindex command.

        Once this starts running, it will not listen to other calls until the
        index is finished running.

        Args:
            index_project: If true, the index will be generated from folders
                used by the project. The csearchindex file location must be set
                in the project settings when set to True.
        """
        if self._is_running:
            return
        self._is_running = True
        self.window.active_view().set_status('YetAnotherCodeSearch',
                                             'cindex (starting)')
        self._total_indexed = 0

        try:
            s = settings.get_project_settings(
                self.window.project_data(),
                index_project_folders=index_project)
            _CindexListThread(self,
                              path_cindex=s.cindex_path,
                              index_filename=s.index_filename,
                              paths_to_index=s.paths_to_index).start()
        except Exception as e:
            self._finish(err=e)

    def _increment_total_indexed(self, count):
        if not self._is_running:
            return
        self._total_indexed += count
        self.window.active_view().set_status(
            'YetAnotherCodeSearch', 'cindex ({} files)'.format(
                self._total_indexed))

    def _finish(self, err=None):
        self._is_running = False
        for view in self.window.views():
            view.erase_status('YetAnotherCodeSearch')
        if err:
            sublime.error_message(str(err))

    def on_files_processed(self, count):
        sublime.set_timeout(functools.partial(self._increment_total_indexed,
                                              count),
                            0)

    def on_finished(self, err=None):
        sublime.set_timeout(functools.partial(self._finish, err=err), 0)


class _CindexListThread(threading.Thread):
    """Runs the cindex command in a thread."""

    def __init__(self, listener, path_cindex='cindex', index_filename=None,
                 paths_to_index=None):
        """Initializes the _CindexListThread.

        Args:
            listener: A _CindexListener object to send events to.
            path_cindex: The location of the cindex command.
            index_filename: An optional csearchindex file location to use.
            paths_to_index: An optional list of paths to index. If supplied,
                replaces the paths currently used in the csearchindex file.
        """
        super(_CindexListThread, self).__init__()
        self._listener = listener
        self._path_cindex = path_cindex
        self._index_filename = index_filename
        self._paths_to_index = paths_to_index or []

    def run(self):
        try:
            self._start_indexing()
            self._listener.on_finished()
        except Exception as e:
            self._listener.on_finished(err=e)

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
        if self._paths_to_index:
            cmd.append('-reset')
            cmd.extend(self._paths_to_index)
        proc = self._get_proc(cmd)
        start = time.time()
        count = 0
        for line in iter(proc.stdout.readline, b''):
            if _FILE_LINE_RE.match(line.decode('utf-8')):
                count += 1
            # Call the listener every so often with an update on what was
            # processed.
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
