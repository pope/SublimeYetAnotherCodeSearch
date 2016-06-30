from itertools import zip_longest
import math
import string

_EOF = '\0'


def _search_text_state(lex):
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
        return _search_quote_state

    while True:
        lex.acceptRunIgnoring(string.whitespace + '\\:')
        if lex.peek() == ':':
            # TODO(pope): Remove this out of here and make this the job of the
            # parser.
            if lex.curstr().lower() in ('file', 'case'):
                lex.emit('flag')
                lex.next()  # advance the ':'.
                lex.ignore()  # drop it.
                return _search_text_state
            else:
                lex.next()
        elif lex.accept('\\'):
            lex.next()  # advance what we're escaping.
        else:
            break
    lex.emit('text')

    return _search_text_state


def _search_quote_state(lex):
    """Lex state for handling double quoted text.

    Args:
        lex: The _Lexer object.
    Returns:
        The next lex state.
    """
    while True:
        lex.acceptRunIgnoring('\\"')
        c = lex.next()
        if c == '\\':
            lex.next()  # Advance over whatever is being escaped.
        elif c == '"':
            lex.emit('quote')
            break
        else:  # end
            lex.emitValue('quote', lex.curstr() + '"')
            break
    return _search_text_state


class _OutputToken(object):
    FileName, LineNumber, Line = range(0, 3)


def _output_start_state(lex):
    """Lex start state for tokenizing search output.

    Args:
        lex: The _Lexer object.
    Returns:
        The next lex state function.
    """
    if lex.peek() == _EOF:
        return None
    return _output_filename_state


def _output_filename_state(lex):
    """Lex state for tokenizing the filename.

    Args:
        lex: The _Lexer object.
    Returns:
        The next lex state function.
    """
    lex.acceptRunIgnoring(':')
    if not lex.hasstr():
        lex.error('Expected to read a filename.')
    lex.emit(_OutputToken.FileName)
    if lex.next() != ':':
        lex.error('Expected to see a ":" after reading the filename.')
    lex.ignore()
    return _output_linenumber_state(lex)


def _output_linenumber_state(lex):
    """Lex state for tokenizing the line number.

    Args:
        lex: The _Lexer object.
    Returns:
        The next lex state function.
    """
    lex.acceptRun(string.digits)
    if not lex.hasstr():
        lex.error('Expected line number as digits.')
    lex.emit(_OutputToken.LineNumber)
    if lex.next() != ':':
        lex.error('Expected to see a ":" after reading the line number.')
    lex.ignore()
    return _output_line_state


def _output_line_state(lex):
    """Lex state for tokenizing the found line.

    Args:
        lex: The _Lexer object.
    Returns:
        The next lex state function.
    """
    lex.acceptRunIgnoring('\n')
    if not lex.hasstr():
        lex.error('Expected the found line.')
    lex.emit(_OutputToken.Line)
    c = lex.next()
    if not (c == '\n' or c == _EOF):
        lex.error('Expected a newline after reading the found line.')
    lex.ignore()
    return _output_start_state


class _LexerException(Exception):
    """Exception class when there is a lexing error."""
    pass


class _Lexer(object):
    """The simple lexer for tokenizing strings."""

    def __init__(self, text, start_state):
        self._text = text
        self._start_state = start_state

    def run(self):
        """Runs the lexer returning a list of tokens.

        Returns:
            A list of token tuples, where the first entry is the token type and
            the second value is the text value.
        """
        self._start = 0
        self._pos = 0
        self._width = 0
        self._tokens = []
        state = self._start_state
        while state is not None:
            state = state(self)
        return self._tokens

    def error(self, msg):
        """Emits an error token with the message.

        Args:
            msg: The error message to emit.
        Raises:
            _LexerException
        """
        # TODO(pope): Keep track of the line number and emit that too.
        raise _LexerException(msg)

    def curstr(self):
        """The string as it's been parsed before being emitted."""
        return self._text[self._start:self._pos]

    def hasstr(self):
        """Checks to see if a string has been parsed before being emitted."""
        return self._pos > self._start

    def emit(self, tokType):
        """Emit appends the current string to the list of tokens and advances
        position.

        Args:
            tokType: The token type describing the current string.
        """
        self.emitValue(tokType, self.curstr())

    def emitValue(self, tokType, value):
        """Emit appends value to the list of tokens and advances position.

        Args:
            tokType: The token type describing the current string.
            value: value of token.
        """
        self._tokens.append((tokType, value))
        self._start = self._pos

    def ignore(self):
        """Ignores the current string."""
        self._start = self._pos

    def next(self):
        """Moves the cursor to the next character in the string.

        Returns:
            The character that was just consumed or _EOF if there's nothing
            left.
        """
        if self._pos >= len(self._text):
            self._width = 0
            return _EOF
        c = self._text[self._pos]
        self._width = 1
        self._pos += self._width
        return c

    def backup(self):
        """Undo one next() call."""
        self._pos -= self._width

    def peek(self):
        """Returns the next character in the string."""
        c = self.next()
        self.backup()
        return c

    def accept(self, text):
        """Advances the cursor to the next character if within the string.

        Args:
            text: A string of expected characters to see next.
        Returns:
            True if the next character was accepted, or False if it was not.
        """
        if self.next() in text:
            return True
        self.backup()
        return False

    def acceptRun(self, text):
        """Advances the cursor forward while the next character is within the
        string.

        Args:
            text: A string of expected characters to see next.
        """
        while self.next() in text:
            pass
        self.backup()

    def acceptRunIgnoring(self, text):
        """Advances the cursor forward while next is not within the string.

        Args:
            text: A string of characters to ignore while calling next.
        """
        while True:
            c = self.next()
            if c == _EOF or c in text:
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

    def args(self):
        """Prints out the command arguments for csearch.

        Returns:
            A list of command line arguments from the query.
        Raises:
            AttributeError: If there is no query for the command.
        """
        if not self.query:
            raise AttributeError('No query to run')
        args = []
        if self.file:
            args.extend(['-f', self.file])
        if not self.case:
            args.append('-i')
        args.append(self.query_re())
        return args

    def query_re(self):
        if len(self.query) == 1:
            return self.query[0]
        else:
            return '({0})'.format('|'.join(self.query))

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


