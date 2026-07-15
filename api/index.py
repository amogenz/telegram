import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.help import GetConfigRequest # FIX ERROR DISINI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SendOTPRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str

class VerifyOTPRequest(BaseModel):
    api_id: int
    api_hash: str
    phone: str
    otp: str
    password: str = ""
    temp_session: str
    phone_code_hash: str

class GetConfigRequest(BaseModel):
    api_id: int
    api_hash: str
    session: str

# ================= BACKEND CORE =================

@app.post("/api/send_otp")
async def send_otp(req: SendOTPRequest):
    try:
        client = TelegramClient(StringSession(), req.api_id, req.api_hash)
        await client.connect()
        send_code = await client.send_code_request(req.phone)
        temp_session = client.session.save()
        phone_code_hash = send_code.phone_code_hash
        await client.disconnect()
        return {"temp_session": temp_session, "phone_code_hash": phone_code_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/verify_otp")
async def verify_otp(req: VerifyOTPRequest):
    try:
        client = TelegramClient(StringSession(req.temp_session), req.api_id, req.api_hash)
        await client.connect()
        if req.password:
            await client.sign_in(req.phone, req.otp, password=req.password, phone_code_hash=req.phone_code_hash)
        else:
            await client.sign_in(req.phone, req.otp, phone_code_hash=req.phone_code_hash)
        final_session = client.session.save()
        await client.disconnect()
        return {"session": final_session}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/get_config")
async def get_config(req: GetConfigRequest):
    try:
        client = TelegramClient(StringSession(req.session), req.api_id, req.api_hash)
        await client.connect()
        # Menggunakan GetConfigRequest() yang benar sesuai dokumentasi Telethon terbaru
        config = await client(GetConfigRequest())
        config_dict = config.to_dict()
        await client.disconnect()
        return {"config": json.loads(json.dumps(config_dict, default=str))}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================= AUTOMATED FRONTEND INTERFACE =================

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Live Leaker Portal</title>
        <style>
            :root {
                --bg-color: #0e1621;
                --header-color: #17212b;
                --accent-color: #5288c1;
                --text-color: #ffffff;
                --text-secondary: #7f91a4;
                --input-bg: #17212b;
                --input-border: #24313f;
                --chat-bg: #182533;
                --diff-del-bg: #492c2c;
                --diff-add-bg: #32493b;
                --diff-del-text: #ff8888;
                --diff-add-text: #88ff88;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, sans-serif; }
            body { background-color: var(--bg-color); color: var(--text-color); display: flex; flex-direction: column; min-height: 100vh; }
            .app-bar { background-color: var(--header-color); padding: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
            .app-bar h1 { font-size: 18px; font-weight: 500; }
            .logout-btn { background: none; border: 1px solid var(--error-color); color: #ec3b3b; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; display: none; }
            
            .tabs { display: flex; background-color: var(--header-color); border-bottom: 1px solid var(--input-border); }
            .tab-btn { flex: 1; background: none; border: none; color: var(--text-secondary); padding: 14px 0; font-size: 13px; font-weight: 500; cursor: pointer; text-transform: uppercase; position: relative; text-align: center; }
            .tab-btn.active { color: var(--accent-color); }
            .tab-btn.active::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background-color: var(--accent-color); }
            
            .content { padding: 16px; flex: 1; max-width: 600px; width: 100%; margin: 0 auto; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            
            /* Telegram Feed Card */
            .channel-header { display: flex; align-items: center; margin-bottom: 16px; padding: 8px 0; }
            .channel-avatar { width: 42px; height: 42px; background: linear-gradient(135deg, #5288c1, #2b5278); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; color: white; margin-right: 12px; }
            .channel-meta h3 { font-size: 15px; font-weight: 600; }
            .channel-meta p { font-size: 12px; color: var(--text-secondary); }
            
            .tg-message { background-color: var(--chat-bg); border-radius: 12px; padding: 14px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.2); }
            .tg-message-text { font-size: 14px; line-height: 1.4; margin-bottom: 8px; }
            
            /* Git Diff Graphic Box */
            .diff-container { background-color: #111c27; border-radius: 8px; border: 1px solid var(--input-border); overflow: hidden; margin: 10px 0; font-family: monospace; font-size: 12px; }
            .diff-file-header { background-color: #1c2a38; padding: 6px 10px; color: var(--text-secondary); border-bottom: 1px solid var(--input-border); font-size: 11px; }
            .diff-line { padding: 3px 10px; display: flex; white-space: pre-wrap; word-break: break-all; }
            .diff-line.del { background-color: var(--diff-del-bg); color: var(--diff-del-text); }
            .diff-line.add { background-color: var(--diff-add-bg); color: var(--diff-add-text); }
            .diff-line.info { color: var(--accent-color); background-color: rgba(82,136,193,0.05); }
            
            .tg-message-footer { display: flex; justify-content: flex-end; align-items: center; font-size: 11px; color: var(--text-secondary); margin-top: 6px; }
            
            /* Form Fields */
            .input-group { margin-bottom: 16px; }
            .input-group label { display: block; color: var(--accent-color); font-size: 12px; font-weight: 500; margin-bottom: 6px; }
            .input-group input { width: 100%; background-color: var(--input-bg); border: 1px solid var(--input-border); border-radius: 8px; padding: 12px; color: var(--text-color); font-size: 15px; outline: none; }
            .input-group input:focus { border-color: var(--accent-color); }
            .btn { width: 100%; background-color: var(--accent-color); color: var(--text-color); border: none; border-radius: 8px; padding: 14px; font-size: 15px; font-weight: 500; cursor: pointer; }
            .status-msg { margin-top: 12px; padding: 10px; border-radius: 6px; font-size: 13px; display: none; }
            .status-msg.error { background-color: rgba(236, 59, 59, 0.1); color: var(--diff-del-text); display: block; }
            .status-msg.success { background-color: rgba(76, 199, 100, 0.1); color: var(--diff-add-text); display: block; }
            
            .loading-shimmer { color: var(--text-secondary); text-align: center; padding: 30px 0; font-size: 14px; }
        </style>
    </head>
    <body>

        <div class="app-bar">
            <h1>Telegram Live Leaker</h1>
            <button id="logout-btn" class="logout-btn" onclick="logOut()">Log Out</button>
        </div>

        <div class="tabs">
            <button class="tab-btn active" id="nav-leaks" onclick="switchTab('leaks-tab', this)">📢 Leaks Feed</button>
            <button class="tab-btn" id="nav-auth" onclick="switchTab('auth-tab', this)">🔑 Account</button>
        </div>

        <div class="content">
            <div id="leaks-tab" class="tab-content active">
                <div class="channel-header">
                    <div class="channel-avatar">⚡</div>
                    <div class="channel-meta">
                        <h3>Live MTProto Monitor Bot</h3>
                        <p id="channel-status">Memeriksa status enkripsi server...</p>
                    </div>
                </div>
                
                <div id="feed-container">
                    <div class="loading-shimmer">Silahkan hubungkan akun Telegram kamu di tab "Account" terlebih dahulu untuk mengaktifkan pemantauan otomatis...</div>
                </div>
            </div>

            <div id="auth-tab" class="tab-content">
                <div id="login-box">
                    <div id="step-1">
                        <div class="input-group"><label>API ID</label><input type="number" id="api-id" placeholder="Contoh: 8586525"></div>
                        <div class="input-group"><label>API HASH</label><input type="password" id="api-hash" placeholder="Masukkan API Hash"></div>
                        <div class="input-group"><label>NOMOR HP</label><input type="text" id="phone" placeholder="Contoh: +62812345678"></div>
                        <button class="btn" onclick="sendOTP()">Kirim Kode OTP Ke Aplikasi</button>
                    </div>
                    <div id="step-2" style="display: none;">
                        <div class="input-group"><label>KODE VERIFIKASI CHAT</label><input type="text" id="otp-code" placeholder="Masukkan 5 digit kode"></div>
                        <div class="input-group"><label>PASSWORD 2FA (BILA ADA)</label><input type="password" id="password-2fa" placeholder="Kosongkan jika tidak ada"></div>
                        <button class="btn" onclick="verifyOTP()">Otorisasi Web Tracker</button>
                    </div>
                </div>

                <div id="profile-box" style="display: none; text-align: center; padding: 20px 0;">
                    <div style="font-size: 50px; margin-bottom: 10px;">✅</div>
                    <h3>Server Monitor Aktif</h3>
                    <p style="color: var(--text-secondary); margin-top: 6px; font-size: 14px;">Akun terhubung ke API ID: <span id="connected-id" style="color:var(--accent-color);"></span></p>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-top: 4px;">Setiap kali kamu membuka web ini, sistem otomatis memantau tanpa perlu login lagi.</p>
                </div>

                <div id="auth-status" class="status-msg"></div>
            </div>
        </div>

        <script>
            let loginData = { temp_session: "", phone_code_hash: "" };

            window.onload = function() {
                checkSession();
            };

            function checkSession() {
                const session = localStorage.getItem('tg_session');
                const apiId = localStorage.getItem('tg_api_id');
                
                if (session && apiId) {
                    document.getElementById('login-box').style.display = 'none';
                    document.getElementById('profile-box').style.display = 'block';
                    document.getElementById('connected-id').innerText = apiId;
                    document.getElementById('logout-btn').style.style.display = 'block';
                    document.getElementById('channel-status').innerText = "Sudah Sinkron • Memantau Server Telegram Aktif";
                    
                    // Eksekusi pemantauan otomatis secara ghaib
                    runAutoTracker(session, apiId, localStorage.getItem('tg_api_hash'));
                } else {
                    document.getElementById('login-box').style.display = 'block';
                    document.getElementById('profile-box').style.display = 'none';
                    document.getElementById('logout-btn').style.style.display = 'none';
                    switchTab('auth-tab', document.getElementById('nav-auth'));
                }
            }

            function switchTab(tabId, element) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                element.classList.add('active');
            }

            async function sendOTP() {
                const apiId = document.getElementById('api-id').value;
                const apiHash = document.getElementById('api-hash').value;
                const phone = document.getElementById('phone').value;
                const statusDiv = document.getElementById('auth-status');
                
                if(!apiId || !apiHash || !phone) { statusDiv.className = "status-msg error"; statusDiv.innerText = "Lengkapi form bray!"; return; }
                statusDiv.className = "status-msg success"; statusDiv.innerText = "Mengirim OTP...";

                try {
                    const res = await fetch('/api/send_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, phone: phone }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal kirim OTP");
                    
                    loginData.temp_session = data.temp_session;
                    loginData.phone_code_hash = data.phone_code_hash;
                    statusDiv.innerText = "OTP Berhasil Dikirim! Cek chat Telegram-mu.";
                    document.getElementById('step-1').style.display = 'none';
                    document.getElementById('step-2').style.display = 'block';
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }

            async function verifyOTP() {
                const apiId = document.getElementById('api-id').value;
                const apiHash = document.getElementById('api-hash').value;
                const phone = document.getElementById('phone').value;
                const otp = document.getElementById('otp-code').value;
                const password = document.getElementById('password-2fa').value;
                const statusDiv = document.getElementById('auth-status');

                try {
                    const res = await fetch('/api/verify_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, phone: phone, otp: otp, password: password, temp_session: loginData.temp_session, phone_code_hash: loginData.phone_code_hash }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Otorisasi gagal");

                    // SIMPAN DATA LOGIN DI BROWSER BIAR GAK LOGIN LAGI
                    localStorage.setItem('tg_session', data.session);
                    localStorage.setItem('tg_api_id', apiId);
                    localStorage.setItem('tg_api_hash', apiHash);

                    statusDiv.innerText = "Berhasil Terhubung!";
                    checkSession();
                    switchTab('leaks-tab', document.getElementById('nav-leaks'));
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }

            async function runAutoTracker(session, apiId, apiHash) {
                const feed = document.getElementById('feed-container');
                try {
                    const res = await fetch('/api/get_config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, session: session }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error("Gagal mengambil update sistem.");

                    const newConfig = data.config;
                    const oldConfigStr = localStorage.getItem('tg_last_cached_config');
                    let oldConfig = oldConfigStr ? JSON.parse(oldConfigStr) : null;
                    
                    // Simpan data terbaru buat perbandingan kunjungan besok
                    localStorage.setItem('tg_last_cached_config', JSON.stringify(newConfig));

                    let htmlOutput = "";
                    let timeNow = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

                    // JIKA INI KUNJUNGAN PERTAMA KALI (INITIAL SYNC)
                    if (!oldConfig) {
                        htmlOutput = `
                            <div class="tg-message">
                                <div class="tg-message-text">👑 <b>[INITIAL SYNC SUKSES]</b><br>Koneksi aman terjalin. Menampilkan parameter UI sistem inti dari server Telegram saat ini:</div>
                                <div class="diff-container">
                                    <div class="diff-file-header">mtproto/current/help.getConfig.json</div>
                                    <div class="diff-line info">ℹ️ Maksimal Anggota Grup: ${newConfig.megagroup_size_max || 200000} orang</div>
                                    <div class="diff-line info">ℹ️ Maksimal Panjang Pesan: ${newConfig.message_length_max || 4096} karakter</div>
                                    <div class="diff-line info">ℹ️ Link Prefix Utama: ${newConfig.me_url_prefix || "https://t.me/"}</div>
                                    <div class="diff-line info">ℹ️ Limit File Uncompressed: ${newConfig.saved_gifs_limit || 200} item</div>
                                </div>
                                <div class="tg-message-footer"><span>👁️ 1</span><span>${timeNow}</span></div>
                            </div>
                        `;
                    } else {
                        // DETEKSI PERUBAHAN SECARA LIVE & OTOMATIS
                        let changesDetected = [];
                        for (let key in newConfig) {
                            if (JSON.stringify(oldConfig[key]) !== JSON.stringify(newConfig[key])) {
                                changesDetected.push({
                                    key: key,
                                    oldVal: oldConfig[key],
                                    newVal: newConfig[key]
                                });
                            }
                        }

                        if (changesDetected.length > 0) {
                            let diffLines = "";
                            changesDetected.forEach(c => {
                                diffLines += `<div class="diff-line del">- "${c.key}": ${JSON.stringify(c.oldVal)}</div>`;
                                diffLines += `<br>`;
                                diffLines += `<br>`;
                                diffLines += `<div class="diff-line add">+ "${c.key}": ${JSON.stringify(c.newVal)}</div>`;
                            });

                            htmlOutput = `
                                <div class="tg-message">
                                    <div class="tg-message-text">🔥 <b>[TERDETEKSI PERUBAHAN KODE SERVER]</b><br>Telegram diam-diam merubah variabel konfigurasi global berikut dari pusat data:</div>
                                    <div class="diff-container">
                                        <div class="diff-file-header">mtproto/patch/help.getConfig.json</div>
                                        ${diffLines}
                                    </div>
                                    <div class="tg-message-footer"><span>👁️ Live</span><span>${timeNow}</span></div>
                                </div>
                            `;
                        } else {
                            // JIKA TIDAK ADA YANG BERUBAH SEJAK KUNJUNGAN TERAKHIR
                            htmlOutput = `
                                <div class="tg-message">
                                    <div class="tg-message-text">🟢 <b>[SERVER STABIL]</b><br>Tidak ada pembaruan data atau potongan kode UI baru dari server Telegram sejak kunjungan terakhirmu bray. Semua masih sinkron secara normal.</div>
                                    <div class="tg-message-footer"><span>👁️ Terpantau</span><span>${timeNow}</span></div>
                                </div>
                            `;
                        }
                    }

                    feed.innerHTML = htmlOutput;

                } catch (err) {
                    feed.innerHTML = `<div class="status-msg error" style="display:block;">Gagal Sinkronisasi: ${err.message}. Coba re-login di tab Account.</div>`;
                }
            }

            function logOut() {
                localStorage.clear();
                alert("Sesi dihapus. Silahkan login kembali bray!");
                window.location.reload();
            }
        </script>
    </body>
    </html>
    """
