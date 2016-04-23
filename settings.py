import sublime

import os.path


def fix_path(path, project_dir=None):
    """Resolves absolute path:
        absolute path is reported as is
        resolve paths with user home (~)
        other relative paths resolved against project dir"""
    path = os.path.expanduser(path)
    if not os.path.isabs(path) and project_dir:
        path = os.path.join(project_dir, path)
    return os.path.abspath(path)


class Settings(object):
    """Code search settings for the project.

    Attributes:
        csearch_path: The path to the csearch command.
        cindex_path: The path to the cindex command.
        index_filename: An optional path to a csearchindex file.
        paths_to_index: An optional list of paths to index.
    """

    def __init__(self, csearch_path, cindex_path, index_filename=None,
                 paths_to_index=None):
        self.csearch_path = csearch_path
        self.cindex_path = cindex_path
        self.index_filename = index_filename
        self.paths_to_index = paths_to_index or []

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.csearch_path == other.csearch_path and
                self.cindex_path == other.cindex_path and
                self.index_filename == other.index_filename and
                self.paths_to_index == other.paths_to_index)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        # Not really needed, so a very dumb implementation to just be correct.
        return 42

    def __repr__(self):
        s = ('{0}(csearch_path={1}; cindex_path={2}; index_filename={3};'
             ' paths_to_index={4})')
        return s.format(self.__class__, self.csearch_path, self.cindex_path,
                        self.index_filename, self.paths_to_index)


def get_project_settings(project_data,
                         project_file_name=None,
                         index_project_folders=False):
    """Gets the Code Search settings for the current project.

    Args:
        project_data: The project data associated for a window as a dict.
        project_file_name: path to project settings file.
        index_project_folders: A boolean which specifies if we should use the
            project's folders as our starting points for indexing files.
    Returns:
        A Settings object describing the code search settings.
    Raises:
        Exception: If an index file was set, but it doesn't exist or if the
            index file is missing.
    """
    settings = sublime.load_settings('YetAnotherCodeSearch.sublime-settings')
    path_cindex = settings.get('path_cindex')
    path_csearch = settings.get('path_csearch')
    index_filename = None
    paths_to_index = []
    project_dir = None
    if project_file_name:
        project_dir = os.path.dirname(project_file_name)
    if ('code_search' in project_data):
        if 'csearchindex' in project_data['code_search']:
            index_filename = fix_path(
                project_data['code_search']['csearchindex'], project_dir)

    if index_project_folders:
        paths_to_index = [fix_path(folder['path'], project_dir)
                          for folder in project_data['folders']]

    return Settings(path_csearch, path_cindex,
                    index_filename=index_filename,
                    paths_to_index=paths_to_index)
