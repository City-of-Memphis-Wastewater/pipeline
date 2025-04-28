# secrets.yaml
Access will not work without a secrets.yaml file in /pipeline/projects/your-project-name/config/secrets.yaml

// Example secrets.yaml:
```
inhouse_apis:
  server1:
    url: "http://some-site/api/v1/"
    username: "basic"
    password: "1234poiu"
  server2:
    url: "http://some-ip-address:port/api/v1/"
    username: "thunder"
    password: "5&5&5&!"
    
contractor_api:
  url: "https://contractor-api.com/v1/special/"
  client_id: "chonka-chonka-special"
  password: "2685steam"
```