def parse_query(text):
    """Parse a search string into a Search object.

    Search example queries include:

        "A literal string"
        ^.*someRegex.*$
        MyClass file:.*c$
        myclass case:no

    Args:
        text: The search query string to parse.
    Returns:
        A Search object representing the parsed string.
    Raises:
        Exception: If there was a problem parsing the search query.
    """
    res = Search()
    lex = _Lexer(text, _search_text_state)
    tokens = iter(lex.run())
    try:
        while True:
            (tokType, tokValue) = next(tokens)
            if tokType == 'text':
                res.query.append(tokValue)
            elif tokType == 'quote':
                res.query.append(tokValue[1:-1])
            elif tokType == 'flag':
                flag = tokValue.lower()
                (ignore_type, value) = next(tokens)
                if flag == 'case':
                    if value.lower() == 'no':
                        res.case = False
                    else:
                        res.case = True
                elif flag == 'file':
                    if value != '*':
                        res.file = value
                else:
                    raise Exception('Unsupported flag value: {0}'.format(flag))
            else:
                raise Exception('Unsupported token type: {0}'.format(tokType))
    except StopIteration:
        pass
    return res


class FileResults(object):
    """The parsed search output for a file.

    Used to organize all of the matched lines for a particular file.

    Attributes:
        filename: The location of the file.
        matches: A list of tuple pairs where the first item is the line number,
            and the second value is the matched line.
    """

    def __init__(self, filename, matches):
        assert matches
        assert filename
        self.filename = filename
        self.matches = matches

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.filename == other.filename and
                self.matches == other.matches)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        # Not really needed, so a very dumb implementation to just be correct.
        return 42

    def __repr__(self):
        msg = '{0}(filename={1}; matches={2})'
        return msg.format(self.__class__, self.filename, self.matches)

    def __str__(self):
        line_tmpl = '{0: >5}: {1}'
        res_matches = []
        matches = iter(self.matches)
        (linenum, line) = next(matches)
        res_matches.append(line_tmpl.format(linenum, line))
        prev_linenum = linenum
        for (linenum, line) in matches:
            if prev_linenum + 1 != linenum:
                num_digits = int(math.log10(prev_linenum)) + 1
                res_matches.append('{0: >5}'.format('.' * num_digits))
            res_matches.append(line_tmpl.format(linenum, line))
            prev_linenum = linenum
        return '{0}:\n{1}'.format(self.filename, '\n'.join(res_matches))


def parse_search_output(text):
    """Parse the output text from a search command.

    The format of the text should be:

        #File_Name:Line_Number:Line_Contents
        a.txt:1:Too many cooks
        a.txt:2:TOO MANY cooks
        b.txt:34:How to cook

    Args:
        text: The search output string.
    Returns:
        A list of FileResults objects.
    Raises:
        Exception: If there was a problem parsing the output.
    """
    res = []
    lex = _Lexer(text, _output_start_state)
    tokens = lex.run()
    if not tokens:
        return res
    # See grouper recipe in itertools docs. Going to group this list into 3s --
    # filename, line number, line.
    tokens = iter(tokens)
    token_groups = zip_longest(tokens, tokens, tokens)

    (filename, linenum, line) = _line_parts(next(token_groups))
    cur_filename = filename
    cur_matches = [(linenum, line)]
    for (filename, linenum, line) in map(_line_parts, token_groups):
        if cur_filename != filename:
            res.append(FileResults(cur_filename, cur_matches))
            cur_filename = filename
            cur_matches = [(linenum, line)]
        else:
            cur_matches.append((linenum, line))
    res.append(FileResults(cur_filename, cur_matches))
    return res


def _line_parts(token_group):
    """Pulls out the data from the token group.

    Args:
        token_group:  The token group of filename, linenum, and line.
    Returns:
        A tuple for the filename, the line number, and the matched line.
    Raises:
        ValueError: If the line number could not be parsed as an int. This
            should not happen.
    """
    (file_token, linenum_token, line_token) = token_group
    # TODO(pope): Add assertions that the tokens are what we expect.
    (unused_tok, filename) = file_token
    (unused_tok, linenum) = linenum_token
    (unused_tok, line) = line_token
    return (filename, int(linenum), line)
