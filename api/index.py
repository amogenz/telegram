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

# ================= INTERFACE TAMPILAN (FRONTEND) =================

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Config Tracker</title>
        <style>
            :root {
                --bg-color: #0e1621;
                --header-color: #17212b;
                --accent-color: #5288c1;
                --text-color: #ffffff;
                --text-secondary: #7f91a4;
                --input-bg: #17212b;
                --input-border: #24313f;
                --btn-hover: #6096d2;
                --error-color: #ec3b3b;
                --success-color: #4cc764;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, sans-serif; }
            body { background-color: var(--bg-color); color: var(--text-color); display: flex; flex-direction: column; min-height: 100vh; }
            .app-bar { background-color: var(--header-color); padding: 16px; display: flex; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
            .app-bar h1 { font-size: 20px; font-weight: 500; margin-left: 10px; }
            .tabs { display: flex; background-color: var(--header-color); border-bottom: 1px solid var(--input-border); }
            .tab-btn { flex: 1; background: none; border: none; color: var(--text-secondary); padding: 14px 0; font-size: 14px; font-weight: 500; cursor: pointer; text-transform: uppercase; position: relative; }
            .tab-btn.active { color: var(--accent-color); }
            .tab-btn.active::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background-color: var(--accent-color); }
            .content { padding: 20px; flex: 1; max-width: 600px; width: 100%; margin: 0 auto; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .input-group { margin-bottom: 20px; }
            .input-group label { display: block; color: var(--accent-color); font-size: 13px; font-weight: 500; margin-bottom: 6px; }
            .input-group input, .input-group textarea { width: 100%; background-color: var(--input-bg); border: 1px solid var(--input-border); border-radius: 8px; padding: 12px 16px; color: var(--text-color); font-size: 16px; outline: none; }
            .input-group input:focus, .input-group textarea:focus { border-color: var(--accent-color); }
            .btn { width: 100%; background-color: var(--accent-color); color: var(--text-color); border: none; border-radius: 8px; padding: 14px; font-size: 16px; font-weight: 500; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
            .btn:disabled { background-color: var(--input-border); color: var(--text-secondary); cursor: not-allowed; }
            .status-msg { margin-top: 15px; padding: 12px; border-radius: 6px; font-size: 14px; display: none; }
            .status-msg.error { background-color: rgba(236, 59, 59, 0.1); color: var(--error-color); display: block; }
            .status-msg.success { background-color: rgba(76, 199, 100, 0.1); color: var(--success-color); display: block; }
            .result-box { margin-top: 20px; background-color: var(--header-color); border: 1px solid var(--input-border); border-radius: 8px; padding: 15px; display: none; }
            .result-box.active { display: block; }
            .result-box code { word-break: break-all; font-family: monospace; color: var(--success-color); user-select: all; }
            pre { background-color: #1c2733; padding: 12px; border-radius: 6px; overflow-x: auto; max-height: 400px; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="app-bar">
            <h1>Telegram Tracker</h1>
        </div>
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('session-tab', this)">Session Generator</button>
            <button class="tab-btn" onclick="switchTab('config-tab', this)">Config Viewer</button>
        </div>
        <div class="content">
            <div id="session-tab" class="tab-content active">
                <div id="step-1">
                    <div class="input-group"><label>API ID</label><input type="number" id="api-id" placeholder="Contoh: 8586525"></div>
                    <div class="input-group"><label>API HASH</label><input type="password" id="api-hash" placeholder="Masukkan API Hash"></div>
                    <div class="input-group"><label>NOMOR TELEPON</label><input type="text" id="phone" placeholder="Contoh: +62812345678"></div>
                    <button class="btn" id="btn-send-otp" onclick="sendOTP()">Kirim Kode OTP</button>
                </div>
                <div id="step-2" style="display: none;">
                    <div class="input-group"><label>KODE OTP</label><input type="text" id="otp-code" placeholder="Masukkan kode"></div>
                    <div class="input-group"><label>PASSWORD 2FA (Opsional)</label><input type="password" id="password-2fa" placeholder="Kosongkan jika tidak ada"></div>
                    <button class="btn" id="btn-verify" onclick="verifyOTP()">Verifikasi Kode</button>
                </div>
                <div id="session-status" class="status-msg"></div>
                <div id="session-result" class="result-box"><label style="color:var(--accent-color); font-size:12px; display:block; margin-bottom:5px;">STRING SESSION KAMU:</label><code></code></div>
            </div>
            <div id="config-tab" class="tab-content">
                <div class="input-group"><label>STRING SESSION</label><textarea id="string-session-input" rows="4" placeholder="Tempel String Session di sini"></textarea></div>
                <button class="btn" id="btn-get-config" onclick="fetchConfig()">Intip Live Config Server</button>
                <div class="config-status status-msg" id="config-status"></div>
                <div id="config-result" class="result-box"><pre><code id="json-output"></code></pre></div>
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
                if(!apiId || !apiHash || !phone) { statusDiv.className = "status-msg error"; statusDiv.innerText = "Semua kolom wajib diisi!"; return; }
                statusDiv.className = "status-msg success"; statusDiv.innerText = "Mengirim OTP...";
                try {
                    const res = await fetch('/api/send_otp', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, phone: phone }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal kirim OTP");
                    loginData.temp_session = data.temp_session;
                    loginData.phone_code_hash = data.phone_code_hash;
                    statusDiv.innerText = "OTP terkirim! Cek Telegram kamu.";
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
                    if (!res.ok) throw new Error(data.detail || "Verifikasi gagal");
                    statusDiv.innerText = "Login sukses!";
                    const resBox = document.getElementById('session-result');
                    resBox.querySelector('code').innerText = data.session;
                    resBox.classList.add('active');
                    document.getElementById('step-2').style.display = 'none';
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }
            async function fetchConfig() {
                const apiId = document.getElementById('api-id').value || 8586525;
                const apiHash = document.getElementById('api-hash').value || "b502b18d61ecf433c5fc8534f9370869";
                const session = document.getElementById('string-session-input').value;
                const statusDiv = document.getElementById('config-status');
                if(!session) { statusDiv.className = "status-msg error"; statusDiv.innerText = "Masukkan session!"; return; }
                statusDiv.className = "status-msg success"; statusDiv.innerText = "Mengambil data server...";
                try {
                    const res = await fetch('/api/get_config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ api_id: parseInt(apiId), api_hash: apiHash, session: session }) });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || "Gagal ambil data");
                    statusDiv.innerText = "Data berhasil dimuat!";
                    document.getElementById('json-output').innerText = JSON.stringify(data.config, null, 2);
                    document.getElementById('config-result').classList.add('active');
                } catch (err) { statusDiv.className = "status-msg error"; statusDiv.innerText = err.message; }
            }
        </script>
    </body>
    </html>
    """
