import requests

json = {
  "version": "2.0",
  "routeKey": "GET /",
  "rawPath": "/",
  "pathParameters": {},
  "requestContext": {
    "http": {
      "sourceIp": "192.0.0.1",
      "path": "/",
      "method": "GET"
    }
  }
}
r = requests.get(url="http://localhost:9000/2015-03-31/functions/function/invocations", json=json)
print(r.text)