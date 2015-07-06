// A trivial web server, suitable for serving YQL tables to Yahoo.

// Listens on port 8080 by default. Responds only to GET requests for files in
// the directory tree below the current directory. Replies 404 for anything
// else.

// To use, change into the directory above your repo and issue
//     go run yql-tables/yahoo/finance/bin/httpd.go <alternate port>

// Note: For some reason, Yahoo refuses to fetch from other than port 80
// or 8080.

// To use, you need Google's Go Programming Language (see https://golang.org/).
package main

import (
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "sync"
    "time"
)

type foo struct {
    sync.Mutex
    serialNo    int
}

func (f *foo) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    f.Lock(); f.serialNo++; serialNo := f.serialNo; f.Unlock()
    response := 200
    if len(r.URL.Path) < 1 {
        r.URL.Path = "![empty path]"
    }
    fn := r.URL.Path[1:]
    data, err := ioutil.ReadFile(fn)
    if err != nil {
        response = 404
        http.NotFound(w, r)
    } else {
        w.Write(data)
    }
    ts := time.Now().Format("01-02 15:04:05.000")
    ip := fmtRemoteAddr(r.RemoteAddr)
    fmt.Printf("%9v %v: %15v  %v %v  %v\n",
            serialNo % 1000000000, ts, ip, r.Method, response, r.URL)
}

func fmtRemoteAddr(s string) string {
        for x:=len(s)-1; x>=0; x-- {
        if s[x] == ':' {
            s = s[:x]
            if s == "[::1]" {
                s = "localhost"
            }
            break
        }
    }
    return s
}

func main() {
    portNumber := "8080"
    if len(os.Args) > 1 {
        portNumber = os.Args[1]
    }
    fmt.Printf("Listening on port %v\n", portNumber)
    http.ListenAndServe(":" + portNumber, &foo{})
}
