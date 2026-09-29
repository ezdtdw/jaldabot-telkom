import time
import re
import requests
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------
# 1. KONFIGURASI BOT TELEGRAM & GOOGLE SHEET
# ----------------------------------------------------
TOKEN_BOT = "8928405538:AAE1zxWBwXOeM2tzmPFJsOy58DMMliSBfcM"
SHEET_ID = "1i9Sz8IRQXnGu6fb-88vKrsNbUqovaN2BbNegVNzmHWo"
JSON_FILE = "credentials.json"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(JSON_FILE, scopes=scopes)
client = gspread.authorize(creds)

# Akses Tab 1 (Sheet1/Tiket) dan Tab 2 (Data_HD)
sheet_tiket = client.open_by_key(SHEET_ID).worksheet("Sheet1")

# Pastikan tab Data_HD sudah dibuat di Google Sheet
try:
    sheet_hd = client.open_by_key(SHEET_ID).worksheet("Data_HD")
except Exception:
    print("⚠️ Warning: Tab 'Data_HD' belum dibuat di Google Sheet. Silakan buat tab bernama 'Data_HD'!")

print("🤖 Bot Helpdesk Telkom Samarinda (Fitur HD Online & Status /done) Running...")

# ----------------------------------------------------
# 2. FUNGSI KIRIM PESAN & TOMBOL
# ----------------------------------------------------
def send_reply(chat_id, text, message_id=None):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML"
    }
    if message_id:
        payload["reply_to_message_id"] = message_id
    requests.post(url, json=payload)

def send_menu_tombol(chat_id, message_id=None):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🛠️ Troubleshoot", "callback_data": "btn_troubleshoot"},
                {"text": "⚠️ Fallout", "callback_data": "btn_fallout"}
            ],
            [
                {"text": "⏸️ Mandeg", "callback_data": "btn_mandeg"}
            ]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "<b>SISTEM HELPDESK TELKOM SAMARINDA</b>\n\nSilakan pilih kategori request di bawah ini untuk mengambil template laporan:",
        "reply_markup": keyboard,
        "parse_mode": "HTML"
    }
    if message_id:
        payload["reply_to_message_id"] = message_id
    requests.post(url, json=payload)

# ----------------------------------------------------
# 3. FUNGSI UPDATE STATUS HD OFFICER (Tab Data_HD)
# ----------------------------------------------------
def update_status_hd(sender_name, username, chat_id, status_baru):
    all_rows = sheet_hd.get_all_values()
    chat_id_str = str(chat_id)
    found_row = -1

    # Cari apakah HD ini sudah terdaftar berdasarkan Chat ID (Kolom C)
    for idx, row in enumerate(all_rows[1:], start=2):
        if len(row) >= 3 and row[2] == chat_id_str:
            found_row = idx
            break

    if found_row != -1:
        # Update Status di Kolom D
        sheet_hd.update_cell(found_row, 4, status_baru)
    else:
        # Tambah Baris HD Baru
        sheet_hd.append_row([sender_name, f"@{username}", chat_id_str, status_baru])

# ----------------------------------------------------
# 4. FUNGSI AMBIL LIST HD YANG ONLINE
# ----------------------------------------------------
def get_hd_online_list():
    all_rows = sheet_hd.get_all_values()
    hd_online = []
    for row in all_rows[1:]:
        if len(row) >= 4 and row[3].strip().lower() == "online":
            hd_online.append({"name": row[0], "chat_id": row[2]})
    return hd_online

# ----------------------------------------------------
# FUNGSI BARU: CARI HD DENGAN TIKET PALING SEDIKIT (ROUND ROBIN / BEBAN MERATA)
# ----------------------------------------------------
def get_best_hd_to_assign():
    hd_online_list = get_hd_online_list()
    if not hd_online_list:
        return None # Kalau gak ada HD yang online sama sekali

    # Ambil data tiket dari Sheet1 untuk dihitung
    all_tickets = sheet_tiket.get_all_values()
    
    # Bikin catatan beban masing-masing HD online (awalnya 0 semua)
    # Contoh: {"Eza": 0, "Margo": 0}
    beban_hd = {hd["name"]: 0 for hd in hd_online_list}
    
    # Hitung tiket yang masih "BELUM SELESAI" di Sheet1
    for row in all_tickets[1:]: 
        if len(row) >= 17:
            status = str(row[15]).strip().upper() # Kolom P (Status)
            hd_name = str(row[16]).strip()        # Kolom Q (Nama HD)
            
            # Kalau tiketnya BELUM SELESAI dan nama HD-nya ada di daftar yang lagi online
            if status == "BELUM SELESAI" and hd_name in beban_hd:
                beban_hd[hd_name] += 1
                
    # Cari Nama HD yang jumlah bebannya paling KECIL (sedikit)
    hd_terpilih_name = min(beban_hd, key=beban_hd.get)
    
    # Ambil detail lengkap (nama & chat_id) si HD terpilih itu
    for hd in hd_online_list:
        if hd["name"] == hd_terpilih_name:
            return hd
            
    return None

