import collections
import string
import textwrap

_EOF = '\0'


def _text_state(lex):
  """Lex state for handling text.

  Args:
    lex: The _Lexer object.
  Returns:
    The next lex state.
  """
  lex.acceptRun(string.whitespace)
  lex.ignore()

  n = lex.next()
  if n == _EOF:
    return None
  if n == '"':
    return _quote_state

  while True:
    lex.acceptRunIgnoring(string.whitespace + '\\:')
    if lex.peek() == ':':
      if lex.curstr().lower() in ('file', 'case'):
        lex.emit('flag')
        lex.next()  # advance the ':'.
        lex.ignore()  # drop it.
        return _text_state
      else:
        lex.next()
    elif lex.accept('\\') and lex.accept(' '):
      pass
    else:
      break
  lex.emit('text')

  return _text_state


def _quote_state(lex):
  """Lex state for handling double quoted text.

  Args:
    lex: The _Lexer object.
  Returns:
    The next lex state.
  """
  # TODO(pope): Handle the error case when we try to leave without seeing a
  # closing quote.
  while True:
    lex.acceptRunIgnoring('\\"')
    c = lex.next()
    if c == '\\':
      lex.next()  # Advance over whatever is being escaped.
    else:
      break
  lex.emit('quote')
  return _text_state


class _Lexer(object):
  """The simple lexer for parsing search queries."""

  def __init__(self, str):
    self.str_ = str
    self.start_state_ = _text_state

  def run(self):
    """Runs the lexer returning a list of tokens.

    Returns:
      A list of token tuples, where the first entry is the token type and the
      second value is the text value.
    """
    self.start_= 0
    self.pos_ = 0
    self.width_ = 0
    self.tokens_ = []
    state = self.start_state_
    while state is not None:
      state = state(self)
    return self.tokens_

  def curstr(self):
    """The string as it's been parsed before being emitted."""
    return self.str_[self.start_:self.pos_]

  def emit(self, tokType):
    """Emit appends the current string to the list of tokens.

    Args:
      tokType: The token type describing the current string.
    """
    self.tokens_.append((tokType, self.curstr()))
    self.start_= self.pos_

  def ignore(self):
    """Ignores the current string."""
    self.start_= self.pos_

  def next(self):
    """Moves the cursor to the next character in the string.

    Returns:
      The character that was just consumed or _EOF if there's nothing left.
    """
    if self.pos_ >= len(self.str_):
      self.width_ = 0
      return _EOF
    c = self.str_[self.pos_]
    self.width_ = 1
    self.pos_ += self.width_
    return c

  def backup(self):
    """Undo one next() call."""
    self.pos_ -= self.width_

  def peek(self):
    """Returns the next character in the string."""
    c = self.next()
    self.backup()
    return c

  def accept(self, str):
    """Advances the cursor to the next character if contained within the string.

    Args:
      str: A string of expected characters to see next.
    Returns:
      True if the next character was accepted, or False if it was not.
    """
    if self.next() in str:
      return True
    self.backup()
    return False

  def acceptRun(self, str):
    """Advances the cursor forward while the next character is in the string.

    Args:
      str: A string of expected characters to see next.
    """
    while self.next() in str:
      pass
    self.backup()

  def acceptRunIgnoring(self, str):
    """Advances the cursor forward while next is not within the string.

    Args:
      str: A string of characters to ignore while calling next.
    """
    while True:
      c = self.next()
      if c == _EOF or c in str:
        break
    self.backup()


class Search(object):
  """A search object.

  Used to organize phrases to search and for while files.

  Attributes:
    query: A list of search terms to hunt down.
    file: A string pattern for files to limit the search to.
    case: A boolean value for if the search is case sensitive or not.
  """

  def __init__(self, query=None, file=None, case=True):
    if query:
      self.query = query
    else:
      self.query = []
    self.file = file
    self.case = case

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            self.query == other.query and
            self.file == other.file and
            self.case == other.case)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    # Not really needed, so a very dumb implementation to just be correct.
    return 42

  def __repr__(self):
    return '{0}(query={1}; file={2}; case={3})'.format(self.__class__,
                                                       self.query,
                                                       self.file,
                                                       self.case)


def parse(str):
  """Parse a search string into a Search object.

  Search example queries include:

    "A literal string"
    ^.*someRegex.*$
    MyClass file:.*c$
    myclass case:no

  Args:
    str: The search string to parse.
  Returns:
    A Search object representing the parsed string.
  """
  res = Search()
  lex = _Lexer(str)
  tokens = iter(lex.run())
  try:
    while True:
      (tokType, tokValue) = next(tokens)
      if tokType in ('text', 'quote'):
        res.query.append(tokValue)
      elif tokType == 'flag':
        flag = tokValue.lower()
        (ignore_type, value) = next(tokens)
        if flag == 'case':
          if value.lower() == 'no':
            res.case = False
          else:
            res.case = True
        elif flag == 'file':
          res.file = value
        else:
          raise Exception('Unsupported flag value: {0}'.format(flag))
      else:
        raise Exception('Unsupported token type: {0}'.format(tokType))
  except StopIteration:
    pass
  return res


if __name__ == '__main__':
  def test(desc, str, expected):
    actual = parse(str)
    assert actual == expected, \
           '{0}: Expected {1}. Got {2}'.format(desc, expected, actual)

  test('Simple',
       r'someVariableName',
       Search(query=['someVariableName']))
  test('Unicode',
       r'Hello, 世界. Done',
       Search(query=['Hello,', '世界.', 'Done']))
  test('Regex',
       r'some.*variable.*name',
       Search(query=[r'some.*variable.*name']))
  test('Quoted String',
       r'"Hello, \"World\"" printf',
       Search(query=[r'"Hello, \"World\""', 'printf']))
  test('With File',
       r'"Hello, World" file:.*py$',
       Search(query=[r'"Hello, World"'], file='.*py$'))
  test('Case Insensitive',
       r'someVariableName case:no',
       Search(query=['someVariableName'], case=False))
  test('Regex with space',
       r'name\ *=\ *foo',
       Search(query=[r'name\ *=\ *foo']))
  test('Keyword looking value',
       r'foo:bar',
       Search(query=['foo:bar']))
