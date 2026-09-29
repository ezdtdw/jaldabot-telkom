import requests

TOKEN_BOT = "8928405538:AAE1zxWBwXOeM2tzmPFJsOy58DMMliSBfcM"
url = f"https://api.telegram.org/bot{TOKEN_BOT}/setMyCommands"

data = {
    "commands": [
        {"command": "req", "description": "Bikin request laporan baru (Troubleshoot/Mandeg/Fallout)"}
    ]
}

response = requests.post(url, json=data)

if response.json().get("ok"):
    print("✅ MANTAP! Menu /req saja yang sekarang muncul di grup!")
else:
    print("❌ Gagal:", response.text)