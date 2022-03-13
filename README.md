Web server test suite
=====================

## Requirements ##

* Respond to `GET` with status code in `{200,404,403}`
* Respond to `HEAD` with status code in `{200,404,403}`
* Respond to all other request methods with status code `405`
* Directory index file name `index.html`
* Respond to requests for `/<file>.html` with the contents of `DOCUMENT_ROOT/<file>.html`
* Requests for `/<directory>/` should be interpreted as requests for `DOCUMENT_ROOT/<directory>/index.html`
* Respond with the following header fields for all requests:
  * `Server`
  * `Date`
  * `Connection`
* Respond with the following additional header fields for all `200` responses to `GET` and `HEAD` requests:
  * `Content-Length`
  * `Content-Type`
* Respond with correct `Content-Type` for `.html, .css, js, jpg, .jpeg, .png, .gif, .swf`
* Respond to percent-encoding URLs
* Correctly serve a 2GB+ files
* No security vulnerabilities

## Testing environment ##

* Put `Dockerfile` to web server repository root
* Prepare docker container to run tests:
  * Read config file `/etc/httpd.conf`
  * Expose port 80

Config file spec:
```
cpu_limit 4       # maximum CPU count to use (for non-blocking servers)
thread_limit 256  # maximum simultaneous connections (for blocking servers)
document_root /var/www/html
```

Run tests:
```
git clone https://github.com/init/http-test-suite.git
cd http-test-suite

docker build -t highload https://github.com/BUSH1997/HighLoad-Server.git -f Dockerfile
docker run -p 40000:80 -t highload --name highload

./httptest.py

ab -n 10000 -c 10 127.0.0.1:40000/httptest/wikipedia_russia.html

docker build -t ng https://github.com/BUSH1997/HighLoad-Server.git -f nginx.Dockerfile
docker run -p 40001:80 -t ng --name ng

ab -n 10000 -c 10 127.0.0.1:40001/httptest/wikipedia_russia.html
```

## Testing  

### Func tests result:  

```asm
Ran 24 tests in 0.019s

OK
```
### Load test result:  

- ab -n 10000 -c 10 127.0.0.1:40000/httptest/wikipedia_russia.html
```
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        BUSH1997
Server Hostname:        127.0.0.1
Server Port:            40000

Document Path:          /httptest/wikipedia_russia.html
Document Length:        954824 bytes

Concurrency Level:      10
Time taken for tests:   14.445 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      9549470000 bytes
HTML transferred:       9548240000 bytes
Requests per second:    692.27 [#/sec] (mean)
Time per request:       14.445 [ms] (mean)
Time per request:       1.445 [ms] (mean, across all concurrent requests)
Transfer rate:          645582.82 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.0      0       1
Processing:     2   14   5.3     13      74
Waiting:        2    9   4.3      8      63
Total:          3   14   5.3     13      74

Percentage of the requests served within a certain time (ms)
  50%     13
  66%     15
  75%     17
  80%     18
  90%     21
  95%     24
  98%     28
  99%     31
 100%     74 (longest request)

```

### Nginx:  
- ab -n 10000 -c 10 127.0.0.1:40001/httptest/wikipedia_russia.html
```asm
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        nginx/1.21.6
Server Hostname:        127.0.0.1
Server Port:            40001

Document Path:          /httptest/wikipedia_russia.html
Document Length:        954824 bytes

Concurrency Level:      10
Time taken for tests:   2.772 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      9550620000 bytes
HTML transferred:       9548240000 bytes
Requests per second:    3607.79 [#/sec] (mean)
Time per request:       2.772 [ms] (mean)
Time per request:       0.277 [ms] (mean, across all concurrent requests)
Transfer rate:          3364904.13 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.0      0       1
Processing:     1    3   0.7      3      37
Waiting:        0    0   0.6      0      35
Total:          1    3   0.7      3      37

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      3
  75%      3
  80%      3
  90%      3
  95%      3
  98%      4
  99%      5
 100%     37 (longest request)

```
