#!/usr/bin/env node
// Unit tests for parseDate.js
MockDate = require('mockdate');     // npm install mockdate

//%begin-include ../lib/parseDate.js
// Returns the year, month, and day corresponding to the input date,
// which should be in the form yyyy-mm-dd. Returns today's date if
// date omitted.
function parseDate(date) {
    var d = new Date;
    if (date) {
        var m = date.match(/^(\d\d\d\d)-(\d+)-(\d+)$/);
        if (!m)
            throw "Invalid date: '" + date + "'";
        var d = new Date(m[1], m[2]-1, m[3]);
    }
    return {y:d.getFullYear(), m:d.getMonth(), d:d.getDate()};
}
//%end-include eb3a754dc5c86babc736a5d5381bca1e618e3ac0

var okCount = 0, errCount = 0;

function pad(n) {return (n/100).toFixed(2).slice(2)}

function fmt(y, m, d) {
    return y + '-' + pad(m+1) + '-' + pad(d);
}

function test(text, y, m, d, when) {
    if (when)
        MockDate.set(when);
    try {
        var r = parseDate(text);
        var good = y ? fmt(y, m, d) : "exception";
        var got = fmt(r.y, r.m, r.d);
        if (got == good)
            okCount++;
        else {
            console.log("For " + text + ", expected " + good + "; got " + got);
            errCount++;
        }
    } catch (e) {
        if (y) {
            console.log("For " + text + ", expected " + fmt(y, m, d) +
                                "; got " + e);
            errCount++;
        } else
            okCount++;
    } finally {
        MockDate.reset()
    }
}

test('1941-12-07', 1941, 11, 7);
var today = new Date;
test(undefined, today.getFullYear(), today.getMonth(), today.getDate());
test(null, today.getFullYear(), today.getMonth(), today.getDate());
test('', today.getFullYear(), today.getMonth(), today.getDate());
test('garbage');
test('2015-05-31', 2015, 4, 31, '2015-05-31 23:59:59 EDT');
test('2015-5-31', 2015, 4, 31, '2015-05-31 23:59:59 EDT');
test('2015-12-31', 2015, 11, 31, '2015-12-31 23:59:59 EST');
test('2015-05-31', 2015, 4, 31, '2015-05-31 EDT');
test('2015-5-31', 2015, 4, 31, '2015-05-31 EDT');
test('2015-12-31', 2015, 11, 31, '2015-12-31 EST');
test(undefined, 2015, 11, 31, '2015-12-31 EST');
test(undefined, 2015, 11, 31, '2015-12-31 23:59:59 EST');
test(undefined, 2015, 11, 30, '2015-12-30 21:00:00 EST');
test(undefined, 2015, 11, 30, '2015-12-31 GMT');
test(undefined, 2015, 11, 31, '2015-12-31 23:59:59 GMT');
test('2015-12-32', 2016, 0, 1);

console.log(okCount + " tests passed; " + errCount + " failed.");
process.exit(+(errCount != 0));
