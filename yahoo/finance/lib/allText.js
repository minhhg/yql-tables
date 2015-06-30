// Returns the text below the passed node as a trimmed string (YQL's trim
// method appears not to strip newlines).
function allText(node) {
    var text = [];
    for each (var x in node.descendants()) {
        if (x.nodeKind() == 'text')
            text.push(x);
    }
    return text.join(' ').replace(/^\s+|\s+$/g, '');
}
