#!/usr/bin/env python
"""
Runs multiple table tests in parallel, using the test-table.py command. Each
test is allowed to have its own success-defining parameters (--minout,
--minstrings, or --checker module).

Reads a list of test specifications from an input file (or stdin), runs them
using a pool of worker threads, reports the results, and exits with the return
code set to the number of failed tests.

Test specifications are one per line and consist of a path to a table
specification, possibly accompanied by parameters understood by the test-table
command. If the --parms argument is included, its content is prepended to
each test specification. Then the test is executed by invoking test-table.py
on the specification.
"""

import argparse
from collections import namedtuple
import os.path
import Queue
from subprocess import Popen, PIPE
import sys
import threading

Line = namedtuple("Line", "lineNo data")
Result = namedtuple("Result", "worker lineNo status line output")

args = None
tests = Queue.Queue()
results = Queue.Queue()
errCount = 0

myDir = os.path.dirname(os.path.realpath(__file__))
testerPath = os.path.join(myDir, 'test-table.py')

def parseArgs(args):
    p = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--parms', action='store', metavar='',
        help="parameter string to be prepended to all tests")
    p.add_argument("-t", '--threads', action='store', type=int, default=5,
        metavar='n',
        help="the maximum number of tests to run in parallel (default 5)")
    p.add_argument('tables', type=argparse.FileType('rb'), nargs='?',
        default=sys.stdin,
        help="a file listing tables to be tested, one per line, "
             "optionally with arguments (default stdin)")
    p.add_argument('-s', '--sort', action='store_true',
        help="show test results in input order instead of completion order")
    p.add_argument('-f', '--failonly', action='store_true',
        help="only show results for failed tests")
    return p.parse_args(args)

# Main run loop. Launches a pool of worker threads, feeds them tests to run,
# and pulls back and prints out the results
def run():
    for x in xrange(max(args.threads, 1)):
        t = threading.Thread(target=worker, name='W%s' % x)
        t.daemon = True
        t.start()
    lineNo = 0
    maxWidth = 0
    for line in args.tables:
        lineNo += 1
        line = line.strip()
        maxWidth = maxWidth if len(line) <= maxWidth else len(line)
        tests.put(Line(lineNo, line.rstrip()))
    count = lineNo
    if args.sort:
        r = []
        while lineNo > 0:
            r.append(results.get())
            lineNo -= 1
        for result in sorted(r, key=lambda r: r.lineNo):
            format(result, maxWidth)
    else:
        while lineNo > 0:
            format(results.get(), maxWidth)
            lineNo -= 1
    print "%s of %s tests failed" % (errCount, count)

# Prints out a test result.
def format(r, width):
    global errCount
    if r.status != 'OK':
        errCount += 1
    elif args.failonly:
        return
    print '%*s: %s' % (width, r.line, r.output or r.status)

# Worker thread. Takes tests off the tests queue, runs them, and puts the
# output on the results queue
def worker():
    while True:
        line = tests.get()
        try:
            result = processLine(line)
        except Exception as e:
            workerName = threading.currentThread().name
            result = Result(workerName, line.lineNo, 'err', line.data, str(e))
        results.put(result)

# Runs a test in a subprocess and returns its output encapsulated in a Result
def processLine(line):
    cmd = testerPath + ' --batch '
    if args.parms:
        cmd += args.parms + ' '
    cmd += line.data
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0].rstrip()
    if ':' in output:
        output = output[output.index(':')+1:]
    status = 'OK' if p.returncode == 0 else 'Err'
    workerName = threading.currentThread().name
    return Result(workerName, line.lineNo, status, line.data, output)

if __name__ == '__main__':
    args = parseArgs(sys.argv[1:])
    run()
    sys.exit(errCount)
