import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
