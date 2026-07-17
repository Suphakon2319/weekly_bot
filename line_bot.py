from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
import logging
import os
import pytz

# ========== CONFIG — อ่านจาก Environment Variables ==========
# ตั้งค่าเหล่านี้ใน Railway/Render dashboard (Variables tab) ห้าม hardcode ค่าจริงในโค้ด
def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"ไม่พบ environment variable: {name} — ต้องตั้งค่านี้ก่อนรันบอท")
    return value

LINE_CHANNEL_SECRET = _require_env("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = _require_env("LINE_CHANNEL_ACCESS_TOKEN")
DISCORD_WEBHOOK_URL = _require_env("DISCORD_WEBHOOK_URL")
COLLECT_START_HOUR = int(os.environ.get("COLLECT_START_HOUR", "16"))   # เริ่มเก็บข้อความ 16:00
COLLECT_END_HOUR = int(os.environ.get("COLLECT_END_HOUR", "18"))       # ส่ง Discord 18:00
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Bangkok")
# ============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# เก็บ updates ของแต่ละคน {ชื่อ: ข้อความ}
collected_updates: dict[str, str] = {}
tz = pytz.timezone(TIMEZONE)

def is_collection_window() -> bool:
    """เช็คว่าอยู่ในช่วงวันศุกร์ 16-18 น. ไหม (ปิดไว้ชั่วคราวเพื่อทดสอบ)"""
    return True  # TODO: เปลี่ยนกลับหลังทดสอบเสร็จ
    now = datetime.now(tz)
    is_friday = now.weekday() == 4
    in_window = COLLECT_START_HOUR <= now.hour < COLLECT_END_HOUR
    return is_friday and in_window

def looks_like_update(text: str) -> bool:
    """เช็คว่าข้อความเป็น update จริงหรือเปล่า
    ต้องมี keyword ในบรรทัดแรก AND มีอย่างน้อย 1 บรรทัดที่เป็น bullet (- หรือ •)
    เพื่อกันข้อความเตือนทั่วไป เช่น "วันนี้อย่าลืมอัพเดทนะ" ที่มี keyword แต่ไม่ใช่ update จริง
    """
    lines = text.split("\n")
    first_line = lines[0].lower()
    has_keyword = (
        "update" in first_line or   # จับทั้ง "update nt" และ "nt update"
        "📝" in first_line or
        "อัพเดท" in first_line or
        "อัพเดต" in first_line or
        "อัปเดต" in first_line
    )
    if not has_keyword:
        return False

    has_bullet = any(line.strip().startswith(("-", "•")) for line in lines[1:])
    return has_bullet

def send_to_discord():
    """รวบรวมทุก update แล้วส่งไป Discord"""
    if not collected_updates:
        logging.info("ไม่มีข้อมูลที่จะส่ง")
        return

    now = datetime.now(tz)
    lines = [
        f"📋 **SE Team Weekly Update | สัปดาห์ {now.strftime('%d/%m/%Y')}**",
        "─" * 35,
        "",
    ]

    for name, content in collected_updates.items():
        lines.append(f"👤 **{name}**")
        # ทำให้ชื่อโปรเจ็คตัวหนา (บรรทัดที่ไม่ใช่บรรทัดแรก ไม่ใช่ bullet และไม่ว่าง)
        content_lines = content.strip().split("\n")
        for i, line in enumerate(content_lines):
            stripped = line.strip()
            if i == 0:
                # บรรทัดแรก = ชื่อ + วันที่ (ข้ามไป)
                continue
            elif stripped == "":
                lines.append("")
            elif stripped.startswith("-") or stripped.startswith("•"):
                lines.append(f"　{stripped}")
            else:
                # ชื่อโปรเจ็ค → ตัวหนา
                lines.append(f"📌 **{stripped}**")
        lines.append("")

    lines.append("─" * 35)
    lines.append(f"🕐 _อัพเดทเมื่อ {now.strftime('%d/%m/%Y %H:%M')}_")
    full_msg = "\n".join(lines)

    # แบ่งส่งถ้าเกิน 1900 ตัวอักษร
    chunks, current = [], ""
    for line in full_msg.split("\n"):
        candidate = current + "\n" + line if current else line
        if len(candidate) > 1900:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)

    for chunk in chunks:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": chunk})
        if resp.status_code not in (200, 204):
            logging.error(f"Discord error: {resp.status_code} {resp.text}")

    collected_updates.clear()
    logging.info("ส่ง Weekly Update ไป Discord เรียบร้อยแล้ว")

# ===== Health check (สำหรับ UptimeRobot ping กันไม่ให้ sleep) =====
@app.route("/", methods=["GET"])
def health_check():
    return "OK", 200

# ===== LINE Webhook =====
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    text = event.message.text.strip()

    # command พิเศษสำหรับทดสอบ: พิมพ์ "!ส่ง" เพื่อส่ง Discord ทันที
    if text == "!ส่ง":
        send_to_discord()
        logging.info("ส่งด้วย command !ส่ง แล้ว")
        return

    if not is_collection_window():
        return

    if not looks_like_update(text):
        return

    # เช็คว่าข้อความส่งมาวันนี้ไหม (ป้องกันข้อความวันก่อนหน้า)
    msg_date = datetime.fromtimestamp(event.timestamp / 1000, tz=tz).date()
    today = datetime.now(tz).date()
    if msg_date != today:
        logging.info(f"ข้ามข้อความเก่า (ส่งเมื่อ {msg_date})")
        return

    # ดึงชื่อจากบรรทัดแรก
    # "Update น้ำทิพย์ 09-13 Jun" → "น้ำทิพย์"
    # "น้ำทิพย์ update 09-13 Jun" → "น้ำทิพย์"
    # "📝 น้ำทิพย์ | 09-13 Jun" → "น้ำทิพย์"
    first_line = text.split("\n")[0].strip()
    words = first_line.replace("📝", "").replace("|", "").split()
    skip_words = {"update", "อัพเดท", "อัพเดต", "อัปเดต"}
    name = next((w for w in words if w.lower() not in skip_words), "unknown")

    collected_updates[name] = text
    logging.info(f"เก็บ update ของ {name} แล้ว ({len(co