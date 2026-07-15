import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon import functions

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

# ================= BACKEND LOGIC =================
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
        config = await client(functions.help.GetConfig())
        config_dict = config.to_dict()
        await client.disconnect()
        return {"config": json.loads(json.dumps(config_dict, default=str))}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================= UI DATABASES & GRAPHICS =================
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Config Leaker</title>
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
            
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
            body { background-color: var(--bg-color); color: var(--text-color); display: flex; flex-direction: column; min-height: 100vh; }
            
            /* App Bar Android Style */
            .app-bar { background-color: var(--header-color); padding: 16px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
            .app-bar h1 { font-size: 20px; font-weight: 500; }
            
            /* Android Tabs */
            .tabs { display: flex; background-color: var(--header-color); border-bottom: 1px solid var(--input-border); }
            .tab-btn { flex: 1; background: none; border: none; color: var(--text-secondary); padding: 14px 0; font-size: 13px; font-weight: 500; cursor: pointer; text-transform: uppercase; position: relative; text-align: center; }
            .tab-btn.active { color: var(--accent-color); }
            .tab-btn.active::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background-color: var(--accent-color); }
            
            .content { padding: 16px; flex: 1; max-width: 600px; width: 100%; margin: 0 auto; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            
            /* Telegram Channel Feed Styles */
            .channel-header { display: flex; align-items: center; margin-bottom: 16px; padding: 8px 0; }
            .channel-avatar { width: 40px; height: 40px; background-color: #2b5278; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; color: white; margin-right: 12px; }
            .channel-meta h3 { font-size: 15px; font-weight: 600; }
            .channel-meta p { font-size: 12px; color: var(--text-secondary); }
            
            .tg-message { background-color: var(--chat-bg); border-radius: 12px; padding: 12px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.2); position: relative; }
            .tg-message-text { font-size: 14px; line-height: 1.4; margin-bottom: 8px; white-space: pre-line; }
            
            /* Code Diff Engine Graphic */
            .diff-container { background-color: #111c27; border-radius: 8px; border: 1px solid var(--input-border); overflow: hidden; margin: 10px 0; font-family: monospace; font-size: 12px; }
            .diff-file-header { background-color: #1c2a38; padding: 6px 10px; color: var(--text-secondary); border-bottom: 1px solid var(--input-border); font-size: 11px; }
            .diff-line { padding: 2px 10px; display: flex; white-space: pre-wrap; word-break: break-all; }
            .diff-line.del { background-color: var(--diff-del-bg); color: var(--diff-del-text); }
            .diff-line.add { background-color: var(--diff-add-bg); color: var(--diff-add-text); }
            
            .tg-message-footer { display: flex; justify-content: flex-end; align-items: center; font-size: 11px; color: var(--text-secondary); margin-top: 4px; }
            .tg-message-footer span { margin-left: 8px; display: flex; align-items: center; gap: 3px; }

            /* Forms Stylings */
            .input-group { margin-bottom: 16px; }
            .input-group label { display: block; color: var(--accent-color); font-size: 12px; font-weight: 500; margin-bottom: 6px; text-transform: uppercase; }
            .input-group input, .input-group textarea { width: 100%; background-color: var(--input-bg); border: 1px solid var(--input-border); border-radius: 8px; padding: 12px; color: var(--text-color); font-size: 15px; outline: none; }
            .input-group input:focus, .input-group textarea:focus { border-color: var(--accent-color); }
            .btn { width: 100%; background-color: var(--accent-color); color: var(--text-color); border: none; border-radius: 8px; padding: 14px; font-size: 15px; font-weight: 500; cursor: pointer; }
            .btn:disabled { background-color: var(--input-border); color: var(--text-secondary); }
            .status-msg { margin-top: 12px; padding: 10px; border-radius: 6px; font-size: 13px; display: none; }
            .status-msg.error { background-color: rgba(236, 59, 59, 0.1); color: var(--diff-del-text); display: block; }
            .status-msg.success { background-color: rgba(76, 199, 100, 0.1); color: var(--diff-add-text); display: block; }
            pre { background-color: #111c27; padding: 10px; border-radius: 8px; overflow-x: auto; font-size: 12px; border: 1px solid var(--input-border); }
        </style>
    </head>
    <body>

        <div class="app-bar">
            <h1>Telegram Config Leaker</h1>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('leaks-tab', this)">📢 Leaks Feed</button>
            <button class="tab-btn" onclick="switchTab('session-tab', this)">🔑 Get Session</button>
            <button class="tab-btn" onclick="switchTab('config-tab', this)">🔍 Fetch Live</button>
        </div>

        <div class="content">
            <div id="leaks-tab" class="tab-content active">
                <div class="channel-header">
                    <div class="channel-avatar">TL</div>
                    <div class="channel-meta">
                        <h3>Telegram UI & Beta Leaks 👑</h3>
                        <p>138,420 subscribers • info fitur terbaru</p>
                    </div>
                </div>

                <div class="tg-message">
                    <div class="tg-message-text">
                        🔥 <b>[BOCORAN SERVER CONFIG]</b>
                        Telegram baru saja merubah parameter routing link utama di sisi server backend mereka. URL pendek t.me mulai dialihkan bertahap menggunakan struktur subdomain global baru.
                    </div>
                    <div class="diff-container">
                        <div class="diff-file-header">mtproto/prod/help.getConfig.json</div>
                        <div class="diff-line del">- "me_url_prefix": "https://t.me/"</div>
                        <div class="diff-line add">+ "me_url_prefix": "https://telegram.me/"</div>
                    </div>
                    <div class="tg-message-footer">
                        <span>👁️ 14.5K</span>
                        <span>16:19</span>
                    </div>
                </div>

                <div class="tg-message">
                    <div class="tg-message-text">
                        ⚡ <b>[BETA UPDATE]</b>
                        Pengujian internal menaikkan limitasi durasi edit pesan text dan batasan ukuran caption media file untuk pengguna dengan status Premium Plan.
                    </div>
                    <div class="diff-container">
                        <div class="diff-file-header">ui/config/limits.data</div>
                        <div class="diff-line">  "caption_length_limit_default": 1024,</div>
                        <div class="diff-line del">- "caption_length_limit_premium": 2048,</div>
                        <div class="diff-line add">+ "caption_length_limit_premium": 4096,</div>
                        <div class="diff-line del">- "edit_time_limit": 172800</div>
                        <div class="diff-line add">+ "edit_time_limit": 259200</div>
                    </div>
                    <div class="tg-message-footer">
                        <span>👁️ 21.2K</span>
                        <span>Kemarin</span>
                    </div>
                </div>
            </div>

            <div id="session-tab" class="tab-content">
                <div id="step-1">
                    <div class="input-group"><label>API ID</label><input type="number" id="api-id" placeholder="Contoh: 8586525"></div>
                    <div class="input-group"><label>API HASH</label><input type="password" id="api-hash" placeholder="Masukkan API Hash"></div>
                    <div class="input-group"><label>Nomor HP</label><input type="text" id="phone" placeholder="Contoh: +62812345678"></div>
                    <button class="btn" id="btn-send-otp" onclick="sendOTP()">Minta OTP Telegram</button>
                </div>
                <div id="step-2" style="display: none;">
                    <div class="input-group"><label>Kode Verifikasi (OTP)</label><input type="text" id="otp-code" placeholder="Masukkan kode chat"></div>
                    <div class="input-group"><label>Password 2FA</label><input type="password" id="password-2fa" placeholder="Kosongkan jika tidak ada"></div>
                    <button class="btn" id="btn-verify" onclick="verifyOTP()">Verifikasi Akun</button>
                </div>
                <div id="session-status" class="status-msg"></div>
                <div id="session-result" class="diff-container" style="display:none; padding:12px;">
                    <code style="color:var(--accent-color); word-break:break-all;"></code>
                </div>
            </div>

            <div id="config-tab" class="tab-content">
                <div class="input-group"><label>String Session Kamu</label><textarea id="string-session-input" rows="4" placeholder="Masukkan session hasil generator"></textarea></div>
                <button class="btn" id="btn-get-config" onclick="fetchConfig()">Ambil help.getConfig Asli</button>
                <div class="config-status status-msg" id="config-status"></div>
                <div id="config-result" style="display:none; margin-top:15px;">
                    <pre><code id="json-output" style="color:#88ff88;"></code></pre>
                </div>
            </div>
        </div>

        <script>
            let loginData = { temp_session: "", phone_code_hash: "" };
            
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
                const statusDiv = document.getElementById('session-status');
                if(!apiId || !apiHash || !phone) { statusDiv.className = "status-msg error"; statusDiv.innerText = "Isi data dengan lengkap bray!"; return; }
                statusDiv.className = "status-msg success"; statusDiv.innerText = "Menembak server Telegram untuk OTP...";
                try {
                    const res = await fetch('/api/send_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, phone: phone }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal kirim OTP");
                    loginData.temp_session = data.temp_session;
                    loginData.phone_code_hash = data.phone_code_hash;
                    statusDiv.innerText = "Sukses! Cek kode OTP di aplikasi Telegram kamu.";
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
                const statusDiv = document.getElementById('session-status');
                try {
                    const res = await fetch('/api/verify_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, phone: phone, otp: otp, password: password, temp_session: loginData.temp_session, phone_code_hash: loginData.phone_code_hash }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Verifikasi OTP Gagal");
                    statusDiv.innerText = "Selamat! Session berhasil digenerate.";
                    const resBox = document.getElementById('session-result');
                    resBox.querySelector('code').innerText = data.session;
                    resBox.style.display = 'block';
                    document.getElementById('step-2').style.display = 'none';
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }
            
            async function fetchConfig() {
                const apiId = document.getElementById('api-id').value || 8586525;
                const apiHash = document.getElementById('api-hash').value || "b502b18d61ecf433c5fc8534f9370869";
                const session = document.getElementById('string-session-input').value;
                const statusDiv = document.getElementById('config-status');
                if(!session) { statusDiv.className = "status-msg error"; statusDiv.innerText = "Masukkan session dulu!"; return; }
                statusDiv.className = "status-msg success"; statusDiv.innerText = "Mengunduh config server aktif...";
                try {
                    const res = await fetch('/api/get_config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, session: session }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal mengambil data");
                    statusDiv.innerText = "Koneksi sukses! Data dimuat di bawah.";
                    document.getElementById('json-output').innerText = JSON.stringify(data.config, null, 2);
                    document.getElementById('config-result').style.display = 'block';
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }
        </script>
    </body>
    </html>
    """
