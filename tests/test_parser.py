import unittest

from YetAnotherCodeSearch import parser


class ParseQueryTest(unittest.TestCase):

  def assertParse(self, search, query=None, file=None, case=True):
    expected = parser.Search(query=query, file=file, case=case)
    actual = parser.parse_query(search)
    self.assertEquals(expected, actual)

  def test_parse_with_simple_query(self):
    self.assertParse('someVariableName', query=['someVariableName'])

  def test_parse_with_unicode_query(self):
    self.assertParse('Hello, 世界. Done', query=['Hello,', '世界.', 'Done'])

  def test_regex(self):
    self.assertParse(r'some.*variable.*name', query=[r'some.*variable.*name'])

  def test_quoted_string(self):
    self.assertParse(r'"Hello, \"World\"" printf',
                     query=[r'"Hello, \"World\""', 'printf'])

  # TODO(pope): Make this give a warning. At least this proves we don't loop
  # infinitely for this value.
  def test_quoted_string_without_closing_quote(self):
    self.assertParse(r'"Hello', query=['"Hello'])

  def test_with_file(self):
    self.assertParse(r'"Hello, World" file:.*py$',
                     query=[r'"Hello, World"'], file='.*py$')

  def test_case_insensitive(self):
    self.assertParse(r'someVariableName case:no',
                     query=['someVariableName'], case=False)

  def test_regex_with_space(self):
    self.assertParse(r'name\ *=\ *foo', query=[r'name\ *=\ *foo'])

  def test_keyword_looking_value(self):
    self.assertParse(r'foo:bar', query=['foo:bar'])


class SearchTest(unittest.TestCase):

  def test_args_simple(self):
    self.assertEquals(parser.Search(query=['hello']).args(), ['hello'])

  def test_args_with_file(self):
    self.assertEquals(parser.Search(query=['hello'], file='.*py$').args(),
                      ['-f', '.*py$', 'hello'])

  def test_args_with_case_insensitive(self):
    self.assertEquals(parser.Search(query=['hello'], case=False).args(),
                      ['-i', 'hello'])

  def test_args_with_multiple_queries(self):
    self.assertEquals(parser.Search(query=['hello', 'world']).args(),
                      ['(hello|world)'])

