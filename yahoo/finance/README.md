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

The ``bin`` directory contains two commands to facilitate running table tests locally without using the YQL Console and to automate regression testing:

- **test-table.py —** Tests tables one at a time, optionally providing a
  formatted dump of the returned JSON.
- **batch-test.py —** Runs a number of table tests in parallel and reports
  the results. Useful for regression testing.

For more info on the above, enter the command name with the `-h` parameter.

As development proceeds, it is advisable to keep around a script to test all the
tables under current development at once. For an example, see ``run-tests``. It
runs the ``batch-test.py`` command on the tables of interest.

###Code Inclusion (Enforcing the [DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself) Principle)

It often happens that JavaScript functions will prove useful in more than one
table definition. As these functions evolve, it is clumsy and error-prone to
keep all of the tables that use them up to date. Instead, it is better to store
one copy of each reusable code segement in a ``lib`` directory and provide an
automated way to get each piece of common code into each table that needs it.

The ``update-includes.py`` command in ``bin`` scans a list of table files and
refreshes any *code includes* they may contain with the current ``lib`` version
of the include. A code include contains a chunk of code from the ``lib``
directory between special comments, e.g.::

    //%begin-include lib/financials.inc
    ... included code placed here ...
    //%end-include 99ffcfaadcfd783e96bb351bf2d9c6c430efc3e5

The long hex code on the end comment is the SHA1 hash of the text between the
special comment lines. At update time, ``update-includes.py`` recalculates the
SHA1 of the existing included code and compares it to the value in the end
comment. If it matches, ``update-includes.py`` replaces the included code with
the current include. Otherwise, it issues a warning pointing out the separate
editing, and, once inconsistencies between local version of the code and library
version are resolved, the user should reissue the command with the ``--force``
option. This will cause ``update-includes.py`` to replace the include everywhere
with the ``lib`` version, losing any local edits.

When first adding an include, omit the SHA1 from the end comment.

Note: YQL's [``y`` object](https://developer.yahoo.com/yql/guide/yql-javascript-objects.html)
has an ``include`` method, however, it requires a URL, which will change
depending on the table's execution environment. Code inclusion at development
time avoids that problem and saves a network fetch.

###Lib Unit Tests

Several of the include files in ``lib`` have unit tests in ``bin``. These
expect [``node.js``](https://nodejs.org/) to be installed.

Setting up a Development Environment
------------------------------------

To work on the YQL tables, fork a YQL repository, such as this one or the [main
one](https://github.com/yql/yql-tables), and clone it onto your local
filesystem. Then set up your environment as described below.

Before you can test a YQL table you have created or modified, you must post it
on the web and let Yahoo know its URL. The easiest way is to create a YQL
environment file, in which you provide [``use``
statements](https://developer.yahoo.com/yql/guide/external_tables.html) for each
table you have modified, followed by an ``env`` statement to include the tables
in the system environment file, at ``store://datatables.org/alltableswithkeys``.
For an example of an environment file, see ``tables.env`` in the root of this
repository.

In queries run from your local machine, from the YQL Console, or from your
applications, you point the ``env`` parameter at your table.

Note: The ``test-table`` command expects the environment variable ``YQL_ENV`` to
contain the URL of your environment file.

###Hosting Your Tables

You need to get your tables hosted on the web. One option is simply to use
GitHub, via a suitably modified version of the ``tables.env`` in the root of
this repo. Your ``env`` parameter should point to the raw GitHub version of
``tables.env``, and the URLs in ``tables.env`` should point to the raw version
of each table under development in your repo.

However, hosting on GitHub requires you to push your changes before each test.
Therefore, it is more convenient to run a local web server configured to serve
Yahoo the tables straight from your local repository. E.g., your server could
serve the directory just above your repo. There you would place an environment
file containing the absolute URLs of the files in your repo which are under
test. Point ``YQL_ENV`` at the external URL of that environment file, and you
should be ready to develop.

Once things are stable, and you just want to *use* your tables instead of hack
on them, you can switch to using GitHub as your table host.

###A Web Server

In the `bin` directory there is a simple web server named `httpd.go`, written in
Google's Go Programming Language ([download page](https://golang.org/dl/)),
designed for use while developing. By default, it listens on port 8080 (it
appears Yahoo won't fetch from other than ports 80 or 8080, even if there is a
perfectly functional web server listening on another port).

To use it you might:

* Subscribe to a dynamic DNS service and configure your router to keep it
  updated. E.g, if you have a D-Link router, you could use [D-Link's free
  dynamic DNS](https://www.dlinkddns.com/). Let's assume you've done that, and
  you are `developer.dlinkddns.com` (`ping developer.dlinkddns.com` pings your
  home or office).

* Configure your router to forward port 8080 to your development machine.

* Place your `tables.env` in the directory above your local repo. Its URL
  will now be `http://developer.dlinkddns.com:8080/tables.env`.

* In your `tables.env`, provide `use` statements pointing at the tables in
  your repo which differ from those in the community repo. E.g., if you've
  created a new magicnumbers table, its `use` statement would be:
  `use "http://developer.dlinkddns.com:8080/yahoo/finance/yahoo.finance.magicnumbers.xml";`

* In the directory where your `tables.env` lives, issue
  `go run yql-tables/yahoo/finance/bin/httpd.go`.
