"""Terms of Service + Privacy Policy.

Defaults are MIT-license-friendly and PDPA-compliant (Thailand's GDPR).
Admin can override via user_settings — see pages/L_📄_Legal.py.

These are SENSIBLE DEFAULTS, not legal advice. Have a Thai lawyer review
before charging real money or onboarding business customers."""
from __future__ import annotations
from datetime import date


# ---- Editable defaults — admin can override per-deployment --------------

_DEFAULT_TOS_TH = f"""# เงื่อนไขการใช้งาน

**ปรับปรุงล่าสุด: {date.today().isoformat()}**

ยินดีต้อนรับสู่ nirva.sell ("บริการ"). การใช้บริการของเราถือว่าคุณยอมรับ
ข้อตกลงต่อไปนี้

## 1. สิ่งที่ nirva.sell ทำ

nirva.sell เป็นเครื่องมือช่วย reseller รวบรวมข้อมูลสินค้า สร้างเนื้อหา
ด้วย AI และส่งออกไปยัง marketplace ต่างๆ คุณ **ใช้ API key ของคุณเอง**
สำหรับเรียก AI — เราไม่ได้เป็นตัวกลางในการขายและไม่ได้ถือเงิน

## 2. account และความรับผิดชอบ

- คุณต้องให้ข้อมูลที่ถูกต้องตอนสมัคร
- คุณรับผิดชอบในการรักษา password ของคุณ
- ห้ามใช้บริการเพื่อสิ่งผิดกฎหมาย / ละเมิดเครื่องหมายการค้า /
  ขายของผิดกฎหมาย
- account ที่ไม่ใช้งานเกิน 12 เดือนอาจถูกลบ

## 3. เนื้อหาที่ AI สร้าง

- เนื้อหาที่ AI สร้างเป็นของคุณ คุณนำไปใช้เชิงพาณิชย์ได้
- เราไม่รับประกันว่าเนื้อหาจะถูกต้อง 100% — คุณต้องตรวจสอบก่อนใช้
- เราไม่รับผิดชอบหากเนื้อหาที่ AI สร้างไปละเมิดสิทธิของบุคคลที่สาม

## 4. ค่าบริการ

nirva.sell ใช้งานได้ฟรี ตามนโยบาย "จ่ายเท่าที่ไหว" หากต้องการสนับสนุน
มีช่องทาง PromptPay / Stripe / GitHub Sponsors บนหน้า Support

## 5. การจำกัดความรับผิด

บริการให้ "ตามที่เป็น" โดยไม่มีการรับประกันใดๆ ทั้งสิ้น เราไม่รับผิดชอบ
ต่อความเสียหายทางตรงหรือทางอ้อมจากการใช้งาน

## 6. การเปลี่ยนแปลง

เราอาจปรับเงื่อนไขนี้เป็นครั้งคราว การใช้งานต่อหลังการปรับปรุง
ถือว่ายอมรับเงื่อนไขใหม่

## 7. ติดต่อ

หากมีคำถาม ติดต่อได้ตามช่องทางที่ระบุในหน้า Support
"""


_DEFAULT_TOS_EN = f"""# Terms of Service

**Last updated: {date.today().isoformat()}**

Welcome to nirva.sell ("Service"). By using our Service you agree to the
terms below.

## 1. What nirva.sell does

nirva.sell is a tool that helps resellers consolidate product data,
generate content with AI, and export to various marketplaces. You provide
**your own AI API key** — we never act as a payment intermediary and never
hold your money.

## 2. Your account

- You must provide accurate information when signing up.
- You are responsible for keeping your password safe.
- You may not use the Service for unlawful activity, IP infringement,
  or selling illegal items.
- Inactive accounts (12+ months) may be deleted.

## 3. AI-generated content

- Content created by the AI is yours; you may use it commercially.
- We do not warrant 100% accuracy — review before publishing.
- We are not liable if AI-generated content infringes third-party rights.

## 4. Pricing

nirva.sell is free under a "pay what you can" model. Optional support is
available via PromptPay / Stripe / GitHub Sponsors on the Support page.

## 5. Limitation of liability

The Service is provided "AS IS" without any warranty. We are not liable
for direct or indirect damages arising from your use.

## 6. Changes

We may update these terms occasionally. Continued use constitutes
acceptance of the new terms.

## 7. Contact

For questions, use the channels listed on the Support page.
"""


