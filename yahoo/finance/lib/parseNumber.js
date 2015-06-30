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
