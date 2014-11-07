import sublime

from YetAnotherCodeSearch.tests import CommandTestCase

import os.path
import time

class CindexCommandTest(CommandTestCase):

  def test_cindex(self):
    self.window.run_command('cindex', {'index_project': True})
    max_iters = 10
    while max_iters > 0 and self.view.get_status('YetAnotherCodeSearch') != '':
      time.sleep(0.1)
      max_iters -= 1
    self.assertEquals('', self.view.get_status('YetAnotherCodeSearch'))
    self.assertTrue(os.path.isfile('test_csearchindex'))