_DEFAULT_PRIVACY_TH = f"""# นโยบายความเป็นส่วนตัว

**ปรับปรุงล่าสุด: {date.today().isoformat()}**

นโยบายนี้สอดคล้องกับ PDPA (พระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล)

## ข้อมูลที่เราเก็บ

- **อีเมล + ชื่อแสดง** — เพื่อสร้าง account
- **password hash** — เก็บแบบ PBKDF2-SHA256 200,000 รอบ ไม่ใช่ plaintext
- **สินค้าที่คุณเพิ่ม** — เก็บใน SQLite database ของคุณเอง
  (data/users/{{user_id}}.db) ผู้ใช้คนอื่นเข้าไม่ได้
- **ภาพสินค้า** — ถ้าคุณใช้ Cloudinary จะถูก upload ไปที่นั่น
- **AI prompts + ผลลัพธ์** — เก็บใน database คุณเอง

## ข้อมูลที่เรา **ไม่** เก็บ

- รหัสบัตรเครดิต/ข้อมูลทางการเงิน (Stripe/PromptPay ทำเอง — เราเห็นแค่
  จำนวนเงินที่คุณรายงาน)
- Anthropic API key (เก็บใน user_settings ของคุณ — ใช้เรียก Claude
  โดยตรง ไม่ผ่าน server เรา)
- ข้อมูลตำแหน่งที่ตั้ง / cookies tracking
- พฤติกรรมการใช้งานเพื่อโฆษณา

## การใช้ Claude API

ทุกครั้งที่ AI ทำงาน คำขอจะถูกส่งไปยัง Anthropic Claude ด้วย API key
ของคุณเอง Anthropic เก็บ log ตามนโยบายของพวกเขา
(https://www.anthropic.com/legal/privacy)

## สิทธิของคุณ (PDPA)

- ขอดูข้อมูลทั้งหมดของคุณ — หน้า Account → "Export all data"
  (ได้ ZIP ของ DB + ภาพ + CSV ทุกอย่าง)
- ขอแก้ไข — ทำได้ในหน้า Account
- ขอลบ — หน้า Account → "Delete my account" (ลบ DB ทั้งหมดของคุณ)
- ขอย้ายข้อมูล — Export ZIP แล้วนำไป import ที่อื่น

## คุกกี้

เราใช้ session cookie เพื่อให้ login ต่อเนื่อง ไม่ใช้ tracking cookies
ของ third party

## ติดต่อ

ส่งคำขอเกี่ยวกับข้อมูลส่วนตัวผ่านช่องทาง Support
"""


_DEFAULT_PRIVACY_EN = f"""# Privacy Policy

**Last updated: {date.today().isoformat()}**

Compliant with Thailand's PDPA (Personal Data Protection Act).

## What we collect

- **Email + display name** — to create your account.
- **Password hash** — PBKDF2-SHA256 with 200k iterations; never stored
  in plaintext.
- **Your products** — stored in your own per-user SQLite database
  (data/users/{{user_id}}.db). No other user can read it.
- **Product images** — uploaded to Cloudinary only if you configure it.
- **AI prompts + outputs** — stored in your own database.

## What we do NOT collect

- Credit card / financial data (Stripe / PromptPay handle that — we
  only see the amount you self-report).
- Anthropic API key (stored in your user_settings; sent directly to
  Claude — never proxied through our servers).
- Location data or tracking cookies.
- Behavioral data for advertising.

## Claude API usage

Each AI call goes directly to Anthropic Claude using your own API key.
Anthropic retains logs per their policy
(https://www.anthropic.com/legal/privacy).

## Your rights (PDPA)

- **Access** — Account page → "Export all data" (ZIP with DB + images
  + CSVs of everything).
- **Rectify** — edit anything in the Account page.
- **Delete** — Account → "Delete my account" (wipes your entire DB).
- **Portability** — exported ZIP can be imported elsewhere.

## Cookies

We use a session cookie to keep you logged in. We do NOT use third-party
tracking cookies.

## Contact

Address data-related requests via the Support page.
"""


# ---- Public API ---------------------------------------------------------

def get_tos(lang: str = "th") -> str:
    """Return Terms of Service, in `th` or `en`. Admin override takes priority."""
    try:
        import user_settings as us
        override = us.get(f"legal.tos.{lang}", "") or ""
        if override.strip():
            return override
    except Exception:
        pass
    return _DEFAULT_TOS_TH if lang == "th" else _DEFAULT_TOS_EN


def get_privacy(lang: str = "th") -> str:
    """Return Privacy Policy, in `th` or `en`. Admin override takes priority."""
    try:
        import user_settings as us
        override = us.get(f"legal.privacy.{lang}", "") or ""
        if override.strip():
            return override
    except Exception:
        pass
    return _DEFAULT_PRIVACY_TH if lang == "th" else _DEFAULT_PRIVACY_EN


def set_tos(lang: str, text: str) -> None:
    import user_settings as us
    us.set(f"legal.tos.{lang}", (text or "").strip())


def set_privacy(lang: str, text: str) -> None:
    import user_settings as us
    us.set(f"legal.privacy.{lang}", (text or "").strip())


def get_contact() -> dict:
    """Operator-set contact info — appears in footer + Support page."""
    try:
        import user_settings as us
        return {
            "email":     us.get("legal.contact_email", "")     or "",
            "line_id":   us.get("legal.contact_line_id", "")   or "",
            "company":   us.get("legal.company_name", "")      or "",
            "address":   us.get("legal.company_address", "")   or "",
            "tax_id":    us.get("legal.tax_id", "")            or "",
        }
    except Exception:
        return {}


def set_contact(**kwargs) -> None:
    import user_settings as us
    mapping = {
        "email":   "legal.contact_email",
        "line_id": "legal.contact_line_id",
        "company": "legal.company_name",
        "address": "legal.company_address",
        "tax_id":  "legal.tax_id",
    }
    for k, v in kwargs.items():
        if k in mapping and v is not None:
            us.set(mapping[k], str(v).strip())
