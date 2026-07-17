# LINE → Discord Weekly Update Bot

รับข้อความ update จากกลุ่ม LINE ทุกวันศุกร์ 16-18 น. แล้วส่งรวมไปยัง Discord อัตโนมัติเวลา 18:00 น.

---

## รูปแบบข้อความที่บอทจะจับ

สมาชิกพิมพ์ใน LINE กลุ่มแบบนี้:

```
nt update 09/06–13/06/2026

1. Project Name
- สิ่งที่ทำ
- สิ่งที่ทำ

2. Project Name
- สิ่งที่ทำ
```

บอทจะจับข้อความที่มีคำว่า **"update"** และ **ปี ค.ศ.** โดยอัตโนมัติ

---

## ขั้นตอนติดตั้ง

### 1. สร้าง Discord Webhook

1. เปิด Discord → ห้องที่จะให้บอทส่ง → ⚙️ Edit Channel
2. **Integrations → Webhooks → New Webhook**
3. คัดลอก **Webhook URL**

### 2. ตั้งค่า line_bot.py

แก้ค่าใน CONFIG:

```python
LINE_CHANNEL_SECRET = "จาก LINE Developers → Basic settings"
LINE_CHANNEL_ACCESS_TOKEN = "จาก LINE Developers → Messaging API"
DISCORD_WEBHOOK_URL = "Webhook URL จาก Discord"
```

### 3. Deploy บน Railway

1. สมัคร [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. อัปโหลดไฟล์ในโฟลเดอร์นี้
3. เพิ่ม Environment Variables แทนค่าใน CONFIG (แนะนำกว่าใส่ตรงในโค้ด)
4. Railway จะให้ URL เช่น `https://your-app.railway.app`

### 4. ตั้งค่า LINE Webhook URL

1. ไปที่ LINE Developers → Messaging API
2. ใส่ Webhook URL: `https://your-app.railway.app/webhook`
3. กด **Verify** → ต้องขึ้น Success
4. เปิด **Use webhook**

### 5. เพิ่มบอทเข้ากลุ่ม LINE

1. LINE Developers → Messaging API → QR Code
2. แสกน QR เพื่อเพิ่มบอทเข้ากลุ่ม

---

## การทำงาน

| เวลา | สิ่งที่เกิดขึ้น |
|------|----------------|
| ศุกร์ 16:00 | บอทเริ่มเก็บข้อความที่มี "update" ในกลุ่ม LINE |
| ศุกร์ 16-18 น. | สมาชิกพิมพ์ update ตามปกติ |
| ศุกร์ 18:00 | บอทรวบรวมทุกคนแล้วส่งไป Discord อัตโนมัติ |
