import sublime

import os.path
import shutil
import textwrap
import time
import uuid

from YetAnotherCodeSearch.tests import CommandTestCase


_NEEDLE_IN_HAYSTACK = 'cc5b252b-e7fb-5145-bf8a-ed272e3aa7bf'


class CsearchCommandTest(CommandTestCase):

  def setUp(self):
    super(CsearchCommandTest, self).setUp()
    if os.path.isfile(self.index):
      return

    self.window.run_command('cindex', {'index_project': True})
    self._wait_for_status(self.view)
    assert os.path.isfile(self.index)

  def test_csearch_exists(self):
    self.assertIsNotNone(shutil.which('csearch'))

  def test_csearch(self):
    results_view = self._search(_NEEDLE_IN_HAYSTACK)
    expected = textwrap.dedent("""\
        Searching for "{0}"

        {1}/test_csearch.py:
           12: _NEEDLE_IN_HAYSTACK = '{0}'

        1 matches across 1 files
    """).format(_NEEDLE_IN_HAYSTACK, self.project_path)
    actual = results_view.substr(sublime.Region(0, results_view.size()))
    self.assertEquals(expected, actual)

  def test_csearch_no_matches(self):
    query = str(uuid.uuid4())
    results_view = self._search(query)
    expected = textwrap.dedent("""\
        Searching for "{0}"

        No matches found
    """).format(query, self.project_path)
    actual = results_view.substr(sublime.Region(0, results_view.size()))
    self.assertEquals(expected, actual)

  def test_csearch_go_to_file(self):
    results_view = self._search(_NEEDLE_IN_HAYSTACK)
    pt = results_view.text_point(3, 10)  # Line 4, 10 characters in
    results_view.sel().clear()
    results_view.sel().add(sublime.Region(pt))
    self.window.run_command('code_search_results_go_to_file')
    self.assertEquals('{0}/test_csearch.py'.format(self.project_path),
                      self.window.active_view().file_name())

  def _wait_for_status(self, view):
    max_iters = 10
    while max_iters > 0 and view.get_status('YetAnotherCodeSearch') != '':
      time.sleep(0.1)
      max_iters -= 1
    assert '' == view.get_status('YetAnotherCodeSearch')

  def _search(self, query):
    self.window.run_command('csearch', {'query': query})
    results_view = next((view for view in self.window.views()
                         if view.name() == 'Code Search Results'))
    self._wait_for_status(results_view)
    return results_view
