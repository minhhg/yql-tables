Fixes and Additions
===================

Fixes
-----

Working versions of the following tables, which have broken in the official
version due to changes in page structure by Yahoo:

  - yahoo.finance.analystestimate.xml
  - yahoo.finance.balancesheet.xml
  - yahoo.finance.cashflow.xml
  - yahoo.finance.incomestatement.xml
  - yahoo.finance.keystats.xml
  - yahoo.finance.stocks.xml

Additions
---------

Several new tables provide easy access to Yahoo Finance's CSV feeds:

- **yahoo.finance.csvdivsandsplits.xml —** Provides price, dividend, and split
  history, at daily, weekly, or monthly granularity or only when a dividend or
  split actually occurred.
- **yahoo.finance.csvhistory.xml —** Provide price and dividend history
  at daily, weekly, or monthly granularity or dividends only.
- **yahoo.finance.csvquote.xml —** Efficiently returns a variety of quote
  data for a list of stocks. You can customize which fields are returned.

###Testing Facility

The ``bin`` directory contains two commands to facilitate testing tables in scriptable fashion without using the YQL Console:

- **test-table.py —** Tests tables one at a time, optionally providing a
  formatted dump of the returned JSON.
- **batch-test.py —** Runs a number of table tests in parallel and reports
  the results. Useful for regression testing.

For more info on the above, enter the command name with the `-h` parameter.

###Code Inclusion (Enforcing [DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself))

The ``update-includes.py`` command in ``bin`` scans a list of table ``.xml``
files and refreshes any *code includes* they may contain. A code include
contains a chunk of code from the ``lib`` directory between special
comments, e.g.::

    //%begin-include lib/financials.inc
    ... included code placed here ...
    //%end-include 99ffcfaadcfd783e96bb351bf2d9c6c430efc3e5

The long hex code on the end comment is the SHA1 hash of the text between the
special comment lines. At update time, ``update-includes.py`` recalculates
the SHA1 of the existing included code and compares it to the value in the
end comment. If it matches, ``update-includes.py`` replaces the included code
with the current include. Otherwise, it issues a warning about outside editing,
and the user should reissue the command with the ``--force`` option once
inconsistencies are resolved. When first adding an include, omit the SHA1 from the end comment.

Note: YQL's [``y`` object](https://developer.yahoo.com/yql/guide/yql-javascript-objects.html)
has an ``include`` method, however, it requires a URL, which will change
depending on the table's execution environment. Code inclusion at development
time avoids that problem and saves a network fetch.

###Lib Unit Tests

Several of the include files in ``lib`` have unit tests in ``bin``. These
expect [``node.js``](https://nodejs.org/) to be installed.

Development Environment
-----------------------
