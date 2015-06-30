#!/usr/bin/env python
"""
Updates all include blocks in the specified source files.

An include block starts out looking like:

    //%begin-include filepath
    //%end-include

where filepath is the path to another file, the contents of which are to be
added between the begin and end comments. The filepath is assumed to be
relative to the file containing the inclusion.

After update-includes has processed the file the first time, the include block
looks like:

    //%begin-include filepath
    Some lines of code from the included file...
    ...
    //%end-include [SHA-1 hashcode of the included lines]

After modifications have been made to the included files, run update-includes
again, and it will replace the existing includes with the updated versions,
providing the existing includes have not been independently modified (which
would change the SHA-1 hash). Use the --force option to ignore hashcode
mismatches.
"""

import argparse
from collections import namedtuple
import hashlib
import os.path
import re

args = namedtuple('Args', 'force')(False)

def run():
    global args
    parser = argparse.ArgumentParser(description=__doc__,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-f", '--force', action='store_true',
        help="complete update despite any independent edits to include blocks")
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    outList = []
    errCount = 0
    for f in args.files:
        if os.path.isdir(f):
            continue
        try:
            msg, err = processFile(f)
        except Exception as e:
            msg = e.message or e.strerror or str(e)
            err = 1
        errCount += err
        if err or msg != 'No includes found':
            outList.append((f, msg))
    if outList:
        maxWidth = max(len(f) for f, m in outList)
        print '\n'.join('%*s: %s' % (maxWidth, f, m) for f, m in outList)
    else:
        print "No includes were processed."
    return errCount

def processFile(filePath):
    extension = os.path.splitext(filePath)[1]
    search = makeSearcher(extension)
    with open(filePath, 'rb') as f:
        fileData = f.read()
    m = search(fileData)
    if not m:
        return "No includes found", 0
    fileDir = dirName(filePath)
    comment = extToComment[extension]
    editedFile = ''
    pos = 0
    includeCount = 0
    while True:
        editedFile += fileData[pos:m.end()]
        indent, beginInclude, endInclude, include, path = m.groups()
        pos = m.end()
        if not beginInclude:
            if include:
                return "Unexpected %%include %s" % (path or "[missing]"), 1
            else:
                return "Unexpected %endInclude", 1
        if not path:
            return "Path missing on %s%%begin-include" % comment, 1
        m = search(fileData, pos)
        if not m:
            return "Missing end-include for %s" % path, 1
        indent, beginInclude, endInclude, include, sha1 = m.groups()
        if not endInclude:
            return ("Unexpected %%%s including %s" %
                                    (beginInclude or include, path)), 1
        if not args.force and sha1:
            if sha1 != hashlib.sha1(fileData[pos:m.start()]).hexdigest():
                return ('Include %s has been edited; bypassing update. ' +
                        'Use --force to override') % path, 1
        try:
            text = loadInclude(os.path.join(fileDir, path))
        except Exception as e:
            return "Error including %s: %s" % (path, e.strerror or str(e)), 1
        sha1 = hashlib.sha1(text).hexdigest()
        editedFile += text
        editedFile += '%s%s%%end-include %s\n' % (indent, comment, sha1)
        pos = m.end()
        includeCount += 1
        m = search(fileData, pos)
        if not m:
            editedFile += fileData[pos:]
            if editedFile != fileData:
                with open(filePath, 'wb') as f:
                    f.write(editedFile)
            return successMsg(editedFile != fileData, includeCount)

def successMsg(changed, includeCount):
    return ("%s (%s include%s)" %
                ('Updated' if changed else "Unchanged",
                 includeCount,
                 '' if includeCount == 1 else 's'), 0)

includeCache = {}

def loadInclude(filePath):
    if filePath in includeCache:
        return includeCache[filePath]
    fileData = loadIncludeFile(filePath)
    includeCache[filePath] = fileData
    return fileData

def loadIncludeFile(filePath):
    extension = os.path.splitext(filePath)[1]
    search = makeSearcher(extension)
    with open(filePath, 'rb') as f:
        fileData = f.read()
    m = search(fileData)
    if not m:
        return fileData
    fileDir = dirName(filePath)
    result = ''
    pos = 0
    while True:
        result += fileData[pos:m.start()]
        pos = m.end()
        indent, beginInclude, endInclude, include, path = m.groups()
        if not include:
            raise Exception("%s illegal in included file %s" %
                        (beginInclude or endInclude, filePath))
        if not path:
            raise Exception("Path missing from %%include in %s", filePath)
        result += loadInclude(os.path.join(fileDir, path))
        m = search(fileData, pos)
        if not m:
            result += fileData[pos:]
            return result

def dirName(path):
    return os.path.realpath(os.path.dirname(path))

extToComment = {
    '.js':  "//",
    '.xml': "//",
    '.py':  "#",
    '.inc': '',
}

searcherCache = {}

def makeSearcher(extension):
    if extension in searcherCache:
        return searcherCache[extension]
    r = (r'^(?:([ \t]*)%s%%(?:(begin-include)|(end-include)|(include)))'
                r'[ \t]*(\S+)?[ \t]*\n' %
            extToComment.get(extension, '#'))
    searcher = re.compile(r, re.M).search
    searcherCache[extension] = searcher
    return searcher

if __name__ == '__main__':
    exit(run())
