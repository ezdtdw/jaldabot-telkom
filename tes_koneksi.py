import gspread
from google.oauth2.service_account import Credentials
import requests

# ----------------------------------------------------
# 1. KONFIGURASI BOT TELEGRAM (Dari Mas Margo)
# ----------------------------------------------------
TOKEN_BOT = "8928405538:AAE1zxWBwXOeM2tzmPFJsOy58DMMliSBfcM"

# Tes Bot Telegram
url_bot = f"https://api.telegram.org/bot{TOKEN_BOT}/getMe"
response = requests.get(url_bot).json()

if response.get("ok"):
    print(f"✅ Telegram Bot Terhubung! Nama Bot: @{response['result']['username']}")
else:
    print("❌ Token Bot Telegram Salah / Error!")

# ----------------------------------------------------
# 2. KONFIGURASI GOOGLE SHEET (Dari Mas Margo)
# ----------------------------------------------------
SHEET_ID = "1i9Sz8IRQXnGu6fb-88vKrsNbUqovaN2BbNegVNzmHWo"
JSON_FILE = "credentials.json" # Pastikan file JSON ada di folder yang sama

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_file(JSON_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Buka Spreadsheet milik Mas Margo
    sheet = client.open_by_key(SHEET_ID).sheet1
    
    # Coba kirim data tes ke baris paling bawah
    data_tes = ["TES BOT", "TELKOM SAMARINDA", "SISTEM BERJALAN"]
    sheet.append_row(data_tes)
    
    print("✅ Google Sheet Terhubung! Data tes berhasil masuk ke sheet Mas Margo.")

except Exception as e:
    print(f"❌ Error Google Sheet: {e}")