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
