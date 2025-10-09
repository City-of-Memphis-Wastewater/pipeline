from urllib.parse import quote_plus

api_url = "https://123scada.com/Mc.Services"
username = "george.bennett@memphistn.gov"
password = "USL-Px8hTeu3zfc"

data = {
	"grant_type": "password",
	"username": username,
	"password": password,
	"client_id": "123SCADA",
	"authenticatorCode": ""
}

# URL-encode each field
data_str = "&".join(f"{k}={quote_plus(v)}" for k, v in data.items())
print(f"data_str = {data_str}")