#!/usr/bin/env python
"""
A tool to automate the testing of YQL tables.

Runs a query against each table provided and reports on whether it appears to
have "worked". Sets the return code to to 0 if all queries worked, or 1 if
not.

By default, the query run is the sample query defined in the table. However,
you can provide substitute WHERE clause content, if desired.

A query is deemed successful if
    * No exception was raised during its running
    * No JavaScript error was found in the diagnostic output
    * At least a minimum amount of JSON query output was received
The standard checker counts the strings received in the JSON results and sums
their length. Then, it deems the query to have worked if it satisfied those
minimum values (see -m and -minstrings).

If you want, you can provide a checker module written in Python to check the
query output. It should contain a check method which will receive the full
JSON and should return a short summary message and a boolean: False if
no error, else True.

You will need to set the YQL_ENV environment variable to contain the URL of
your .env file. Your .env file should contain USE statements for each table
you have added or modified, followed by

        ENV "store://datatables.org/alltableswithkeys";

to make the system tables available.

Note: The --noenv and --debug options formulate the USE statement assuming that
your tables are stored alongside your .env file at the same site. E.g., if
your tables.env is at http://example.com/tables.env, then your highfinance table
must be available at http://example.com/yahoo.finance.highfinance.xml.
"""
import argparse
from collections import defaultdict, namedtuple
import imp
import json
import os
import os.path
import re
import sys
import urllib2
import urllib
from urlparse import urlparse
import xml.etree.cElementTree as ET

Result = namedtuple('Result', 'tablePath status json, err')

DefaultYqlEnv = ('https://raw.githubusercontent.com/'
                        'cynwoody/yql-tables/finance-1/tables.env')
# DefaultYqlEnv = "store://datatables.org/alltableswithkeys"
YqlEnv = os.environ.get('YQL_ENV', DefaultYqlEnv)
p = urlparse(YqlEnv)
ServerUrl = p.scheme + '://' + p.netloc

URL = ("http://query.yahooapis.com/v1/public/yql?"
                "q=%s&format=json&diagnostics=true")

args = None

def parseArgs(argv):
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-q", '--quiet', action='store_const', const="quiet",
        dest='output',
        help="omit output and set the return code only")
    p.add_argument("-s", "--summarize", action='store_const', const="summarize",
        dest='output', default='summarize',
        help="print a short summary of the test output (default)")
    p.add_argument("-v", "--verbose", action='store_const', const="verbose",
        dest='output',
        help="print the summary followed by the JSON pretty-printed")
    p.add_argument("-j", "--json", action='store_const', const="json",
        dest='output',
        help="write only the raw json to stdout")
    p.add_argument('-m', '--minout', action='store',
        metavar='16', default=16, type=int,
        help="the minimum output bytes for test to have worked")
    p.add_argument('--minstrings', action='store',
        metavar='7', default=7, type=int,
        help="the minimum data points for test to have worked")
    p.add_argument('-w', '--where', action='store', metavar='',
        help="a value to replace the WHERE clause's content")
    p.add_argument('-c', '--checker', action='store', metavar='',
        help="the path to a Python module to call to check the output")
    p.add_argument('--noenv', action='store_true',
        help="do not pass the env parameter. Add a USE statement to the query "
                "instead")
    p.add_argument('--debug', action="store_true",
        help="set debug=true in the query. Implies --noenv")
    p.add_argument('--batch', action='store_true',
        help="used by the batch-test utility")
    p.add_argument('tables', nargs='+')
    return p.parse_args(argv)

# The main run loop
def run():
    if not args.output in ('quiet', 'json') and not args.batch:
        print "YQL environment:", YqlEnv
    results = []
    for tablePath in args.tables:
        try:
            j, status, err = testTable(tablePath)
        except Exception as e:
            j = None
            status = e
            err = True
        results.append(Result(tablePath, status, j, err))
    formatter = globals().get('fmt_%s' % args.output, fmt_summarize)
    return formatter(results)

def okErr(arg):
    return 'Err' if arg else 'OK'

def fmt_quiet(results):
    return reduce(lambda x, y: x|y, (r.err for r in results))

def fmt_summarize(results):
    width = max(len(r.tablePath) for r in results)
    for r in results:
        print "%*s: %3s %s" % (width, r.tablePath, okErr(r.err), r.status)
    return fmt_quiet(results)

