"""WhatsApp Cloud API webhook.   uvicorn whatsapp.webhook:app --port 8000

Needs: pip install -r requirements-whatsapp.txt and env vars from .env.example.
Expose it with a tunnel (for example ngrok) and set the webhook URL in Meta's dashboard.
"""
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent.agent import SupportAgent
from agent.llm import get_backend
from whatsapp.parser import extract_message

app = FastAPI(title="D2C WhatsApp agent")
agent = SupportAgent(get_backend(os.getenv("AGENT_BACKEND", "mock")))
sessions = {}  # sender phone -> chat history (in memory; use Redis or a DB in production)


@app.get("/webhook")
def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive(request: Request):
    parsed = extract_message(await request.json())
    if parsed is None:
        return {"status": "ignored"}
    sender, text = parsed
    result = agent.reply(text, sessions.setdefault(sender, []))
    await send_text(sender, result.text)
    return {"status": "ok"}


async def send_text(to: str, body: str):
    phone_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    token = os.environ["WHATSAPP_TOKEN"]
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
