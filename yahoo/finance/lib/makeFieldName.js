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