def fmt_verbose(results):
    for r in results:
        print '%s: %s %s' % (r.tablePath, okErr(r.err), r.status)
        if r.json:
            if type(r.json) in (dict, list):
                print json.dumps(r.json, indent=4, sort_keys=True)
            else:
                print r.json
    return fmt_quiet(results)

def fmt_json(results):
    for r in results:
        if r.json:
            print json.dumps(r.json)
    return fmt_quiet(results)

# Tests a table and returns the JSON, the summary string, and the error boolean
def testTable(tablePath):
    url = urlFor(tablePath)
    try:
        u = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        data = e.read()
        e.close()
        try:
            data = json.loads(data)
        except:
            pass
        return data, e, True
    data = u.read()
    u.close()
    j = json.loads(data)
    assessment, err = assessRun(j)
    return j, assessment, err

# Computes the URL to run the query on the table
def urlFor(tablePath):
    baseName = os.path.basename(tablePath)
    tableName = os.path.splitext(baseName)[0]
    try:
        root = ET.parse(tablePath).getroot()
    except Exception as e:
        raise Exception("Error parsing query XML: %s" % e)
    nsUrl = root.tag[1:].partition('}')[0]
    ns = dict(y=nsUrl)
    query = root.find('./y:meta/y:sampleQuery', ns)
    if query is None:
        raise Exception('No sample query is defined')
    query = query.text
    if not query or not query.strip():
        raise Exception('Empty sample query')
    query = query.strip().replace('{table}', tableName)
    query = editQuery(query)
    if args.debug or args.noenv:
        query = 'use "%s/%s";%s' % (ServerUrl, baseName, query)
        url = URL % urllib.quote(query)
        if args.debug:
            url += "&debug=true"
    else:
        url = URL % urllib.quote(query)
        url += "&env=" + urllib.quote(YqlEnv)
    return url

# Substitutes the user's predicate, if any, into the WHERE clause
def editQuery(query):
    if not args.where:
        return query
    m = re.match(r'^(.*?WHERE\s)(.*)$', query, re.I | re.S)
    if not m:
        return query
    return m.group(1) + args.where

# Decides if the query ran. Returns a summary string and an error boolean
def assessRun(j):
    jq = j['query']
    js = findJavaScript(jq)
    if js:
        jsErr = javaScriptOk(jq)
        if jsErr:
            return jsErr, True
    if args.checker:
        m = imp.load_source('checkerMod', args.checker)
        return m.check(j)
    err = False
    results = jq['results']
    if results is None:
        return 'No results', True
    f = jsonTypes(results)
    status = ("dicts/lists/ints/strings/stringLen/Nones = %s/%s/%s/%s/%s/%s" %
            (f[dict], f[list], f[int], f[unicode] + f[str], f['strLen'],
                    f[type(None)]))
    if f['strLen'] < args.minout:
        status += "; %s < minout of %s" % (f['strLen'], args.minout)
        err = True
    objCount = f[unicode] + f[str]
    if objCount < args.minstrings:
        status += "; %s < minstrings of %s" % (objCount, args.minstrings)
        err = True
    insts = instructions(js)
    if insts:
        status += ' / ' + str(insts) + ' instructions'
    return status, err

def findJavaScript(jq):
    if 'diagnostics' not in jq:
        return
    j = jq['diagnostics']
    if 'javascript' not in j:
        return
    return j['javascript']

# Checks for a JavaScript reported in the diagnostics
def javaScriptOk(js):
    e = filter(lambda x:'Exception' in x, js)
    if e:
        return e[0]

# Scans a JSON object and returns a table containing the count of each
# datatype found therein, together with the total length of its strings.
def jsonTypes(j):
    f = defaultdict(int)
    def count(j):
        t = type(j)
        f[t] += 1
        if t is list:
            for e in j:
                count(e)
        elif t is dict:
            for e in j.values():
                count(e)
        elif t in (unicode, str):
            f['strLen'] += len(j)
    count(j)
    return f

# Adds up the instruction counts from the JavaScript blocks
def instructions(js):
    if not js:
        return
    if type(js) != list:
        js = [js]
    return sum(int(j['instructions-used']) for j in js)

if __name__ == '__main__':
    args = parseArgs(sys.argv[1:])
    err = run()
    sys.exit(err)
