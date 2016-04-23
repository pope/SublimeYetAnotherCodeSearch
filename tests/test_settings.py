import os.path
import unittest
from unittest.mock import patch

from YetAnotherCodeSearch import settings


def abspath(x):
    return x if x.startswith('/') else '/abs/' + x


def expanduser(x):
    return x.replace('~', '/abs/home/you')


class GetProjectSettingsTest(unittest.TestCase):

    def setUp(self):
        self.project_data = {
            'code_search': {
                'csearchindex': '/abs/csearchindex'},
            'folders': [
                {'path': '~/bar'},
                {'path': '~/foo'},
                {'path': 'src'}]}
        self.project_file_name = '/abs/project/test.project'

    @patch('os.path.isabs', autospec=True)
    @patch('os.path.abspath', autospec=True)
    @patch('os.path.expanduser', autospec=True)
    @patch('os.path.isfile', autospec=True)
    def test_get_project_settings(self, mock_isfile, mock_expanduser,
                                  mock_abspath, mock_isabs):
        mock_expanduser.side_effect = expanduser
        mock_abspath.side_effect = abspath
        mock_isfile.return_value = True
        mock_isabs.side_effect = lambda x: x.startswith('/')

        s = settings.get_project_settings(self.project_data,
                                          self.project_file_name,
                                          index_project_folders=True)
        self.assertEquals(s.paths_to_index, ['/abs/home/you/bar',
                                             '/abs/home/you/foo',
                                             '/abs/project/src'])
        self.assertEquals(s.index_filename, '/abs/csearchindex')
        # Test the basename here incase someone is testing and has their own
        # user settings.
        self.assertEquals(os.path.basename(s.cindex_path), 'cindex')
        self.assertEquals(os.path.basename(s.csearch_path), 'csearch')

    @patch('os.path.isabs', autospec=True)
    @patch('os.path.abspath', autospec=True)
    @patch('os.path.expanduser', autospec=True)
    @patch('os.path.isfile', autospec=True)
    def test_get_project_settings_when_indexing_project_and_no_index_set(
            self, mock_isfile, mock_expanduser, mock_abspath, mock_isabs):
        mock_expanduser.side_effect = expanduser
        mock_abspath.side_effect = abspath
        mock_isfile.return_value = True
        mock_isabs.side_effect = lambda x: x.startswith('/')

        del self.project_data['code_search']
        s = settings.get_project_settings(self.project_data,
                                          self.project_file_name,
                                          index_project_folders=True)
        self.assertEquals(s.paths_to_index, ['/abs/home/you/bar',
                                             '/abs/home/you/foo',
                                             '/abs/project/src'])
        self.assertIsNone(s.index_filename)
        self.assertEquals(os.path.basename(s.cindex_path), 'cindex')
        self.assertEquals(os.path.basename(s.csearch_path), 'csearch')
