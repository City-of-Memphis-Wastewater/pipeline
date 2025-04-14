Invoke-WebRequest -Uri 'http://172.19.4.127:43080/login' `
-Method POST `
-Headers @{
    "Content-Type" = "application/json"
    "api-key" = "63PjmdIZ.zR4L0RLdZJNulqpboZKCL"
    "Cookie" = "csrftoken=HB5kNWCDrMTT2b4uPh2sE3u0vAmUjCC4jQvKL6ERqNiftwxZqLjTwIjdG93rUAEk"
} `
-Body '<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:eds="http://tt.com.pl/eds/">
    <SOAP-ENV:Body>
        <eds:login>
            <eds:username>operator</eds:username>
            <eds:password>Operator1</eds:password>
        </eds:login>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'
