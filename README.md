# YetAnotherCodeSearch

[![Analytics](https://ga-beacon.appspot.com/UA-280328-3/pope/SublimeYetAnotherCodeSearch/README)](https://github.com/igrigorik/ga-beacon)

This is a plugin for [Sublime Text][ST] that works with [CodeSearch][CS] to
provide fast searching in a large codebase. This is most useful for large
projects where a normal Find is just too slow.

### Yet Another...?

Yeah. There is [SublimeCodeSearch][]; however, there is no LICENSE file so I
couldn't make any modifications to the project. That said, this project will
probably deviate enough from SublimeCodeSearch that it will be worth separating
anyway. Some things worth highlighting:

- Search results are placed in a buffer, similar to Sublime Text's Find
  functionality.
- Searching and indexing don't require a `csearchindex` setting to be set in the
  project, thus using the user's index file, as is the default for `cindex`.
- Plus new features
  - Can specify case and file restrictions when searching
  - Manage and update the index file for a Sublime project.

## Installation

TODO. (talk about installing csearch AND this plugin)

## Settings

In case anyone is migrating over from SublimeCodeSearch (like myself), you will
be pleased to know that the settings and setting names are the same for this
plugin.

The location of `csearch` and `cindex` can be specified by editing the user-
specific `YetAnotherCodeSearch.sublime-settings` file. See the default file
for configuration options. Both are easily found via
*Preferences > Package Settings > YetAnotherCodeSearch*.

### Project Settings

You can specify an index file to use for the project by editing the project
(*Project > Edit Project*) and adding the following property to the JSON file.

    "code_search": {
      "csearchindex": "path/to/csearchindex"
    }

The location of `codesearchindex` is defined relatively to the project location.

## Usage

As is with CodeSearch, there are two main steps to using this plugin - indexing
and searching.

### Indexing

In order to make searching fast, first we need to index the project. To do that,
open up the command palette (*Tools > Command Palette...*) and look for
*Code Search Index*. This command runs in the background and could take a while
depending on the size of the project and the speed of the disk.

That works with existing index files, but YetAnotherCodeSearch can also set up
an index for your current project. From the command palette, run
*Code Search Index Project*. What this will do is take all of the folders in the
project and index them for you. For this to work though, you must specify a
project `csearchindex` file. See *Project Settings* above.

It should be noted, if you make edits to files then you will want to re-run the
indexing step as to pick up those edits for the next time you run a search.

### Searching

To run a search, open up the command pallet (*Tools > Command Palette...*) and
look for *Code Search*. This will open up an input for you to enter your query.

From there, enter a regex-based search query. Multiple queries are supported.
Each term will be ORed together. For queries with spaces in them, you can either
escape the spaces or wrap the query in quotes.

Here are some examples:

    some_obscure_method
    my_method my_variable
    "Hello, world"

The `csearch` command also supports limiting the results to just files that
match a regex as well as can be told to be case insensitive. Since Sublime
doesn't allow you to set custom UI on the input bar, you can encode these
properties into special keywords in the query -- namely `file:` and `case:`.

    some.*variable.*name case:no
    my_method file:\.py$
    foo.*bar case:NO file:\.[ch]$

Once you enter your query, the *Code Search Results* file view should come into
focus. You can move to any matched line and then press the `enter` key and be
taken to that file and that match. You can also invoke the Goto Symbol command
(*Goto > Goto Symbol...*) to get a list of all of the files that match your
query.

## Development

TODO. (talk about current development and testing)

[ST]: https://www.sublimetext.com/
[CS]: https://code.google.com/p/codesearch/
[SublimeCodeSearch]: https://github.com/whoenig/SublimeCodeSearch
