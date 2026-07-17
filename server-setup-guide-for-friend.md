# LINE → Discord Bot — คู่มือ Setup สำหรับเพื่อน

## ภาพรวมระบบ
บอทรับข้อความ "update" จากกลุ่ม LINE แล้วรวบรวมส่งเข้า Discord อัตโนมัติทุกวันศุกร์ 18:00 (Asia/Bangkok)

- **GitHub repo**: `salinthip/line-to-discord`
- **เดิม deploy อยู่บน**: Railway (หมดสิทธิ์ free trial แล้ว กำลังหาที่โฮสต์ใหม่)
- **Stack**: Python / Flask + gunicorn + APScheduler

## ไฟล์ในโปรเจกต์
- `line_bot.py` — Flask webhook server หลัก (โค้ดทั้งหมดอยู่ในไฟล์เดียว)
- `requirements.txt` — dependencies
- `Procfile` — คำสั่งรัน

### requirements.txt
```
flask
gunicorn
line-bot-sdk>=3.0.0
apscheduler
requests
pytz
```

### Procfile
```
web: gunicorn line_bot:app --bind 0.0.0.0:$PORT
```

## Config — ตอนนี้อ่านจาก Environment Variables แล้ว (ไม่ hardcode ในโค้ดอีกต่อไป)
`line_bot.py` เปลี่ยนมาอ่านค่าจาก environment variables แทน เพราะจะ push ขึ้น GitHub ของเพื่อน (คนละ repo/บัญชี) ถ้าค่ายังฝังอยู่ในโค้ดแล้ว repo เป็น public จะหลุดทันที

**ต้องตั้งค่า 3 ตัวนี้เป็น environment variables (บังคับ ไม่ตั้งแล้วบอทจะรันไม่ขึ้น):**

| ชื่อ Variable | ค่า |
|---|---|
| `LINE_CHANNEL_SECRET` | `a4cdac2059c5c3c2e718652ead821ad4` |
| `LINE_CHANNEL_ACCESS_TOKEN` | `kaoUNhXLW5p+RimJ5pJW8/cppvrlpr4nplMIwBs8eD2hGm5av1fp5oXNLkKXTNqRrRTulbDcS1GyLSyl4Vpk1zK1fS2rwAmlRZxzRaetz9ieAdipajNhk8tb/HLN7GEKbpWiJYUT+AW15SwH1WHbtwdB04t89/1o/w1cDnyilFU=` |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/1516340699723993129/vF6pJOIL5aMPkGWt3nxXmdKEBfugTRbGoudKoKf9yY6rYs_AmQVuQzbIs8BJ5G8nHkQW` |

**ตัวเลือกเสริม (ไม่ตั้งก็ได้ มีค่า default อยู่แล้ว):**

| ชื่อ Variable | ค่า default |
|---|---|
| `COLLECT_START_HOUR` | `16` |
| `COLLECT_END_HOUR` | `18` |
| `TIMEZONE` | `Asia/Bangkok` |

ค่าจริงทั้งหมดอยู่ในไฟล์ `.env` ในโฟลเดอร์โปรเจกต์แล้ว (ไฟล์นี้ถูกกันไว้ใน `.gitignore` แล้ว **จะไม่ถูก push ขึ้น git** — ใช้เปิดดูเพื่อ copy ค่าไปกรอกใน Railway/Render dashboard เท่านั้น)

> **ข้อควรระวังเรื่องความปลอดภัย**: ค่าด้านบนคือ credential จริงที่ใช้งานอยู่ แนะนำให้พิจารณา regenerate `DISCORD_WEBHOOK_URL` ใหม่ก่อนส่งให้เพื่อน (ทำได้ง่ายจาก Discord channel settings)

## งานที่เพิ่งแก้ไปล่าสุด (อยู่ใน commit ล่าสุดที่ต้อง push)
1. **`looks_like_update()`** — เดิมข้อความเตือนทั่วไปที่มีคำว่า "อัพเดท" (เช่น "อย่าลืมอัพเดทนะ") จะถูกจับเป็น update ผิด ตอนนี้แก้ให้ต้องมี bullet (`-` หรือ `•`) อย่างน้อย 1 บรรทัดด้วยถึงจะนับเป็น update จริง
2. เพิ่ม route `GET /` สำหรับ health check (ใช้กับ UptimeRobot หรือ platform อื่นที่ต้อง ping กันไม่ให้ sleep)
3. ย้าย config (LINE secret/token, Discord webhook) จาก hardcode ในโค้ด → environment variables พร้อมเพิ่ม `.gitignore` กัน `.env` หลุดขึ้น git (โค้ดทดสอบแล้วว่า import และรันได้ปกติเมื่อมี env vars ครบ)

## งานที่ยังค้างอยู่ (Pending)
1. **`is_collection_window()` ยังเป็น testing mode** — ปัจจุบัน `return True` อยู่บนสุดของฟังก์ชัน (ข้ามการเช็ควันเวลาจริง) ต้องลบบรรทัดนั้นออกเพื่อกลับไปเช็ควันศุกร์ 16-18 น. จริง (โค้ดเช็คจริงมีอยู่แล้วด้านล่าง แค่ถูก return True บังไว้)
2. **ไม่มี persistent storage** — `collected_updates` เป็น dict ในหน่วยความจำเท่านั้น พอ server restart/redeploy/sleep ข้อมูลหายหมด ถ้าจะให้ทนทานจริงต้องต่อ database (เช่น Postgres) แทน

## วิธี Deploy (เลือกได้ตามความสะดวก)

### ตัวเลือก A: Railway ด้วยบัญชี/GitHub ของเพื่อน
1. เพื่อน push โค้ดขึ้น GitHub repo ของตัวเอง (**อย่า push ไฟล์ `.env`** — เช็คว่า `.gitignore` ติดไปด้วย)
2. สมัคร Railway ด้วย GitHub ของเพื่อน → New Project → Deploy from GitHub repo → เลือก repo นี้
3. Railway จะอ่าน `Procfile` อัตโนมัติ ไม่ต้องตั้ง Start Command เอง
4. เข้า **Variables tab** ของ service → เพิ่ม 3 ตัวที่บังคับ (`LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `DISCORD_WEBHOOK_URL`) ตามตารางด้านบน → Deploy จะรันใหม่อัตโนมัติ
5. Settings → Networking → **Generate Domain** เพื่อได้ public URL (`https://xxxx.up.railway.app`)
6. เอา URL ไปตั้งใน LINE Developers Console → Webhook URL = `https://xxxx.up.railway.app/webhook` → กด Verify
7. ทดสอบพิมพ์ `!ส่ง` ในกลุ่ม LINE เพื่อเช็คว่าบอทตอบและส่งเข้า Discord ได้

