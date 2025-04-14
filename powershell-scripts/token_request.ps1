$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    client_id = $env:CLIENT_ID_RJN_CLARITY_API
    password = $env:PASSWORD_RJN_CLARITY_API
} | ConvertTo-Json -Depth 10

$url = "https://rjn-clarity-api.com/v1/clarity/auth"

$data_response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

# Save data locally
$data_response | ConvertTo-Json -Depth 10 | Set-Content -Path "token.json"
