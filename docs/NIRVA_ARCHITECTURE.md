# 🧠 NIRVA — Autonomous Business Operating System

**สถาปัตยกรรมหลัก (Master Architecture)**

> เป้าหมาย: สร้าง *Self-Managing Company Platform* ที่ให้ธุรกิจทำงานได้เทียบเท่า
> องค์กร 100–500 คน ด้วยคนจริงเพียง 3–10 คน — โดย AI/Automation รับงานซ้ำ
> ส่วนมนุษย์ถือ **การตัดสินใจ อนุมัติ ความรับผิดชอบตามกฎหมาย ความสัมพันธ์ และวิสัยทัศน์**

เอกสารนี้เป็น blueprint ระดับสถาปัตยกรรม ไม่ใช่ implementation
ดูบริบทกลุ่มธุรกิจที่ NIRVA สังกัดได้ที่ [BEST_GROUP.md](./BEST_GROUP.md)

---

## สารบัญ

1. [หลักการออกแบบ (Design Principles)](#0-หลักการออกแบบ)
2. [ภาพรวมสถาปัตยกรรม (Architecture Overview)](#1-ภาพรวมสถาปัตยกรรม)
3. [Human-in-the-Loop Model](#2-human-in-the-loop-model--เส้นแบ่งคนกับ-ai)
4. **10 Layers**
   - [Layer 1 — Governance](#layer-1--governance-layer)
   - [Layer 2 — Knowledge](#layer-2--knowledge-layer-nirva-knowledge-hub)
   - [Layer 3 — People](#layer-3--people-layer-nirva-people)
   - [Layer 4 — ESG / Sustainability](#layer-4--esg-layer-nirva-sustainability)
   - [Layer 5 — AI](#layer-5--ai-layer-multi-ai-ecosystem)
   - [Layer 6 — Automation](#layer-6--automation-layer-nirva-automation-engine)
   - [Layer 7 — Finance](#layer-7--finance-layer-nirva-finance)
   - [Layer 8 — Sales / CRM](#layer-8--sales-layer-nirva-crm)
   - [Layer 9 — Procurement](#layer-9--procurement-layer-nirva-procurement)
   - [Layer 10 — Self-Managing Company](#layer-10--self-managing-company)
5. [Cross-cutting Concerns](#3-cross-cutting-concerns)
6. [Roadmap / Phasing](#4-roadmap--การทยอยสร้าง)

---

## 0. หลักการออกแบบ

ทุก Process ในระบบต้องมีคุณสมบัติ 5 ข้อ — เป็น "สัญญา" ที่ทุก module ต้องทำตาม:

| คุณสมบัติ | หมายความว่า | บังคับใช้ผ่าน |
|-----------|--------------|----------------|
| **Measurable** | มี metric/KPI ที่วัดได้เป็นตัวเลข | ทุก entity ผูกกับ metric definition |
| **Auditable** | ทุกการเปลี่ยนแปลงมี trail ว่าใคร/เมื่อไหร่/ทำไม | Event log + immutable audit store (Layer 1) |
| **Learnable** | ผลลัพธ์ป้อนกลับเข้า Knowledge ได้ | Lessons Learned pipeline (Layer 2) |
| **Automatable** | นิยามเป็น workflow/rule ได้ | Automation Engine (Layer 6) |
| **Sustainable** | ผลกระทบ ESG วัดได้ | Sustainability hooks (Layer 4) |

**กฎเหล็ก:** ถ้า process ใดไม่ผ่าน 5 ข้อนี้ ถือว่ายังไม่พร้อมขึ้นระบบ

---

## 1. ภาพรวมสถาปัตยกรรม

NIRVA เป็น **layered platform** — layer ล่างเป็นรากฐาน (governance, knowledge,
ai, automation) ที่ทุก business module ด้านบนเรียกใช้ร่วมกัน ไม่ใช่ระบบที่ต่าง
คนต่างทำ

```
┌─────────────────────────────────────────────────────────────┐
│  L10  SELF-MANAGING COMPANY  (sense → analyze → propose →      │
│        approve → act)  — orchestration เหนือทุก layer          │
├─────────────────────────────────────────────────────────────┤
│  BUSINESS MODULES                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ L7 Finance│ │ L8 CRM   │ │ L9 Procure   │ │ L3 People    │  │
│  └──────────┘ └──────────┘ └──────────────┘ └──────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ L4 ESG / Sustainability (วัดผลกระทบจากทุก module)          │ │
│  └──────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  PLATFORM CORE (รากฐานที่ทุก module ใช้ร่วม)                   │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ L6 Auto- │ │ L5 AI         │ │ L2 Know- │ │ L1 Governance │  │
│  │ mation   │ │ (Multi-LLM)   │ │ ledge    │ │ (audit/auth)  │  │
│  └──────────┘ └──────────────┘ └──────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  FOUNDATION: Identity · Event Bus · Data Lake · API Gateway    │
└─────────────────────────────────────────────────────────────┘
```

**Event-driven backbone:** ทุก action สร้าง *event* ลง event bus → Automation
ฟัง event เพื่อ trigger workflow, ESG ฟังเพื่อคำนวณผลกระทบ, Self-Managing
layer ฟังเพื่อ detect anomaly, Audit ฟังเพื่อบันทึก trail นี่คือสิ่งที่ทำให้
"บริษัทดูแลตัวเองได้"

**Data model หลัก** (entity กลางที่ทุก layer แชร์):
`Organization → Department → Role → Person`, `Process`, `Document`, `Metric`,
`Event`, `ApprovalRequest`, `RiskItem` — มี `id`, `created/updated_by`,
`audit_ref` ทุกตัว

---

## 2. Human-in-the-Loop Model — เส้นแบ่งคนกับ AI

ทุกการกระทำในระบบจัดอยู่ใน 4 ระดับสิทธิ์ — เป็น "ภาษากลาง" ที่ใช้ตลอดทุก layer:

| ระดับ | ใครทำ | ตัวอย่าง |
|-------|--------|----------|
| 🟢 **AUTO** | AI/Automation ทำเองเต็มที่ | จัดหมวดเอกสาร, สรุปประชุม, แจ้งเตือน, reconcile ข้อมูลที่ match |
| 🟡 **AUTO + REVIEW** | AI ทำร่าง มนุษย์ตรวจ/แก้ก่อนใช้ | ร่างใบเสนอราคา, ร่าง JD, จัด budget forecast |
| 🟠 **HUMAN APPROVE** | AI เสนอ มนุษย์ต้องกดอนุมัติจึงมีผล | จ่ายเงิน, เซ็นสัญญา, จ้าง/เลิกจ้าง, ราคาขายต่ำกว่าทุน |
| 🔴 **LEGAL / LICENSED** | ต้องผู้มีคุณสมบัติตามกฎหมายเท่านั้น | ปิดงบ, สอบบัญชี, รับรองเอกสารนิติบุคคล |

ทุก workflow ต้องระบุระดับนี้ที่แต่ละ step — และระดับ 🟠/🔴 จะถูก enforce โดย
**Authority Matrix** ใน Layer 1

---

## Layer 1 — Governance Layer

**หน้าที่:** เป็นชั้นกำกับที่บอกว่า "ใครมีสิทธิ์ทำอะไร, อะไรต้องอนุมัติ,
ความเสี่ยงอยู่ตรงไหน, ทุกอย่างถูกบันทึกไว้ครบ" — เป็นรากฐานของ trust ทั้งระบบ

### Components

| Module | บทบาท | Auto / Human |
|--------|--------|--------------|
| **Company Governance** | นิยามโครงสร้างนิติบุคคล, ผู้ถือหุ้น, กรรมการ, มติที่ประชุม | 🟡 ระบบจัดเก็บ/เตือน, คนตัดสิน |
| **Corporate Governance** | นโยบาย, code of conduct, จริยธรรม, conflict of interest | 🟡 |
| **Delegation Matrix** | มอบอำนาจชั่วคราว (เช่นหัวหน้าลา → มอบให้รอง) | 🟢 ระบบสลับ scope ตามตาราง |
| **Authority Matrix** | วงเงิน/ประเภทงานที่แต่ละ role อนุมัติได้ (DOA) | 🟢 engine บังคับใช้ทุก approval |
| **Risk Management** | ทะเบียนความเสี่ยง, likelihood × impact, owner, mitigation | 🟡 AI เสนอความเสี่ยงจาก signal, คน rate |
| **Compliance Management** | ผูกกฎหมาย/มาตรฐานกับ control + หลักฐาน | 🟡 |
| **Legal Management** | ทะเบียนสัญญา, วันหมดอายุ, ภาระผูกพัน | 🟡 AI สรุป/เตือน, คนตัดสิน |
| **Internal Audit** | แผนตรวจ, checklist, finding, corrective action | 🟡 AI รวบหลักฐานจาก event log |
| **AI Governance** | policy การใช้ AI: ข้อมูลไหนห้ามส่ง, model ไหนใช้ได้, ใครรับผิดเมื่อ AI ผิด | 🟠 |

### หัวใจสำคัญ: Authority Matrix Engine

นี่คือ component ที่ทำให้ "อนุมัติ" มีความหมาย — ทุก `ApprovalRequest` จะถูก
route ตามกฎ: *ประเภทงาน + วงเงิน + cost center → หา approver ที่มีสิทธิ์ →
ถ้าเกินวงเงินก็ escalate ขึ้นชั้นถัดไป* และทุกการอนุมัติบันทึกลง **immutable
audit store** (append-only, hash-chained) ที่แก้ย้อนหลังไม่ได้

### Data
`LegalEntity`, `Policy`, `AuthorityRule(role, action_type, max_amount, scope)`,
`RiskItem`, `ComplianceControl`, `Contract`, `AuditFinding`, `AuditEvent(immutable)`

---

## Layer 2 — Knowledge Layer (Nirva Knowledge Hub)

**หน้าที่:** ทำให้องค์กร "จำได้" และ "สอนตัวเองได้" — เปลี่ยนความรู้ที่กระจัด
กระจายให้ค้นเจอ ใช้ซ้ำ และให้ AI หยิบไปตอบงานจริงได้

### สิ่งที่เก็บ
SOP · ISO documents · Policies · Training material · **Lessons Learned** ·
Meeting Notes · Contracts · Best Practices

### สถาปัตยกรรมความรู้ (3 ชั้น)

```
แหล่งข้อมูลดิบ (docs, notes, chat, email, ระบบอื่น ๆ ในแพลตฟอร์ม)
        │  ingest + chunk + embed + จัด metadata อัตโนมัติ (🟢)
        ▼
[ Vector Store ]  ←──┐
        │            │  เชื่อมความสัมพันธ์
        ▼            ▼
[ RAG Retrieval ]  [ Knowledge Graph ]  (entity: คน/ลูกค้า/สินค้า/process)
        │            │
        ▼            ▼
[ Enterprise Search ]   +   [ AI Knowledge Retrieval / Q&A พร้อม citation ]
```

- **Enterprise Search** — ค้นข้ามทุก module ด้วยภาษาธรรมชาติ เคารพสิทธิ์การเข้าถึง
  (ไม่เห็นเอกสารที่ไม่มีสิทธิ์)
- **Knowledge Graph** — ตอบคำถามเชิงความสัมพันธ์ เช่น "สัญญานี้เกี่ยวกับลูกค้าราย
  ไหน, process ใด, มีความเสี่ยงอะไรผูกอยู่"
- **RAG** — ทุกคำตอบของ AI ต้องอ้างอิงแหล่งที่มา (citation) ป้องกัน hallucination
- **Lessons Learned pipeline** — เมื่อ project/incident จบ ระบบ prompt ให้บันทึก
  บทเรียน → กลายเป็น knowledge ที่ค้นเจอครั้งหน้า (นี่คือกลไก "เรียนรู้")

### Auto / Human
- 🟢 ingest, embed, จัดหมวด, สรุป, ตอบคำถาม (พร้อม citation)
- 🟡 อนุมัติเอกสารเป็น "official SOP / controlled document" (มี version + ผู้อนุมัติ)

---

## Layer 3 — People Layer (Nirva People)

**หน้าที่:** ดูแลวงจรชีวิตพนักงานทั้งหมด และทำให้องค์กร "สอนคนเอง" ได้

### Components & lifecycle

```
Recruitment → Onboarding → Training/Learning → Performance → Career Path
                                                      │
                              Succession Planning ◄───┘   Certification
```

| Module | Auto / Human | หมายเหตุ |
|--------|--------------|----------|
| Recruitment | 🟡 AI คัด resume + สรุป, คนสัมภาษณ์/ตัดสิน | จ้างจริง = 🟠 HUMAN APPROVE |
| Onboarding | 🟢 สร้าง checklist, มอบ training, เปิดสิทธิ์ตาม role | |
| Training / Learning System (LMS) | 🟢 จัด course ตาม role + gap, AI tutor จาก Knowledge Hub | |
| Performance | 🟡 AI รวบ metric/feedback เป็นร่าง, หัวหน้าประเมิน | |
| Career Path | 🟡 แนะนำเส้นทาง+ทักษะที่ขาด | |
| Succession Planning | 🟡 ระบุ key person risk + ผู้สืบทอด | ผูกกับ Risk (L1) |
| Certification System | 🟢 ออก/ต่ออายุ cert, เตือนหมดอายุ | ผูก ISO (L2) |

**จุดเชื่อม:** People ↔ Knowledge (LMS ดึงจาก SOP), People ↔ Governance
(สิทธิ์/authority ผูกกับ role), People ↔ Self-Managing (พนักงานลาออก → trigger
analysis ที่ L10)

---

## Layer 4 — ESG Layer (Nirva Sustainability)

**หน้าที่:** วัดผลกระทบด้านสิ่งแวดล้อม-สังคม จากกิจกรรมจริงในทุก module —
และเปลี่ยนเป็น **คะแนนสะสม** ที่จับต้องได้

### สิ่งที่วัด
Carbon (Scope 1/2/3) · ขยะ/Waste · การใช้พลังงาน · ผลกระทบสิ่งแวดล้อมอื่น ·
กิจกรรมเพื่อสังคม (CSR/อาสา)

### กลไก: ESG เป็น "ผู้ฟัง event"
ESG ไม่ต้องให้คนกรอกซ้ำ — แต่ subscribe event จาก module อื่น แล้วแปลงเป็นผลกระทบ
โดยใช้ **emission factor library**:

```
Procurement: ซื้อของ X กก.      ──► factor ──► CO₂e
Finance: บิลค่าไฟ Y kWh          ──► factor ──► พลังงาน + CO₂e
Fleet/Logistics: วิ่ง Z กม.      ──► factor ──► CO₂e
People: กิจกรรมอาสา N ชม.        ──►        ──► social score
            │
            ▼
   [ ESG Ledger ]  ──►  Sustainability Score (สะสม)  ──►  รายงาน ESG / dashboard
```

### Auto / Human
- 🟢 คำนวณจาก event, สะสมคะแนน, ออก dashboard/รายงาน
- 🟡 ตั้ง factor, ตั้งเป้า, รับรองรายงานก่อนเผยแพร่ภายนอก (🔴 ถ้าต้องมีผู้ทวนสอบตามมาตรฐาน)

---

## Layer 5 — AI Layer (Multi-AI Ecosystem)

**หน้าที่:** เป็นชั้น AI กลางที่ทุก layer เรียกใช้ — **ไม่ผูกกับเจ้าเดียว**
รองรับ OpenAI · Anthropic · Google · DeepSeek · Mistral · Local LLM

### สถาปัตยกรรม

```
        Module ใด ๆ เรียก "ขอความสามารถ AI" (ไม่รู้ว่าเบื้องหลังใช้ใคร)
                                │
                    ┌───────────▼────────────┐
                    │   AI ORCHESTRATOR        │  วางแผนงานหลายขั้น,
                    │   (วางแผน + เรียก agents) │  เรียก tool, รวมผล
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │      AI ROUTER           │  เลือก model ตาม
                    │ (เลือก provider/model)   │  งาน/คุณภาพ/ราคา/นโยบาย
                    └───────────┬────────────┘
        ┌──────────┬───────────┼───────────┬──────────┐
        ▼          ▼           ▼           ▼          ▼
     OpenAI   Anthropic     Google     DeepSeek    Local LLM
        └──────────┴───────────┴───────────┴──────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                         ▼
  AI Cost Control        AI Monitoring             AI Governance
  (budget/quota,         (latency, error,          (PDPA: ข้อมูลไหน
   เลือก model ถูกลง      drift, ใช้เกิน)            ห้ามส่ง cloud →
   เมื่องานง่าย)                                     บังคับ Local LLM)
```

### Components
- **AI Router** — กฎเลือก model: งานความลับสูง → Local; งานง่าย → model ถูก;
  งานคุณภาพสูง → frontier model; มี fallback เมื่อ provider ล่ม
- **AI Orchestrator** — รันงานหลายขั้น เรียก agent หลายตัว เรียก tool (ค้น
  Knowledge, query Finance ฯลฯ)
- **AI Agent Marketplace** — คลัง agent สำเร็จรูป (HR/Finance/ISO/Procurement/
  Research/Executive agent) ที่ติดตั้ง/แชร์/กำหนดสิทธิ์ได้ — สอดคล้องกับ NOVA
  ใน [BEST_GROUP](./BEST_GROUP.md)
- **AI Cost Control** — งบต่อ team/agent, เตือนเมื่อใกล้เพดาน, downgrade model
  อัตโนมัติ, รายงานต้นทุนต่อ business outcome
- **AI Monitoring** — คุณภาพ/latency/error/cost ต่อ provider + ตรวจ quality drift
- **AI Governance** — บังคับ policy จาก L1 (ข้อมูล PDPA ห้ามออก cloud, ต้องมี
  audit log ทุก call, ต้องระบุผู้รับผิดชอบเมื่อ AI ตัดสินผิด)

---

## Layer 6 — Automation Layer (Nirva Automation Engine)

**หน้าที่:** เปลี่ยน "กระบวนการ" ให้รันเองตาม event และ rule โดยมีจุดให้คน
อนุมัติชัดเจน

### รองรับ
Workflow · BPM · Agent Workflow · Event-Driven · Human Approval Flow ·
Escalation · Notification

### โมเดลการทำงาน

```
Trigger (event บน bus / schedule / manual)
   │
   ▼
Workflow steps  ──► step = AUTO (ทำเอง) | AI-AGENT (ให้ agent ทำ)
   │                         | HUMAN-TASK (รอคนทำ)
   │                         | APPROVAL (รออนุมัติ ตาม Authority Matrix)
   │
   ├─ เกินเวลา/วงเงิน? ──► ESCALATION (ดันขึ้นหัวหน้าถัดไป)
   │
   ▼
Notification (อีเมล/แชต/ในระบบ) ทุกจุดสำคัญ + บันทึก Audit (L1)
```

- **Human Approval Flow** ผูกตรงกับ Authority Matrix (L1) — ไม่มีการ approve
  ที่เกินสิทธิ์
- **Escalation** — งานค้างเกิน SLA หรือเกินวงเงิน → ดันขึ้นอัตโนมัติ
- ทุก workflow = controlled document ใน Knowledge Hub (มี version + ผู้อนุมัติ)

---

## Layer 7 — Finance Layer (Nirva Finance)

**หน้าที่:** บริหารการเงินครบวงจร โดยแยกชัดว่าอะไรอัตโนมัติได้ อะไรต้องคน
อะไร**ต้องผู้มีวิชาชีพตามกฎหมาย**

### Module & เส้นแบ่งสิทธิ์ (สำคัญมากตามที่บรีฟไว้)

| Module | ระดับ | คำอธิบาย |
|--------|-------|----------|
| **AP** (เจ้าหนี้/จ่าย) | 🟢 จับคู่บิล-PO-รับของ 3-way match; 🟠 **อนุมัติจ่ายเงินต้องมนุษย์** | AI เตรียม, คนอนุมัติจ่าย |
| **AR** (ลูกหนี้/รับ) | 🟢 ออกใบแจ้งหนี้, reconcile เงินเข้า, ทวงถามอัตโนมัติ | |
| **GL** (บัญชีแยกประเภท) | 🟢 ลง entry จาก transaction; 🟡 ปรับปรุงรายการ manual | |
| **Cashflow** | 🟢 รวบรวม real-time | |
| **Budget** | 🟡 AI เสนอร่าง, ผู้บริหารอนุมัติ | |
| **Forecast** | 🟢 พยากรณ์ด้วย ML; 🟡 คนทบทวนสมมติฐาน | |
| **Cost Center** | 🟢 ปันส่วนต้นทุนอัตโนมัติ | |
| **Project Accounting** | 🟢 รวมรายรับ-รายจ่ายต่อ project | |
| **Tax Support** | 🟡 คำนวณ/เตรียมแบบ; 🔴 **ยื่น/รับรองตามกฎหมาย** | |

### เส้นแบ่งวิชาชีพ (ระบุชัดตามบรีฟ)

| คำถาม | คำตอบ |
|--------|--------|
| อะไร**ทำอัตโนมัติได้** | บันทึกรายการ, 3-way match, reconcile, ออกใบแจ้งหนี้, รายงาน, พยากรณ์ |
| อะไร**ต้องมนุษย์ตรวจ** | อนุมัติจ่ายเงิน, รายการปรับปรุง manual, สมมติฐาน budget/forecast, รายการผิดปกติ |
| อะไร**ต้องผู้ทำบัญชีตามกฎหมาย** | จัดทำ/ปิดงบการเงินตามมาตรฐานบัญชี, ลงนามผู้ทำบัญชี |
| อะไร**ต้องผู้สอบบัญชีตามกฎหมาย** | ตรวจสอบและแสดงความเห็นต่องบการเงิน (ผู้สอบบัญชีรับอนุญาต — เป็นอิสระจากระบบ) |

> หลักการ: AI/ระบบ **เตรียมและตรวจทานเบื้องต้น** ได้ แต่ **ความรับผิดทาง
> กฎหมายและการรับรองตามวิชาชีพ ต้องเป็นมนุษย์ผู้มีคุณสมบัติเสมอ** (ระดับ 🔴)

---

## Layer 8 — Sales Layer (Nirva CRM)

**หน้าที่:** บริหารวงจรขายตั้งแต่ lead จนถึงต่อสัญญา

### Pipeline
```
Lead → Opportunity → Quotation → Proposal → Contract → Customer Success → Renewal
```

| Stage | Auto / Human |
|-------|--------------|
| Lead | 🟢 จับ lead จากทุกช่องทาง, score, แจกจ่าย |
| Opportunity | 🟢 อัปเดต stage, แจ้งเตือน follow-up |
| Quotation | 🟡 AI ร่างตาม pricing rule, sales ตรวจ |
| Proposal | 🟡 AI ร่างจาก template + Knowledge |
| Contract | 🟠 **เซ็นสัญญาต้องมนุษย์** (ผูก Legal L1) |
| Customer Success | 🟢 health score, churn signal → ส่งต่อ L10 |
| Renewal | 🟢 เตือนล่วงหน้า, ร่างข้อเสนอต่ออายุ |

**จุดเชื่อม:** CRM → Finance (quote→invoice), CRM → Self-Managing (churn/ลูกค้า
ลดลง → trigger), CRM → Knowledge (proposal best practice)

---

## Layer 9 — Procurement Layer (Nirva Procurement)

**หน้าที่:** จัดซื้อจัดจ้างโปร่งใส ตรวจสอบได้ มี supplier scorecard

### Flow
```
Vendor Management → Purchase Request → RFQ/RFP → เปรียบเทียบ →
Purchase Order → Approval Workflow → รับของ → Supplier Scorecard
```

| Module | Auto / Human |
|--------|--------------|
| Vendor Management | 🟢 ทะเบียน, เอกสาร, สถานะ |
| RFQ / RFP | 🟢 ส่งคำขอ, รวบรวมข้อเสนอ, เทียบราคา/เงื่อนไข |
| Purchase Request | 🟢 สร้างจากความต้องการ (เช่น restock จาก inventory) |
| Purchase Order | 🟡 AI ร่าง |
| Approval Workflow | 🟠 **อนุมัติตาม Authority Matrix** (วงเงิน) |
| Supplier Scorecard | 🟢 ให้คะแนนจากคุณภาพ/ตรงเวลา/ราคา |

**จุดเชื่อม:** Procurement → Finance (PO→AP 3-way match), → ESG (carbon ของที่
ซื้อ), → Risk (single-source supplier = ความเสี่ยง)

---

## Layer 10 — Self-Managing Company

**หน้าที่:** ชั้นที่ทำให้บริษัท "ดูแลตัวเอง" — วน loop เหนือทุก layer:

```
   SENSE ──► ANALYZE ──► PROPOSE ──► (HUMAN) APPROVE ──► ACT ──► LEARN
     ▲                                                            │
     └────────────────── feedback เข้า Knowledge ◄────────────────┘
```

1. **SENSE** — ฟัง event/metric ทุก layer หา anomaly (เทียบ baseline/เป้า/เทรนด์)
2. **ANALYZE** — AI หาสาเหตุที่เป็นไปได้ ดึงบริบทจาก Knowledge Graph
3. **PROPOSE** — เสนอแผนพร้อมผลกระทบที่ประเมินไว้ (เป็นทางเลือก ไม่ใช่คำสั่ง)
4. **APPROVE** — มนุษย์ตัดสินตาม Authority Matrix (🟠) — **ไม่มีการ act เรื่อง
   สำคัญโดยไม่ผ่านคน**
5. **ACT** — เมื่ออนุมัติ → trigger workflow ใน Automation Engine
6. **LEARN** — บันทึกผลลัพธ์เป็น Lessons Learned ป้อนกลับเข้า Knowledge

### ตัวอย่างสถานการณ์ (ตามบรีฟ)

| สัญญาณ | SENSE | ANALYZE | PROPOSE | APPROVE |
|--------|-------|---------|---------|---------|
| **ลูกค้าลดลง** | active customer ↓ vs baseline | churn กระจุกที่ segment/หลัง incident ใด? | แคมเปญ win-back, แก้ root cause | หัวหน้าขาย/ผู้บริหาร |
| **กำไรลดลง** | margin ↓ MoM | ต้นทุนขึ้น? ราคาตก? mix เปลี่ยน? | ปรับราคา/ลดต้นทุน/เลิกสินค้าขาดทุน | ผู้บริหาร |
| **พนักงานลาออก** | turnover ↑ / key person risk | แผนก/สาเหตุ? เทียบ engagement | retention plan, เร่ง succession | HR + หัวหน้า |
| **ลูกค้าร้องเรียน** | complaint ↑ / CSAT ↓ | สินค้า/process/ช่วงเวลาไหน? | corrective action (ผูก Audit L1) | เจ้าของ process |
| **ต้นทุนเพิ่มขึ้น** | cost ↑ เกิน budget | cost center ไหน? supplier เดียว? | RFQ ใหม่/เจรจา/หา supplier สำรอง | ฝ่ายจัดซื้อ/การเงิน |

> **กฎความปลอดภัย:** L10 มีสิทธิ์ "เสนอ" เสมอ แต่ "ลงมือ" ได้เฉพาะงานระดับ 🟢
> เท่านั้น งานที่กระทบเงิน/คน/สัญญา/กฎหมาย ต้องผ่านมนุษย์ทุกครั้ง

---

## 3. Cross-cutting Concerns

| ด้าน | แนวทาง |
|------|--------|
| **Identity & Access** | SSO, RBAC ผูกกับ role/authority ของ L1; ทุก request ตรวจสิทธิ์ |
| **Audit & Trail** | event ทุกตัวลง immutable store; ตอบได้เสมอว่าใคร/เมื่อไหร่/ทำไม |
| **PDPA / Data Privacy** | จัดชั้นข้อมูล; ข้อมูลส่วนบุคคล/ความลับ → บังคับ Local LLM ผ่าน AI Governance |
| **Multi-tenant** | แยกข้อมูลตามนิติบุคคล/หน่วยธุรกิจในกลุ่ม (ดู BEST_GROUP) |
| **Observability** | metric/log/trace ทั้งระบบ + AI monitoring (L5) |
| **Extensibility** | ทุก module เปิด API + ฟัง event bus → ต่อ module/agent ใหม่ได้โดยไม่แก้แกน |

---

## 4. Roadmap / การทยอยสร้าง

แนะนำสร้างจากรากฐานขึ้นบน ไม่ใช่ทำทุก layer พร้อมกัน:

| Phase | สร้าง | ได้คุณค่าอะไร |
|-------|-------|----------------|
| **0 — Foundation** | Identity, Event Bus, Audit store, L1 Authority Matrix | trust + ความปลอดภัยก่อนเป็นอันดับแรก |
| **1 — Core Platform** | L2 Knowledge Hub + L5 AI Layer + L6 Automation | สมองกลาง + แขนขาที่ module อื่นใช้ร่วม |
| **2 — Business Modules** | L7 Finance, L8 CRM, L9 Procurement, L3 People | งานธุรกิจจริงเริ่มอัตโนมัติ |
| **3 — Sustainability** | L4 ESG (subscribe event ที่มีอยู่แล้ว) | วัดผลกระทบโดยไม่กรอกซ้ำ |
| **4 — Autonomy** | L10 Self-Managing loop | บริษัทเริ่มดูแล/เตือน/เสนอเอง |

> **เหตุผล:** L10 จะ "ฉลาด" ได้ก็ต่อเมื่อมี event/metric/knowledge จาก layer
> ล่างป้อนให้ — จึงต้องสร้างรากฐานก่อน

---

*เอกสารนี้เป็น living document — ปรับปรุงเมื่อสถาปัตยกรรมเปลี่ยน และทุกการ
เปลี่ยนแปลงควรผ่าน review ตามหลัก Governance (L1)*
