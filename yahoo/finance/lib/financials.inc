
// Scraper for the financials: the income statement, the balance sheet, and
// the cash flow statement. Expects reporttype_code to indicate which ('is',
// 'bs', 'cf'). Hopefully, the three will remain scrapable by common code.
%include common.inc

// Assumes reporttype_code has been set to one of 'is', 'bs', or 'cf'.
var url = "http://finance.yahoo.com/q/" + reporttype_code + "?s=" + symbol + "&" + timeframe;
var restquery = y.rest(url);
var rawresult = restquery.accept("text/html").get().response;
var query = y.xpath(rawresult, "//table[@class='yfnc_tabledata1']//tr/td/table//tr");

// Process Results
var outputdata = <{reporttype} symbol={symbol} timeframe={timeframe}></{reporttype}>;
if (query.*.length() !== 0)
{
    var c = 0;
    var numcolumns = 0;
    var data_array = new Array();

    // Read Column Headings
    data_array[0] = new Array();
    data_array[0][0] = "Headings";
    for each (var node in query[0].*)
    {
        data_array[c] = new Array();
        data_array[c][0] = allText(node);
        c++;
    }
    numcolumns = c;

    // Read Rows
    var r = 1;
    var i = 1;
    while (i < query.length())
    {
        var row = query[i];
        if(row.td.length() >= numcolumns){
            c = 0;
            // read each column in row
            for each (var column in row.td){
                if ("spacer" in column)
                    continue;
                var dataitem = allText(column);
                if (c == 0)
                    dataitem = makeFieldName(dataitem).name;
                else
                    dataitem = parseNumber(dataitem, 1000);
                data_array[c][r] = dataitem;
                c++;
            }
            r++;
        }
        i++;
    }
    var numrows = r;

    // Append the results to the XML tree
    for(c = 1; c < numcolumns; c++){
        var period = data_array[c][0];
        var financial_period = <statement period={period}></statement>;
        for(r = 1; r < numrows; r++){
            row_name = data_array[0][r];
            data = data_array[c][r];
            financial_period.appendChild(<{row_name} report_row={r}>{data}</{row_name}>);
        }
        outputdata.appendChild(financial_period);
    }
}
response.object = outputdata;