ถ้า Railway ของเพื่อนยังไม่เคยใช้ free trial มาก่อน จะได้ $5 credit ฟรี 30 วันแบบ Full Trial (verify ผ่าน GitHub) ใช้ได้สบายๆ กับบอทขนาดนี้ หลังจากนั้นค่อยพิจารณาว่าจะอัพเป็น Hobby $5/เดือนต่อไหม

### ตัวเลือก B: Render (ฟรีถาวร) + UptimeRobot
1. Render.com → New Web Service → connect repo ของเพื่อน
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn line_bot:app --bind 0.0.0.0:$PORT`
   - Instance Type: Free
2. เข้า **Environment tab** → เพิ่ม 3 ตัวที่บังคับตามตารางด้านบน
3. เอา URL ที่ได้ (`https://xxxx.onrender.com`) ไปตั้งใน LINE Developers Console → Webhook URL = `https://xxxx.onrender.com/webhook` → กด Verify
4. สมัคร UptimeRobot.com (ฟรี) → Add Monitor → HTTP(s) → URL `https://xxxx.onrender.com/` → Interval 5 นาที ping ตลอด 24 ชม.
   - เหตุผล: Render free จะ sleep หลังไม่มี request 15 นาที แล้ว "รีสตาร์ทใหม่" ทำให้ข้อมูลใน memory หาย ต้อง ping กันไว้ตลอดไม่ใช่แค่วันศุกร์

## Format ข้อความที่ทีมพิมพ์ใน LINE
```
Update [ชื่อ] [ช่วงวันที่]

[ชื่อ Project]
- สิ่งที่ทำ
- สิ่งที่ทำ

[ชื่อ Project 2]
- สิ่งที่ทำ
```
ต้องมี keyword (`update`/`อัพเดท`/`อัพเดต`/`อัปเดต`/`📝`) ในบรรทัดแรก **และ** มีอย่างน้อย 1 บรรทัด bullet ถึงจะถูกจับเป็น update

## Format ข้อความที่ส่งไป Discord
```
📋 SE Team Weekly Update | สัปดาห์ DD/MM/YYYY
───────────────────────────────────
👤 [ชื่อ]
📌 [ชื่อ Project]
　- สิ่งที่ทำ
👤 [ชื่อ]
...
───────────────────────────────────
🕐 อัพเดทเมื่อ DD/MM/YYYY HH:MM
```
ถ้าข้อความรวมยาวเกิน 1900 ตัวอักษร บอทจะแบ่งส่งเป็นหลายข้อความอัตโนมัติ
