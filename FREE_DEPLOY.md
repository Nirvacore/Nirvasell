# Free deploy — โปรเจกต์ส่วนตัวฟรี 100%

ใช้เป็นของเราเอง ไม่จ่ายเลยสักบาท เลือกได้ 4 ทาง — ตามที่ถนัด

---

## 🥇 Streamlit Community Cloud (แนะนำมากสุด)

**ฟรีตลอดกาล · ตั้งค่า ~5 นาที · สนับสนุนโดย Streamlit ตรงๆ · auto-SSL**

### ขั้นตอน

```bash
# 1. push โค้ดขึ้น GitHub (ใช้ private repo ได้)
cd /Users/machd/Claude/nirva
git init
git add .
git commit -m "first deploy"
gh repo create nirva-sell --private --source=. --push
# ถ้าไม่มี gh CLI ก็สร้าง repo ใน github.com → push ปกติ

# 2. ไปที่ https://share.streamlit.io
# 3. คลิก "New app"
#    - Repository: นาย/nirva-sell
#    - Branch: main
#    - Main file path: app.py
# 4. Advanced settings → Secrets — paste:
```

```toml
# (จะวางใน secrets editor บนเว็บ)
ANTHROPIC_API_KEY = "sk-ant-..."   # คีย์ของคุณ
PROMPTPAY_ID = "0812345678"        # ใส่หรือไม่ใส่ก็ได้
PROMPTPAY_NAME = "ร้านของคุณ"
APP_URL = "https://your-app.streamlit.app"

# ถ้าจะใช้ Google login (optional):
[auth]
redirect_uri = "https://your-app.streamlit.app/oauth2callback"
cookie_secret = "<สุ่ม 64 ตัวอักษร>"

[auth.google]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

5. กด **Deploy** → รอ 2-3 นาที → เสร็จ ได้ URL `https://YOURNAME-nirva-sell.streamlit.app`

**Limits ฟรี:** 1 GB RAM, sleep หลังไม่มีคนใช้ 7 วัน (ตื่นเองตอนคนเปิด)

---

## 🥈 Hugging Face Spaces

**ฟรี · 16 GB RAM (เยอะกว่า Streamlit Cloud!) · ไม่มี sleep · custom domain ได้**

### ขั้นตอน

1. สมัครที่ https://huggingface.co (ฟรี)
2. คลิก profile → New Space
3. ตั้งค่า:
   - **Space name**: `nirva-sell` (เป็น URL: `username-nirva-sell.hf.space`)
   - **SDK**: Streamlit
   - **Hardware**: CPU basic (ฟรี)
   - **Visibility**: Private (ของเราคนเดียว)
4. push code:

```bash
git remote add hf https://huggingface.co/spaces/YOURNAME/nirva-sell
git push hf main
```

5. ตั้ง secrets ใน Space → Settings → Variables and secrets:
   - `ANTHROPIC_API_KEY`
   - `APP_URL` = `https://YOURNAME-nirva-sell.hf.space`

6. รอ build 3-5 นาที → live

**ข้อดี:** RAM เยอะกว่ามาก (เหมาะกับ Vision / rembg ที่กิน RAM)

---

## 🥉 Cloudflare Tunnel (รันจากเครื่องเรา ฟรีตลอด)

**ฟรี · ทำงานบนเครื่อง Mac ของเรา · ไม่ต้องเช่า server · custom domain ฟรี**

ข้อเสีย: คอมเราต้องเปิดอยู่ตลอด

### ขั้นตอน

```bash
# 1. ติดตั้ง cloudflared (Mac)
brew install cloudflared

# 2. login เข้า Cloudflare
cloudflared tunnel login
# → เปิดเบราว์เซอร์ ให้ login + ผูก domain ใน Cloudflare

# 3. สร้าง tunnel ชื่อ nirva
cloudflared tunnel create nirva

# 4. ผูก domain (ฟรี: ใช้ domain ที่อยู่ใน Cloudflare)
cloudflared tunnel route dns nirva nirva.your-domain.com

# 5. รัน streamlit + tunnel พร้อมกัน
streamlit run app.py &
cloudflared tunnel run --url http://localhost:8501 nirva
```

ตอนนี้เปิด `https://nirva.your-domain.com` ได้แล้ว — SSL อัตโนมัติ ปลอดภัย

**ตรง:** ไม่มี TODO เปิดเครื่อง — เปิดทั้งวัน อยู่ที่ Mac

---

## 🏅 Railway / Render / Fly.io

ถ้าอยากได้ container แบบ professional + free tier:

| Service | Free quota | Sleep? |
|---------|-----------|--------|
| **Railway** | $5 credit/เดือน | ไม่ |
| **Render** | 750 ชม/เดือน | ใช่ (sleep หลังไม่มีคน 15 นาที) |
| **Fly.io** | 3 small VMs ฟรี | ไม่ |

ทุกตัวรองรับ Dockerfile ที่เรามีอยู่แล้ว — just `git push` แล้วใช้ได้

```bash
# Railway
brew install railway
railway login
railway up

# Render — สร้าง Web Service ในเว็บ → connect GitHub → เลือก repo
# Fly
brew install flyctl
flyctl launch
```

---

## 📊 เปรียบเทียบให้เห็นภาพ

| | Streamlit Cloud | HF Spaces | Cloudflare Tunnel | Railway |
|---|---|---|---|---|
| **ค่าใช้จ่าย** | ฟรี | ฟรี | ฟรี | ฟรี ($5 credit) |
| **RAM** | 1 GB | 16 GB | unlimited (ของคุณ) | 512 MB |
| **Sleep** | 7 วัน inactive | ไม่ | ไม่ (คอมเปิดต้อง) | ไม่ |
| **Custom domain** | ไม่ฟรี | ฟรี | ฟรี | ฟรี |
| **Setup** | 5 นาที | 10 นาที | 15 นาที | 10 นาที |
| **SSL** | อัตโนมัติ | อัตโนมัติ | อัตโนมัติ | อัตโนมัติ |

---

## 💡 ผมแนะนำว่า

**ถ้าเพิ่งเริ่ม:** Streamlit Community Cloud — เร็ว ฟรีไม่จำกัด

**ถ้าใช้บ่อย + ของหนัก (Vision/rembg):** Hugging Face Spaces — RAM เยอะ

**ถ้าอยากเป็นเจ้าของเอง 100% + custom domain:** Cloudflare Tunnel

**ถ้าจะขายต่อให้คนอื่น:** Railway / Render (ดู DEPLOY.md ที่เขียนไว้)

---

## ⚙ จะตั้งค่าอะไรหลังจาก deploy

ไม่ว่าจะ deploy ที่ไหน หลัง live แล้ว ทำพวกนี้:

1. **เปิด URL → สมัคร account แรก** = ได้เป็น admin อัตโนมัติ
2. **Sidebar → ใส่ Anthropic API key** ของคุณ
3. **หน้า Legal → Admin panel** → กรอก contact info
4. **หน้า Support → Admin panel** → ใส่ PromptPay ID
5. **(option)** หน้า Admin → Social Login setup → GitHub / Facebook / LINE

เรียบร้อย — ลูกค้าสมัครได้แล้ว