# ----------------------------------------------------
# 5. FUNGSI PARSING LAPORAN
# ----------------------------------------------------
def parse_field(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "-"

def parse_pesan_mas_margo(text):
    first_line = text.split("\n")[0].strip().lower()
    jenis_req = "Troubleshoot"
    if "mandeg" in first_line:
        jenis_req = "Mandeg"
    elif "fallout" in first_line:
        jenis_req = "Fallout"

    return {
        "jenis": jenis_req,
        "no_order": parse_field(r"(?:No\s*Order|Order)\s*:\s*([^\n]+)", text),
        "sto": parse_field(r"STO\s*:\s*([^\n]+)", text),
        "no_internet": parse_field(r"(?:No\s*Internet|Internet)\s*:\s*([^\n]+)", text),
        "sn_modem": parse_field(r"(?:SN\s*Modem|SN)\s*:\s*([^\n]+)", text),
        "odp": parse_field(r"ODP\s*:\s*([^\n]+)", text),
        "port": parse_field(r"PORT\s*:\s*([^\n]+)", text),
        "barcode": parse_field(r"Barcode\s*:\s*([^\n]+)", text),
        "id_valin": parse_field(r"(?:Id\s*Valin|ID\s*Valin)\s*:\s*([^\n]+)", text),
        "keterangan": parse_field(r"Keterangan\s*:\s*([^\n]+)", text),
        "wonum": parse_field(r"WONUM\s*:\s*([^\n]+)", text),
        "tiket_fallout": parse_field(r"(?:Tiket\s*Fallout|Fallout)\s*:\s*([^\n]+)", text)
    }

# ----------------------------------------------------
# TEMPLATE TAP-TO-COPY
# ----------------------------------------------------
TPL_TROUBLESHOOT = "<b>📋 TEMPLATE TROUBLESHOOT</b>\n<i>Tap teks di bawah untuk menyalin:</i>\n\n<code>/req troubleshoot\nNo Order:\nSTO:\nNo Internet:\nSN Modem:\nODP:\nPORT:\nBarcode:\nId Valin:\nKeterangan:</code>"
TPL_MANDEG = "<b>📋 TEMPLATE ORDER MANDEG</b>\n<i>Tap teks di bawah untuk menyalin:</i>\n\n<code>/req Mandeg\nNo Order:\nWONUM:\nSTO:\nNo Internet:</code>"
TPL_FALLOUT = "<b>📋 TEMPLATE FALLOUT</b>\n<i>Tap teks di bawah untuk menyalin:</i>\n\n<code>/req Fallout\nNo Order:\nSTO:\nTiket Fallout:\nNo Internet:\nSN Modem:\nODP:\nPORT:\nBarcode:\nId Valin:</code>"

# ----------------------------------------------------
# 6. LOGIKA UTAMA (POLLING)
# ----------------------------------------------------
last_update_id = 0

while True:
    try:
        url_get = f"https://api.telegram.org/bot{TOKEN_BOT}/getUpdates?offset={last_update_id + 1}&timeout=30"
        response = requests.get(url_get).json()

        if response.get("ok"):
            for result in response.get("result", []):
                last_update_id = result["update_id"]

                # A. KONDISI 1: TOMBOL INLINE DIKLIK
                if "callback_query" in result:
                    cb = result["callback_query"]
                    cb_data = cb["data"]
                    chat_id = cb["message"]["chat"]["id"]

                    if cb_data == "btn_troubleshoot":
                        send_reply(chat_id, TPL_TROUBLESHOOT)
                    elif cb_data == "btn_mandeg":
                        send_reply(chat_id, TPL_MANDEG)
                    elif cb_data == "btn_fallout":
                        send_reply(chat_id, TPL_FALLOUT)
                    continue

                # B. KONDISI 2: PESAN TEKS MASUK
                if "message" in result and "text" in result["message"]:
                    msg = result["message"]
                    chat_id = msg["chat"]["id"]
                    msg_id = msg["message_id"]
                    text = msg["text"].strip()
                    text = text.replace("@jalda12_bot", "").replace("@Jalda12_bot", "")
                    sender = msg.get("from", {}).get("first_name", "User")
                    username = msg.get("from", {}).get("username", "TanpaUsername")

                    # 3. PERINTAH UPDATE STATUS HD (/status)
                    if text.lower().startswith("/status"):
                        # ==========================================
                        # FITUR 1: BLOKIR DARI GRUP (HANYA BISA JAPRI/PM)
                        # ==========================================
                        if chat_id < 0:
                            # Chat ID grup Telegram selalu bernilai minus (-)
                            pesan_tolak = "⚠️ <b>Peringatan:</b>\nUbah status tidak bisa di grup. Silakan ubah status kamu lewat Chat Pribadi (Japri) ke bot ini ya!"
                            send_reply(chat_id, pesan_tolak, msg_id)
                            continue # Langsung stop, jangan diproses ke Sheet

                        parts = text.split(maxsplit=1)
                        if len(parts) >= 2:
                            new_status = parts[1].strip().upper()
                            if new_status in ["ONLINE", "OFFLINE", "BREAK"]:
                                
                                # ==========================================
                                # FITUR 2: UPDATE SHEET BIAR NAMA GAK DOBEL
                                # ==========================================
                                print(f"⏳ Mengupdate status {sender} menjadi {new_status}...")
                                
                                # Ambil semua nama HD dari Kolom A di tab Data_HD
                                all_hd_names = sheet_hd.col_values(1)
                                
                                found_row = -1
                                for idx, name in enumerate(all_hd_names):
                                    if name.strip() == sender:
                                        found_row = idx + 1
                                        break
                                
                                waktu_update = time.strftime("%Y-%m-%d %H:%M:%S")

                                if found_row != -1:
                                    # JIKA NAMA UDAH ADA -> UPDATE BARIS LAMA
                                    # Asumsi: Kolom B = Status, Kolom C = Chat ID, Kolom D = Waktu Update
                                    sheet_hd.update_cell(found_row, 2, new_status)
                                    sheet_hd.update_cell(found_row, 3, str(chat_id))
                                    # Jika kamu pakai kolom waktu update, buka pagar di bawah ini:
                                    # sheet_hd.update_cell(found_row, 4, waktu_update) 
                                else:
                                    # JIKA NAMA BELUM ADA -> BIKIN BARIS BARU
                                    sheet_hd.append_row([sender, new_status, str(chat_id)])
                                    
                                send_reply(chat_id, f"✅ Status kamu berhasil diubah menjadi: <b>{new_status}</b>", msg_id)
                                print(f"👤 Status {sender} di-update ke {new_status}")
                                
                            else:
                                send_reply(chat_id, "⚠️ Status tidak valid! Pilih: ONLINE, OFFLINE, atau BREAK.", msg_id)
                        else:
                            send_reply(chat_id, "⚠️ Format salah! Ketik: <code>/status [online/offline/break]</code>", msg_id)
                        continue
                    
                        parts = text.split()
                        if len(parts) > 1:
                            st = parts[1].upper()
                            if st in ["ONLINE", "BREAK", "OFFLINE"]:
                                update_status_hd(sender, username, chat_id, st)
                                send_reply(chat_id, f"🟢 <b>Status HD Berhasil Diperbarui:</b> {st}", msg_id)
                                print(f"👤 HD {sender} mengubah status jadi {st}")
                            else:
                                send_reply(chat_id, "⚠️ Pilihan status salah! Gunakan: <code>/status online</code>, <code>/status break</code>, atau <code>/status offline</code>", msg_id)
                        else:
                            send_reply(chat_id, "⚠️ Format salah! Gunakan: <code>/status online</code>, <code>/status break</code>, atau <code>/status offline</code>", msg_id)
                        continue

                    # 2. PERINTAH HD MENYELESAIKAN TIKET (DENGAN ROUTING BALIK KE GRUB TEKNISI)
                    if text.lower().startswith("/done"):
                        parts = text.split(maxsplit=2)
                        if len(parts) >= 3:
                            no_order_target = parts[1].strip()
                            ket_hd = parts[2].strip()

                            print(f"⏳ Memproses No Order: {no_order_target}...")

# Ambil data Kolom E (No Order) & Data lengkap dari Sheet
                            all_rows = sheet_tiket.get_all_values()
                            col_orders = [row[4].strip() if len(row) > 4 else "" for row in all_rows]
                            
                            found_rows = []
                            teknisi_username = "Teknisi"
                            asal_chat_id = None
                            asal_msg_id = None
                            
                            for idx, val in enumerate(col_orders):
                                if val == no_order_target:
                                    found_rows.append(idx + 1)
                                    if len(all_rows[idx]) > 2:
                                        teknisi_username = all_rows[idx][2].strip()
                                    if len(all_rows[idx]) > 17:
                                        asal_chat_id = all_rows[idx][17].strip() # Kolom R
                                    if len(all_rows[idx]) > 18:
                                        asal_msg_id = all_rows[idx][18].strip()  # Kolom S

                            if len(found_rows) > 0:
                                for row_idx in found_rows:
                                    sheet_tiket.update_cell(row_idx, 16, "SELESAI")
                                    sheet_tiket.update_cell(row_idx, 17, sender)

                                # Balasan ke HD
                                send_reply(chat_id, f"✅ <b>Tiket No Order {no_order_target} Berhasil Di-close!</b>\nNotifikasi telah dikirim balik ke Teknisi.", msg_id)
                                
                                # NOTIFIKASI BALIK (DENGAN FITUR REPLY KE PESAN ASAL)
                                if asal_chat_id:
                                    notif_ke_teknisi = (
                                        f"🔔 <b>UPDATE TIKET SELESAI</b> 🔔\n\n"
                                        f"Halo {teknisi_username}, laporan kamu telah diselesaikan!\n\n"
                                        f"🔢 <b>No Order:</b> {no_order_target}\n"
                                        f"👨‍💻 <b>Dikerjakan Oleh HD:</b> {sender}\n"
                                        f"📝 <b>Keterangan Hasil:</b> <i>{ket_hd}</i>\n\n"
                                        f"<i>Terima kasih.</i>"
                                    )
                                    # Gunakan send_reply dengan 3 parameter (chat_id asal, teks, message_id asal)
                                    send_reply(asal_chat_id, notif_ke_teknisi, asal_msg_id)
                            else:
                                send_reply(chat_id, f"❌ No Order <b>{no_order_target}</b> tidak ditemukan di Google Sheet!", msg_id)
                        else:
                            send_reply(chat_id, "⚠️ Format salah! Gunakan: <code>/done [No Order] [Keterangan]</code>", msg_id)
                        continue
                    
                        parts = text.split(maxsplit=2)
                        if len(parts) >= 3:
                            no_order_target = parts[1].strip()
                            ket_hd = parts[2].strip()

                            print(f"⏳ Memproses No Order: {no_order_target}...")

                            col_orders = [str(x).strip() for x in sheet_tiket.col_values(5)]
                            col_users = sheet_tiket.col_values(3) # Kolom C: Username Teknisi

                            found_rows = []
                            teknisi_username = "Teknisi"
                            
                            for idx, val in enumerate(col_orders):
                                if val == no_order_target:
                                    found_rows.append(idx + 1)
                                    # Simpan username teknisi dari baris yang ditemukan
                                    if len(col_users) > idx:
                                        teknisi_username = str(col_users[idx]).strip()

                            if len(found_rows) > 0:
                                for row_idx in found_rows:
                                    sheet_tiket.update_cell(row_idx, 16, "SELESAI") 
                                    sheet_tiket.update_cell(row_idx, 17, sender)    

                                # 1. Balas ke HD (Konfirmasi berhasil close)
                                send_reply(chat_id, f"✅ <b>Tiket No Order {no_order_target} Berhasil Di-close!</b>", msg_id)
                                
                                # 2. NOTIFIKASI BALIK KE GRUP/TEKNISI (Wajib sesuai spek Mas Margo)
                                # Catatan: Jika bot ada di dalam 1 grup bersama teknisi & HD, chat_id ini akan menembak ke grup tersebut.
                                notif_ke_teknisi = (
                                    f"🔔 <b>UPDATE TIKET SELESAI</b> 🔔\n\n"
                                    f"Halo {teknisi_username}, laporan kamu telah diselesaikan!\n\n"
                                    f"🔢 <b>No Order:</b> {no_order_target}\n"
                                    f"👨‍💻 <b>Dikerjakan Oleh HD:</b> {sender}\n"
                                    f"📝 <b>Keterangan Hasil:</b> <i>{ket_hd}</i>\n\n"
                                    f"<i>Terima kasih.</i>"
                                )
                                # Mengirim pesan ke grup/chat yang sama tempat HD membalas /done
                                send_reply(chat_id, notif_ke_teknisi)
                                
                                print(f"🎉 Order {no_order_target} ditutup dan notifikasi terkirim!")
                            else:
                                send_reply(chat_id, f"❌ No Order <b>{no_order_target}</b> tidak ditemukan di Google Sheet!", msg_id)
                        else:
                            send_reply(chat_id, "⚠️ Format salah! Gunakan: <code>/done [No Order] [Keterangan]</code>", msg_id)
                        continue
                    
                        parts = text.split(maxsplit=2)
                        if len(parts) >= 3:
                            no_order_target = parts[1].strip()
                            ket_hd = parts[2].strip()

                            print(f"⏳ Memproses No Order: {no_order_target}...")

                            # 1. Ambil seluruh No Order di Kolom E & bersihkan spasi
                            col_orders = [str(x).strip() for x in sheet_tiket.col_values(5)]

                            # 2. Kumpulkan SEMUA baris yang punya No Order sama
                            found_rows = []
                            for idx, val in enumerate(col_orders):
                                if val == no_order_target:
                                    found_rows.append(idx + 1) # idx + 1 karena baris di Sheet mulai dari 1

                            # 3. Jika ketemu, update SEMUA baris tersebut
                            if len(found_rows) > 0:
                                for row_idx in found_rows:
                                    sheet_tiket.update_cell(row_idx, 16, "SELESAI") # Kolom P (Status)
                                    sheet_tiket.update_cell(row_idx, 17, sender)    # Kolom Q (HD Officer)

                                send_reply(chat_id, f"✅ <b>Tiket No Order {no_order_target} Berhasil Di-close!</b>\n<i>(Total {len(found_rows)} laporan duplikat otomatis diselesaikan)</i>\n\n📝 <b>Ket HD:</b> {ket_hd}", msg_id)
                                print(f"🎉 Order {no_order_target} diselesaikan pada baris: {found_rows}")
                            else:
                                send_reply(chat_id, f"❌ No Order <b>{no_order_target}</b> tidak ditemukan di Google Sheet!", msg_id)
                        else:
                            send_reply(chat_id, "⚠️ Format salah! Gunakan: <code>/done [No Order] [Keterangan]</code>\nContoh: <code>/done 1728394051 Sudah di-reset dari sentral</code>", msg_id)
                        continue
                    
                    # 3. PERINTAH MENU UTAMA
                    if text.lower() in ["/start", "/help", "/req", "/mandeg", "/troubleshoot", "/fallout"]:
                        send_menu_tombol(chat_id, msg_id)
                        continue

                    # 4. PENDAFTARAN REQUEST BARU DARI TEKNISI (/req)
                    if text.lower().startswith("/req"):
                        data = parse_pesan_mas_margo(text)

                        if data["no_order"] == "-" or data["sto"] == "-":
                            send_reply(chat_id, "❌ <b>Format Belum Lengkap!</b>\nMohon pastikan <b>No Order</b> dan <b>STO</b> diisi.\nKetik /help untuk ambil tombol template.", msg_id)
                            continue

                        # ====================================================
                        # FITUR BARU: CEGAH DUPLIKAT TIKET (ANTI-SPAM)
                        # ====================================================
                        print(f"🔍 Mengecek apakah No Order {data['no_order']} duplikat...")
                        col_orders = sheet_tiket.col_values(5)  # Ambil semua No Order (Kolom E)
                        col_status = sheet_tiket.col_values(16) # Ambil semua Status (Kolom P)
                        
                        is_duplicate = False
                        for idx, order_val in enumerate(col_orders):
                            # Jika No Order sama persis
                            if str(order_val).strip() == data["no_order"]:
                                # Cek apakah statusnya masih BELUM SELESAI
                                if len(col_status) > idx and str(col_status[idx]).strip() == "BELUM SELESAI":
                                    is_duplicate = True
                                    break
                        
                        if is_duplicate:
                            pesan_tolak = f"⚠️ <b>TIKET DITOLAK (DUPLIKAT)</b>\n\nNo Order <b>{data['no_order']}</b> sudah terdaftar di sistem dan saat ini masih <b>BELUM SELESAI</b> (Sedang diproses HD).\n\n<i>Mohon tunggu HD menyelesaikan tiket tersebut sebelum mengirim ulang.</i>"
                            send_reply(chat_id, pesan_tolak, msg_id)
                            print(f"🚫 Tiket {data['no_order']} ditolak karena duplikat!")
                            continue # Langsung stop/kembali ke awal, jangan di-append ke sheet
                        # ====================================================

                        waktu_sekarang = time.strftime("%Y-%m-%d %H:%M:%S")

                        # ====================================================
                        # SISTEM ROUND ROBIN / BEBAN MERATA
                        # ====================================================
                        hd_terpilih = get_best_hd_to_assign()
                        
                        hd_assigned = "Belum Diassign"
                        if hd_terpilih:
                            hd_assigned = hd_terpilih["name"]

                        row_data = [
                            waktu_sekarang,
                            sender,
                            f"@{username}",
                            data["jenis"],
                            data["no_order"],
                            data["sto"],
                            data["no_internet"],
                            data["sn_modem"],
                            data["odp"],
                            data["port"],
                            data["barcode"],
                            data["id_valin"],
                            data["wonum"],
                            data["tiket_fallout"],
                            data["keterangan"],
                            "BELUM SELESAI", # Kolom P
                            hd_assigned,     # Kolom Q (Hanya 1 HD terpilih)
                            str(chat_id),    # Kolom R (Chat ID Asal)
                            str(msg_id)      # Kolom S (Message ID Asal)
                        ]

                        sheet_tiket.append_row(row_data)

                        # Auto Format Center & Unbold
                        last_row = len(sheet_tiket.get_all_values())
                        sheet_tiket.format(f"A{last_row}:S{last_row}", {
                            "textFormat": {"bold": False},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        })

                        # Teruskan pesan tiket HANYA ke HD YANG TERPILIH
                        if hd_terpilih:
                            notif_hd = (
                                f"🔔 <b>TIKET BARU UNTUK KAMU!</b>\n"
                                f"<i>(Sistem memilihmu karena antrean tiketmu paling sedikit)</i>\n\n"
                                f"👤 <b>Teknisi:</b> {sender} (@{username})\n"
                                f"📌 <b>Jenis:</b> {data['jenis']}\n"
                                f"🔢 <b>No Order:</b> {data['no_order']}\n"
                                f"🏢 <b>STO:</b> {data['sto']}\n"
                                f"🌐 <b>No Internet:</b> {data['no_internet']}\n"
                                f"📝 <b>Keterangan:</b> {data['keterangan']}\n\n"
                                f"<i>Ketik <code>/done {data['no_order']} [Keterangan]</code> jika sudah selesai!</i>"
                            )
                            send_reply(hd_terpilih["chat_id"], notif_hd)
                            print(f"🎯 Tiket {data['no_order']} di-assign ke {hd_terpilih['name']}")

                        # Balasan ke Teknisi di Grup
                        balasan = (
                            f"✅ <b>REQUEST {data['jenis'].upper()} BERHASIL DICATAT</b>\n\n"
                            f"📌 <b>No Order:</b> {data['no_order']}\n"
                            f"🏢 <b>STO:</b> {data['sto']}\n"
                            f"👨‍💻 <b>HD Officer:</b> {hd_assigned}\n"
                            f"⏳ <b>Status Tiket:</b> BELUM SELESAI\n\n"
                            f"<i>Mohon ditunggu, tiket sedang dikerjakan.</i>"
                        )
                        send_reply(chat_id, balasan, msg_id)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(2)