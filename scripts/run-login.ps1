# Writes login response to login-response.txt in this folder.
$OutFile = Join-Path $PSScriptRoot "login-response.txt"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/login" -Method POST -ContentType "application/json" -Body '{"email":"karim@yahoo.com","password":"test123"}' -UseBasicParsing
    $response.Content | Set-Content $OutFile -Encoding utf8
} catch {
    @("Status: " + $_.Exception.Response.StatusCode.value__, "Body: " + $_.ErrorDetails.Message) | Set-Content $OutFile -Encoding utf8
}
