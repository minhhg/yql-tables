#!/usr/bin/env node
// Unit tests for parseNumber.js

//%begin-include ../lib/parseNumber.js
// Normalizes suffixed Yahoo Finance numbers to numeric values.
// Deletes %-signs. Multiplies by scale, if provided.
function parseNumber(n, scale) {
    if (!n)
        return n;
    n = String(n);
    if (/^\s*(?:[nN]\/?[aA])|-\s*$/.test(n))
        return '';
    var m = n.match(/^\s*(?:\(\s*([0-9.,]+[bBmMkK%]?)\s*\))\s*$/);
    if (m)
        n = '-' + m[1];
    var m = n.match(/^\s*(?:([+-])\s*)?([0-9.,]+)\s*([BbMmKk%]?)\s*$/);
    if (!m)
        return n
    var value = (m[1] == '-' ? -1 : 1) * m[2].replace(/,/g, '');
    switch (m[3]) {
        case 'b':
        case 'B':
            value = +(value + 'e9');
            break;
        case 'm':
        case 'M':
            value = +(value + 'e6');
            break;
        case 'k':
        case 'K':
            value = +(value + 'e3');
            break;
        default:
            value = +value;
    }
    if (scale)
        value *= scale;
    return value;
}
//%end-include 28844b4b00243e230a279e71cf5d443485749fad

var okCount = 0, errCount = 0;

function test(text, goodNumber, scale) {
    function quote(n) {
        return typeof n == 'number' ? n : "'" + n + "'";
    }
    var number = parseNumber(text, scale);
    if (typeof number != typeof goodNumber) {
        console.log("Expected a " + typeof goodNumber + "; got a " +
                    typeof number + " (" + quote(number) + ").");
        errCount++;
        return;
    }
    if (number != goodNumber) {
        console.log("For " + quote(text) + ": got " + quote(number) +
                            "; expected " + quote(goodNumber) + '.');
        errCount++;
    } else {
        okCount++;
    }
}

test('  - ', '');
test('  N/A ', '');
test('n/a', '');
test('NA', '');
test('na', '');
test('42', 42);
test('  42 ', 42);
test(' (42) ', -42);
test('42.1%', 42.1);
test('-42.1%', -42.1);
test(' (42.1%)', -42.1);
test(' - 42.1%', -42.1);
test(' +8.91%', 8.91);
test('   763.57B', 763570000000);
test(' 182,795,000K ', 182795000000);
test(' 3.141593B', 3141593000);
test(' - 3.141593M ', -3141593);
test(' ( 3.141593k )', -3141.593);
test('(3.14159)', -3.14159);
test(' (800) 676-2775', ' (800) 676-2775');
test('67,491,000', 67491000000, 1000);
test('(13,171,000)', -13171000000, 1000);
test('0.142857142857142857', 1, 7);

console.log(okCount + " tests passed; " + errCount + " failed.");
process.exit(+(errCount != 0));
