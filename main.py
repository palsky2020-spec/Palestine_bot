import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
TO_CHANNEL = os.getenv("TO_CHANNEL")
FROM_CHANNELS = os.getenv("FROM_CHANNELS", "QudsN,tjrebe1111,alburaij,livequds,AkkaNews48,alersalps,alhodhud,palnws24")

SOURCES = [s.strip().replace("https://t.me/", "").replace("@", "") for s in FROM_CHANNELS.split(",") if s.strip()]

# هذا السطر هو اللي زبط معك - بطلع بس مربع القناة بدون نص
CHANNEL_FOOTER = "\n\n[‎](https://t.me/Palestineforours)"

print("🚀 Bot started - Copy Mode مع مربع القناة")
print(f"TO: {TO_CHANNEL}")
print(f"FROM: {SOURCES}")

# حل مشكلة Render - بفتح بورت وهمي
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCES))
async def handler(event):
    try:
        msg = event.message
        text = msg.message or msg.text or ""

        if event.chat and event.chat.username and event.chat.username.lower() == "alhodhud":
            if any(word in text for word in ["هدية", "هدايا", "إرسال الهدايا", "🎁", "Gift"]):
                print(f"🎁 تم تجاهل رسالة هدايا من {event.chat.username}")
                return

        print(f"📩 جديد من {event.chat.username}")
        new_text = text + CHANNEL_FOOTER if text else CHANNEL_FOOTER

        if msg.media:
            await client.send_message(TO_CHANNEL, new_text, file=msg.media)
        else:
            await client.send_message(TO_CHANNEL, new_text)

        print("✅ تم النشر مع مربع القناة")
    except Exception as e:
        print(f"❌ خطأ: {e}")

async def main():
    await client.start()
    print("📡 شغال - يتجاهل هدايا الهدهد")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
