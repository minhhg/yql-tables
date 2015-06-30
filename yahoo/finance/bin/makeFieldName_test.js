#!/usr/bin/env node
// Unit tests for makeFieldName.js

//%begin-include ../lib/makeFieldName.js
// Converts an HTML display name into a JavaScript identifier. Also
// splits out any parenthesized qualifying term, such as "ttm",
// "intraday", "mrq", or "yoy".
function makeFieldName(name) {
    name = String(name).replace(/:/g, '');
    var m = name.match(/^(.*?)\s*\((.+?)\)\s*$/);
    var term = null;
    if (m) {
        name = m[1];
        term = m[2];
    }
    name = name.replace(/\b(.)/g, function(s){
        return s.toUpperCase();
    });
    name = name.replace(/[\s-]+/g, '');
    name = name.replace(/%/g, 'Pct');
    name = name.replace(/&/g, 'And');
    name = name.replace(/([a-z])\//g, '$1To');
    name = name.replace(/\W/g, '');
    if (/^\d/.test(name))
        name = 'P_' + name;
    return {name:name, term:term};
}
//%end-include f7025d612cf0503731d742185c16e0e5ed32432c

var okCount = 0, errCount = 0;

function test(text, goodName, goodTerm) {
    function quote(n) {
        return typeof n == 'number' ? n : "'" + n + "'";
    }
    var result = makeFieldName(text);
    var errs = 0;
    if (result.name != goodName) {
        console.log("For " + quote(text) + ": got " + quote(result.name) +
                            "; expected " + quote(goodName) + '.');
        errs++;
    }
    if (result.term != goodTerm) {
        console.log("For " + quote(text) + ": got term = " +
                    quote(result.term) + "; expected " + quote(goodTerm));
        errs++;
    }
    if (errs == 0)
        okCount++;
    else
        errCount++;
}


test('200-day Moving Average', 'P_200DayMovingAverage');
test('% Held by Institutions', 'PctHeldByInstitutions');
test('% net Shares Purchased (Sold)', 'PctNetSharesPurchased', 'Sold');
test('Ex-Dividend Date', 'ExDividendDate');
test('  No. of Analysts  \n', 'NoOfAnalysts');
test('Market Cap (intraday)', 'MarketCap', 'intraday');
test('Price/Sales(ttm)', 'PriceToSales', 'ttm');
test('Enterprise Value/EBITDA', 'EnterpriseValueToEBITDA');
test('Trailing P/E\n(ttm, intraday)\n', 'TrailingPE', 'ttm, intraday');
test('Sales, General, and Administrative ', 'SalesGeneralAndAdministrative');
test('Sales, General & Administrative', 'SalesGeneralAndAdministrative');
test('Long-term Debt', 'LongTermDebt');

console.log(okCount + ' tests passed; ' + errCount + ' failed.');
process.exit(+(errCount != 0));
