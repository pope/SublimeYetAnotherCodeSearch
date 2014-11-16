import os.path
import unittest
from unittest.mock import patch

from YetAnotherCodeSearch import settings


class GetProjectSettingsTest(unittest.TestCase):

    def setUp(self):
        self.project_data = {
            'code_search': {
                'csearchindex': 'csearchindex'},
            'folders': [
                {'path': '~/bar'},
                {'path': '~/foo'}]}

    @patch('os.path.abspath', autospec=True)
    @patch('os.path.expanduser', autospec=True)
    @patch('os.path.isfile', autospec=True)
    def test_get_project_settings(self, mock_isfile, mock_expanduser,
                                  mock_abspath):
        mock_expanduser.side_effect = lambda x: x.replace('~', 'home/you')
        mock_abspath.side_effect = lambda x: '/abs/' + x
        mock_isfile.return_value = True

        s = settings.get_project_settings(self.project_data,
                                          index_project_folders=True)
        self.assertEquals(s.paths_to_index, ['/abs/home/you/bar',
                                             '/abs/home/you/foo'])
        self.assertEquals(s.index_filename, '/abs/csearchindex')
        # Test the basename here incase someone is testing and has their own
        # user settings.
        self.assertEquals(os.path.basename(s.cindex_path), 'cindex')
        self.assertEquals(os.path.basename(s.csearch_path), 'csearch')

    @patch('os.path.isfile', autospec=True)
    def test_raises_exception_if_index_file_is_missing(self, mock_isfile):
        mock_isfile.return_value = False
        with self.assertRaises(Exception):
            settings.get_project_settings(self.project_data)

    @patch('os.path.abspath', autospec=True)
    @patch('os.path.expanduser', autospec=True)
    @patch('os.path.isfile', autospec=True)
    def test_get_project_settings_when_indexing_project_and_no_index_set(
            self, mock_isfile, mock_expanduser, mock_abspath):
        mock_expanduser.side_effect = lambda x: x.replace('~', 'home/you')
        mock_abspath.side_effect = lambda x: '/abs/' + x
        mock_isfile.return_value = True

        del self.project_data['code_search']
        s = settings.get_project_settings(self.project_data,
                                          index_project_folders=True)
        self.assertEquals(s.paths_to_index, ['/abs/home/you/bar',
                                             '/abs/home/you/foo'])
        self.assertIsNone(s.index_filename)
        self.assertEquals(os.path.basename(s.cindex_path), 'cindex')
        self.assertEquals(os.path.basename(s.csearch_path), 'csearch')
