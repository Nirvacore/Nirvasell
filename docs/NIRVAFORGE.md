# 🏭 NirvaForge — AI Software Factory

**Blueprint ระดับ Enterprise — โรงงานสร้างซอฟต์แวร์องค์กรด้วย AI Agent แบบครบวงจร**

> วิสัยทัศน์: *"ทำให้การสร้างซอฟต์แวร์องค์กรเร็วขึ้น 10–100 เท่า"* โดยรวม AI
> Agents + Automation + Reusable Modules + Standard Templates + Enterprise
> Architecture + ISO + Knowledge Graph เป็น ecosystem เดียว

เอกสารนี้เป็นคู่กับ [NIRVA_ARCHITECTURE.md](./NIRVA_ARCHITECTURE.md) (แพลตฟอร์ม
ที่ NirvaForge สร้างออกมา) และ [BEST_GROUP.md](./BEST_GROUP.md) (โครงสร้างกลุ่ม)

---

## สารบัญ (ตาม Output Format)

1. [Executive Summary](#1-executive-summary)
2. [Enterprise Architecture](#2-enterprise-architecture-8-layers)
3. [Product Architecture](#3-product-architecture)
4. [AI Agent Architecture](#4-ai-agent-architecture)
5. [Data Architecture](#5-data-architecture)
6. [Security Architecture](#6-security-architecture)
7. [Automation Architecture](#7-automation-architecture)
8. [DevOps Architecture](#8-devops-architecture)
9. [Knowledge Architecture](#9-knowledge-architecture)
10. [Roadmap](#10-roadmap)
11. [Risk Assessment](#11-risk-assessment)
12. [Cost Estimate](#12-cost-estimate)
13. [Team Structure](#13-team-structure)
14. [Revenue Model](#14-revenue-model)
15. [Final Recommendation](#15-final-recommendation)

---

## 1. Executive Summary

**NirvaForge คืออะไร:** แพลตฟอร์มที่รับ *requirement* ของลูกค้า แล้วใช้ทีม AI
Agent + reusable module + template มาตรฐาน ประกอบเป็นระบบองค์กร (ERP, CRM, HRM,
Payroll, Accounting, Procurement, Asset, Workflow, AI Agent, Automation) ได้เร็ว
กว่าการเขียนเองหลายเท่า

**กลไกเร่งความเร็ว 10–100×:**
1. **Reusable Modules** — 70–80% ของระบบองค์กรซ้ำกัน (auth, RBAC, workflow,
   audit, รายงาน, approval) → ประกอบ ไม่เขียนใหม่
2. **Standard Templates** — แต่ละ vertical (ทำความสะอาด/รักษาความปลอดภัย/etc.)
   มี template สำเร็จ → ปรับ 20% ที่เหลือ
3. **AI Agents** — generate code/config/test/doc จาก spec ที่มี structure
4. **Knowledge Graph + ISO** — ความรู้และมาตรฐานฝังอยู่ในระบบ ไม่ต้องสอนซ้ำ

**กลยุทธ์ Go-to-market:** ใช้ **ธุรกิจจริงในกลุ่ม BEST (บริษัททำความสะอาด)** เป็น
beachhead — สร้างของจริง ใช้จริง พิสูจน์จริง → จากนั้นจึงทำเป็น template ขายต่อ
(dogfooding) นี่คือข้อได้เปรียบที่คู่แข่งไม่มี

**Business model (10 ขา):** Internal ERP → SaaS → White Label → Enterprise
License → Managed Service → Consulting → ISO Consulting → AI Consulting →
Workflow Automation → Custom Development (รายละเอียดใน §14)

**คำแนะนำสรุป:** เริ่มแคบ-ลึก (HR/Payroll ของบริษัททำความสะอาด) บนสถาปัตยกรรม
ที่ออกแบบเผื่อ multi-tenant + modular ตั้งแต่วันแรก อย่าสร้างทั้ง 10 product
พร้อมกัน

---

## 2. Enterprise Architecture (8 Layers)

```
┌─ L8 GOVERNANCE ─ นโยบาย, ISO, compliance, authority, audit, AI governance ─┐
├─ L7 SECURITY ─── identity, RBAC/ABAC, encryption, SIEM, DLP, DR ───────────┤
├─ L6 AUTOMATION ─ workflow/BPM, event-driven, human approval, orchestration ┤
├─ L5 AI ───────── multi-LLM router, agent runtime, RAG, memory, cost control┤
├─ L1 BUSINESS ─── process, business rules, KPI, org model (ภาษาธุรกิจ) ──────┤
├─ L2 APPLICATION  modular services: ERP/CRM/HR/Payroll/Acct/Procure/Asset ──┤
├─ L3 DATA ─────── master data, transactional, data lake, search, cache ──────┤
└─ L4 INFRASTRUCTURE ─ k8s, network, storage, message queue, observability ──┘
```

> หมายเหตุ: ลำดับเลข layer ตามโจทย์ (Business=1) แต่เชิงเทคนิค Infra เป็นฐานล่าง
> สุด ส่วน Security/Governance เป็น cross-cutting ที่ครอบทุกชั้น

### L1 — Business Layer
นิยาม **กระบวนการธุรกิจ, business rule, KPI, org model** เป็น metadata ที่ระบบ
อ่านได้ (ไม่ hardcode) — เปลี่ยน process = แก้ config ไม่ใช่แก้ code นี่คือชั้นที่
Business Analyst และ AI Agent ทำงานร่วมกัน

### L2 — Application Layer
**Modular monolith → modular services**: แต่ละ business capability (HR, Payroll,
Accounting, Procurement, Asset, CRM, Workflow) เป็น module ที่มี API ชัดเจน แชร์
core services (auth, workflow, audit, notification, reporting) เริ่มเป็น modular
monolith (deploy ง่าย) แล้วค่อยแยก service เมื่อโตจริง

### L3 — Data Layer
Master Data (single source of truth) + Transactional DB ต่อ tenant + Data Lake
สำหรับ analytics/AI + Search (Elasticsearch/OpenSearch) + Cache (Redis) ดู §5

### L4 — Infrastructure Layer
Kubernetes (container orchestration), object storage (S3/MinIO), message queue
(Kafka/RabbitMQ/NATS), networking/ingress, observability stack (metrics/logs/
traces), IaC ทั้งหมด ดู §8

### L5 — AI Layer
Multi-LLM router (ไม่ผูกเจ้าเดียว), agent runtime, RAG pipeline, agent memory,
tool registry, cost control + monitoring + AI governance ดู §4 และ §9

### L6 — Automation Layer
Workflow/BPM engine, event-driven triggers, human-approval flow (ผูก authority
matrix), agent orchestration, escalation, notification ดู §7

### L7 — Security Layer
Identity, RBAC + ABAC, encryption (at-rest/in-transit), audit trail, backup/DR,
SIEM, DLP, MFA — อิง ISO 27001 / SOC2 / NIST / CIS ดู §6

### L8 — Governance Layer
Policy, ISO management, compliance framework, authority/delegation matrix,
internal audit, AI governance — กำกับว่า "ใครทำอะไรได้ และทุกอย่างตรวจสอบได้"

---

## 3. Product Architecture

### Product Family

| # | Product | หน้าที่ | โมดูลหลัก | กลุ่มลูกค้า | รายได้ |
|---|---------|---------|-----------|-------------|--------|
| 1 | **NirvaCore** | ERP แกนกลาง | HR, Payroll, Accounting, Procurement, Asset, Contract | SME–Enterprise | License/SaaS |
| 2 | **NirvaFlow** | Workflow/BPM + automation | workflow designer, approval, event engine | ทุกกลุ่ม | SaaS/seat |
| 3 | **NirvaAgent** | AI agent platform | agent runtime, marketplace, orchestrator | ทุกกลุ่ม | usage + sub |
| 4 | **NirvaOps** | Operations/site/field mgmt | site, attendance, fleet, QC, dispatch | service biz | SaaS |
| 5 | **NirvaCloud** | Infra/hosting layer | tenancy, deploy, scaling | internal + partner | infra margin |
| 6 | **NirvaDeploy** | CI/CD + provisioning | pipeline, env, release | internal + dev | tooling |
| 7 | **NirvaSell** | Online seller OS *(repo นี้)* | stock, orders, profit, promo, live | แม่ค้าออนไลน์/SME | freemium/SaaS |
| 8 | **NirvaTrade** | B2B commerce/marketplace | catalog, dealer, RFQ | wholesale/dealer | take-rate |
| 9 | **NirvaWealth** | Finance/treasury/budget | cashflow, budget, forecast | finance teams | SaaS |
| 10 | **NirvaInvestOS** | Investment/portfolio mgmt | asset alloc, reporting | holding/investors | AUM/SaaS |

### การเชื่อมต่อกัน (dependency)

```
        NirvaCloud (infra) ── NirvaDeploy (ci/cd)  ← รากฐานทุก product
                  │
   ┌──────────────┼───────────────────────────────┐
   │              │                                │
NirvaCore ◄──► NirvaFlow ◄──► NirvaAgent  ← แกนกลาง (ERP + workflow + AI)
   │              │                                │
   ├─ NirvaOps (ต่อยอด ERP → service ops)           │
   ├─ NirvaSell / NirvaTrade (commerce, ใช้ Core)    │
   └─ NirvaWealth / NirvaInvestOS (finance, ใช้ Core)┘
```

**หลักการ:** NirvaCore + NirvaFlow + NirvaAgent คือ "platform" ที่เหลือเป็น
"vertical application" ที่ build บนแพลตฟอร์มเดียวกัน — นี่คือสิ่งที่ NirvaForge
ผลิตออกมา

---

## 4. AI Agent Architecture

### Pattern กลาง (ทุก agent ใช้ร่วม)

```
Trigger → [Plan] → [Retrieve context: RAG + Knowledge Graph + Memory]
       → [Act: เรียก tools / agent อื่น] → [Verify ตามกฎ/QA]
       → Output + [Human gate ถ้าเข้าเกณฑ์ 🟠/🔴] → [Log + Learn]
```

- **Memory:** short-term (working context ต่อ task) + long-term (vector store
  per-domain) + episodic (ผลลัพธ์/บทเรียนที่ผ่านมา)
- **Tools:** ผ่าน tool registry กลาง (query DB, เรียก API module, สร้างเอกสาร,
  ค้น Knowledge) — มีสิทธิ์ตาม role ของ agent
- **Human gate:** งานกระทบเงิน/คน/กฎหมาย ต้องผ่านมนุษย์เสมอ (ดูระดับสิทธิ์ใน
  NIRVA_ARCHITECTURE §2)

### สเปก Agent ทั้ง 20 ตัว

| Agent | หน้าที่ | Input | Output | Tools หลัก | Memory | KPI | Risk หลัก |
|-------|---------|-------|--------|------------|--------|-----|-----------|
| **CEO** | สังเคราะห์ภาพรวม, เสนอกลยุทธ์ | KPI ทุกฝ่าย, ตลาด | สรุปผู้บริหาร, ทางเลือกเชิงกลยุทธ์ | BI query, Knowledge | long+episodic | คุณภาพการตัดสินใจ, accuracy ของ insight | overreach → ต้อง human approve |
| **COO** | ติดตาม operation, จัดสรรงาน | งาน/SLA/ทรัพยากร | แผนปฏิบัติ, แจ้งคอขวด | workflow, ops data | long | on-time %, utilization | จัดงานผิด → SLA หลุด |
| **HR** | จัดการพนักงาน, นโยบาย HR | คำขอ HR, ข้อมูลพนักงาน | คำตอบ/เอกสาร HR | HRIS, policy KB | long | response time, ความถูกต้อง | ข้อมูลส่วนบุคคล (PDPA) |
| **Payroll** | คำนวณเงินเดือน/ภาษี/ประกันสังคม | เวลา, OT, อัตรา | ร่าง payroll | payroll engine, tax rule | episodic | ความถูกต้อง 100% | ผิด = กระทบกฎหมาย → 🟠 human |
| **Recruiter** | สรรหา/คัดกรอง | JD, resume | shortlist + สรุป | ATS, search | long | time-to-hire, quality | bias ในการคัด |
| **Procurement** | จัดซื้อ, เทียบ supplier | PR, RFQ | ร่าง PO, เปรียบเทียบ | vendor DB, RFQ tool | long | cost saving, lead time | conflict of interest |
| **Finance** | วิเคราะห์การเงิน, budget | GL, cashflow | forecast, variance | finance API | long | forecast accuracy | สมมติฐานผิด |
| **Accounting** | ลงบัญชี, reconcile | transaction | journal entry (ร่าง) | GL, bank feed | episodic | match rate | ปิดงบ = 🔴 ต้องผู้ทำบัญชี |
| **Legal** | ตรวจสัญญา, ความเสี่ยงกม. | contract draft | risk flag, สรุปข้อ | contract KB | long | issue caught | คำแนะนำผิด → 🟠 ทนายตรวจ |
| **ISO** | คุม SOP/มาตรฐาน, เตรียม audit | process, หลักฐาน | gap report, checklist | ISO KB, audit log | long | compliance %, NC ลดลง | หลักฐานไม่ครบ |
| **Data Analyst** | วิเคราะห์ข้อมูลตามคำถาม | คำถาม, dataset | analysis + viz | SQL, notebook | episodic | insight usefulness | ตีความผิด |
| **BI** | dashboard/report อัตโนมัติ | metric def | dashboard, alert | BI engine | long | adoption, freshness | metric นิยามผิด |
| **QA** | ทดสอบซอฟต์แวร์ที่ generate | code, spec | test result, bug | test runner | episodic | defect escape rate | false pass |
| **Security** | เฝ้าระวัง/ตรวจช่องโหว่ | log, scan | alert, finding | SIEM, scanner | long | MTTD/MTTR | alert fatigue |
| **DevOps** | deploy, monitor infra | build, metric | release, scaling | CI/CD, k8s | episodic | uptime, lead time | bad deploy → outage |
| **Software Architect** | ออกแบบจาก requirement | requirement | design, module map | template lib, KG | long | rework ลดลง | over-engineering |
| **UX/UI** | ออกแบบ UI จาก spec | requirement, brand | wireframe/component | design system | long | usability score | inconsistency |
| **Customer Support** | ตอบ/แก้ปัญหาลูกค้า | ticket | reply, resolution | KB, ticketing | long | CSAT, FCR | ตอบผิด → ความเชื่อมั่น |
| **Sales** | จัดการ lead → deal | lead, ประวัติ | quote, follow-up | CRM | long | conversion | over-promise |
| **Marketing** | คอนเทนต์/แคมเปญ | brief, ข้อมูลตลาด | content, แผน | content tool, analytics | long | ROAS, engagement | brand risk |

**Orchestration:** มี **Orchestrator** วางแผนงานข้าม agent (เช่น "สร้าง HR
module" → Software Architect ออกแบบ → UX/UI ทำ UI → DevOps deploy → QA ทดสอบ →
ISO ตรวจมาตรฐาน) โดยทุก agent คุยผ่าน shared task/event bus

---

## 5. Data Architecture

### Master Data Model (conceptual)

```
                         ┌──────────────┐
                         │ Organization │
                         └──────┬───────┘
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                   ▼
        ┌──────────┐      ┌──────────┐        ┌──────────┐
        │ Employee │      │  Site    │        │  Asset   │
        └────┬─────┘      └────┬─────┘        └────┬─────┘
             │   assigned-to   │   located-at      │
             └────────┬────────┴───────┬───────────┘
                      ▼                 ▼
                 ┌──────────┐     ┌──────────┐
                 │ Project  │◄────│ Contract │
                 └────┬─────┘     └────┬─────┘
                      │ for             │ with
              ┌───────┴───────┐   ┌─────┴──────┐
              ▼               ▼   ▼            ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Customer │    │ Document │    │  Vendor  │
        └──────────┘    └──────────┘    └──────────┘
```

### Entity หลัก & ความสัมพันธ์

| Entity | คีย์ความสัมพันธ์ |
|--------|------------------|
| **Employee** | สังกัด Org/Department; assigned-to Site/Project; มี payroll/attendance/cert |
| **Customer** | มี Contract; เชื่อม Project/Site; มี ticket/invoice |
| **Vendor** | มี Contract/PO; มี scorecard |
| **Contract** | ผูก Customer **หรือ** Vendor; มี Document; มีวันหมดอายุ/ภาระผูกพัน |
| **Site** | ของ Customer; มี Employee ประจำ; มี Asset; ผูก Project |
| **Asset** | located-at Site; assigned-to Employee/Project; มี maintenance |
| **Project** | for Customer; ใช้ Employee/Asset/Site; มี Document/cost |
| **Document** | polymorphic — แนบกับ entity ใดก็ได้; เข้า Knowledge (RAG) |

### หลักการ Data
- **Single source of truth** สำหรับ master data; module อื่นอ้าง id ไม่ copy
- **Multi-tenant isolation** — แยกข้อมูลตาม tenant (schema/row-level + encryption key แยก)
- **Event-sourced audit** — ทุกการเปลี่ยนแปลงเป็น event (append-only) → ตรวจสอบย้อนได้
- **Data lake** สำหรับ analytics/AI แยกจาก transactional (ไม่ให้ analytics กระทบ OLTP)
- **PDPA/GDPR by design** — tag ข้อมูลส่วนบุคคล, รองรับ right-to-erasure, data residency

---

## 6. Security Architecture

อ้างอิง **ISO 27001 · SOC2 · NIST CSF · CIS Controls**

| ด้าน | การออกแบบ |
|------|-----------|
| **Identity / MFA** | SSO (OIDC/SAML), MFA บังคับ role สำคัญ, passwordless option |
| **RBAC** | สิทธิ์ตาม role (มาตรฐาน, ง่ายต่อการกำกับ) |
| **ABAC** | เงื่อนไขเชิง attribute (เช่น เห็นได้เฉพาะ site ที่รับผิดชอบ, ในเวลางาน) — ใช้คู่ RBAC |
| **Encryption** | at-rest (AES-256, key ต่อ tenant via KMS), in-transit (TLS 1.3) |
| **Audit Trail** | immutable, hash-chained, ครอบคลุมทั้ง human + AI action |
| **Backup** | automated, encrypted, ทดสอบ restore สม่ำเสมอ (3-2-1) |
| **Disaster Recovery** | กำหนด RTO/RPO ต่อ tier, multi-AZ/region, runbook + ซ้อม |
| **SIEM** | รวม log → ตรวจจับ anomaly → alert (Security Agent) |
| **DLP** | ป้องกันข้อมูลรั่ว (โดยเฉพาะข้อมูลที่ห้ามส่ง LLM cloud → บังคับ local model) |

**AI-specific security:** prompt-injection guard, ตรวจ output ก่อน act, จำกัด
tool scope ต่อ agent, ห้ามส่งข้อมูลชั้นความลับออก cloud (ผ่าน AI Governance)

---

## 7. Automation Architecture

### เลือกเครื่องมือตามประเภทงาน

| เครื่องมือ | เหมาะกับ | ข้อดี | ข้อเสีย |
|-----------|----------|-------|---------|
| **n8n** | integration กลาง-ยาก, self-host, มี logic | open-source, self-host, ขยาย node เองได้, คุมข้อมูล | ต้องดูแล infra เอง |
| **Make** | automation เชิงภาพ ปานกลาง | UI ดี, connector เยอะ | cloud-only, ราคาตาม operation |
| **Zapier** | งานง่าย เชื่อม SaaS ยอดนิยม เร็ว | connector มากสุด, เริ่มไว | แพงเมื่อ scale, logic จำกัด |
| **Temporal** | workflow ยาว/สำคัญ ที่ต้อง reliable (payroll run, provisioning) | durable execution, retry/state ในตัว, code-first | ต้องเขียน code, learning curve |
| **Windmill** | internal tools + script orchestration | รัน script (Py/TS) เป็น workflow, self-host, เร็ว | community เล็กกว่า |

### หลักการเลือก (สำหรับ NirvaForge)
- **งาน mission-critical, long-running, ต้องการความถูกต้องสูง** (payroll, billing,
  customer provisioning) → **Temporal** (durable, ตรวจสอบได้)
- **integration ทั่วไป + business workflow** → **n8n** (self-host, คุมข้อมูล PDPA)
- **internal script/automation ของทีม** → **Windmill**
- **Make/Zapier** → ใช้เฉพาะ edge เชื่อม SaaS ภายนอกเร็ว ๆ ไม่ใช่แกนหลัก

> **คำแนะนำ:** แกนหลัก = Temporal + n8n (self-host, ควบคุมข้อมูลได้) ส่วน
> Make/Zapier เป็น optional connector ไม่ผูกธุรกิจหลักไว้กับ vendor cloud

---

## 8. DevOps Architecture

### Pipeline

```
Requirement → Design → Coding → Testing → Security Scan → Staging
   → Production → Monitoring → Incident Response → (feedback) → Requirement
```

| ขั้น | ทำอะไร | ใคร/Agent |
|------|--------|-----------|
| **Requirement** | เก็บ requirement → spec มี structure (อ่านได้โดยเครื่อง) | BA + Software Architect Agent |
| **Design** | ออกแบบ module/data/API จาก template | Software Architect + UX/UI Agent |
| **Coding** | generate จาก template + reusable module, คนรีวิว | dev + agents |
| **Testing** | unit/integration/e2e อัตโนมัติ | QA Agent + CI |
| **Security Scan** | SAST, dependency scan, secret scan, container scan | Security Agent + CI |
| **Staging** | deploy env เหมือน prod, UAT | DevOps Agent |
| **Production** | deploy แบบ progressive (canary/blue-green), rollback ได้ | DevOps Agent + human approve 🟠 |
| **Monitoring** | metrics/logs/traces, SLO, alert | observability + Security Agent |
| **Incident Response** | detect → triage → mitigate → postmortem → Lessons Learned | on-call + agents |

### หลักการ
- **GitOps + IaC** — ทุกอย่างเป็น code, environment reproducible
- **Quality gate** — code ที่ AI generate ต้องผ่าน test + security scan + human
  review ก่อน merge (AI ช่วย ไม่ใช่ AI ปล่อยตรงขึ้น prod)
- **Progressive delivery** — canary/feature flag ลดความเสี่ยง
- **Postmortem → Knowledge** — ทุก incident กลายเป็นบทเรียนที่ค้นเจอครั้งหน้า

---

## 9. Knowledge Architecture

ใช้ **RAG + Vector DB + Knowledge Graph + AI Memory** (+ NotebookLM-style Q&A)

```
แหล่ง: SOP · ISO · คู่มือ · สัญญา · เอกสาร HR/บัญชี/ลูกค้า
   │  ingest → chunk → embed → จัด metadata + สิทธิ์ (อัตโนมัติ)
   ▼
[Vector DB]  ◄──เชื่อม──►  [Knowledge Graph (entity/ความสัมพันธ์)]
   │                              │
   ▼                              ▼
[RAG retrieval (มี citation)]  [graph query (เชิงความสัมพันธ์)]
   │                              │
   └──────────────┬───────────────┘
                  ▼
   AI Agents ทุกตัว + Enterprise Search  ← "ไม่ต้องสอนซ้ำ"
```

- **ไม่ต้องสอนซ้ำ:** เอกสารองค์กรเข้า pipeline ครั้งเดียว → ทุก agent หยิบใช้ได้
  ทันที (เคารพสิทธิ์การเข้าถึง)
- **Citation บังคับ:** ทุกคำตอบอ้างแหล่ง → ตรวจสอบได้ ลด hallucination
- **Per-tenant isolation:** knowledge ของลูกค้าแต่ละราย/แต่ละบริษัทแยกขาดกัน
- **Lessons Learned loop:** ผลงาน/incident/postmortem ป้อนกลับเป็น knowledge ใหม่

---

## 10. Roadmap

จัดด้วย MoSCoW (Must / Should / Could / Future)

| ช่วง | Must Have | Should Have | Could Have | Future Vision |
|------|-----------|-------------|------------|----------------|
| **12 เดือน** | Foundation (auth, RBAC, audit, multi-tenant) + **HR/Payroll/Attendance/Site** สำหรับบริษัททำความสะอาด (ใช้จริง) + NirvaFlow workflow แกน | Contract & Asset mgmt, BI dashboard, 3–4 agent แรก (HR/Payroll/ISO/Support) | mobile app ภาคสนาม | — |
| **24 เดือน** | NirvaCore ครบ (Accounting, Procurement) + ทำ template ขาย (SaaS ตัวแรก) + agent platform (NirvaAgent) | white-label, vertical ที่ 2 | marketplace agent | — |
| **36 เดือน** | multi-vertical SaaS, NirvaForge generate ระบบจาก requirement ได้จริง (semi-auto) | enterprise license, managed service | partner ecosystem | — |
| **60 เดือน** | platform โตเต็ม, self-service NirvaForge | global/multi-region | — | autonomous software factory + investOS เต็มรูป |

> **ลำดับสำคัญ:** อย่าทำ product ทั้ง 10 พร้อมกัน — เริ่ม HR/Payroll ของธุรกิจ
> จริง → พิสูจน์ → templatize → ขยาย

---

## 11. Risk Assessment

| ความเสี่ยง | ผลกระทบ | การลด |
|-----------|---------|-------|
| **Over-scope** (ทำ 10 product พร้อมกัน) | สูง — เผาเงิน ไม่เสร็จสักอย่าง | beachhead เดียวก่อน (cleaning HR/Payroll), MoSCoW เข้ม |
| **AI ผิดพลาดในงานกฎหมาย/การเงิน** | สูง — รับผิดทางกฎหมาย | human gate 🟠/🔴, citation, audit, QA agent |
| **Vendor lock-in (LLM/cloud)** | กลาง | multi-LLM router, self-host option, abstraction layer |
| **Data privacy (PDPA/GDPR)** | สูง | privacy-by-design, local LLM สำหรับข้อมูลลับ, DLP |
| **Security breach** | สูง | ISO 27001 controls, SIEM, encryption, ซ้อม DR |
| **Code ที่ AI generate มีบั๊ก/ช่องโหว่** | กลาง-สูง | quality gate (test+scan+review) ก่อน prod เสมอ |
| **Key person dependency** | กลาง | succession plan, documentation, knowledge hub |
| **Market/adoption** | กลาง | dogfood ในกลุ่มก่อน, ขายเมื่อพิสูจน์แล้ว |

---

## 12. Cost Estimate

> ประมาณการเชิงโครงสร้าง (order-of-magnitude) — ตัวเลขจริงขึ้นกับขนาดทีม/ประเทศ

| หมวด | 12 เดือนแรก | หมายเหตุ |
|------|-------------|----------|
| **คน (ทีม core)** | สัดส่วนสูงสุด (60–70%) | 6–10 คน (ดู §13) |
| **Infrastructure** | ต่ำ-กลาง | เริ่ม managed k8s + self-host บางส่วน, scale ตามใช้จริง |
| **LLM / AI API** | ผันแปร | คุมด้วย AI Cost Control + downgrade model + local LLM งานปริมาณมาก |
| **เครื่องมือ/license** | ต่ำ | เน้น open-source (n8n, Temporal, Postgres, k8s) |
| **Security/compliance** | กลาง (ปีหลัง) | audit ISO/SOC2 เมื่อเริ่มขาย enterprise |

**กลยุทธ์คุมต้นทุน:** open-source-first, self-host สิ่งที่คุมข้อมูลสำคัญ, จ่าย
SaaS เฉพาะที่ ROI ชัด, ใช้ reusable module ลดเวลา dev (ต้นทุนคนคือก้อนใหญ่สุด)

---

## 13. Team Structure

**ทีม core 6–10 คน (ตามวิสัยทัศน์ "คนน้อย AI เสริม"):**

| บทบาท | จำนวน | รับผิดชอบ |
|-------|-------|-----------|
| **Founder/CTO** | 1 | สถาปัตยกรรม, ทิศทาง, การตัดสินใจ |
| **Full-stack/Platform Eng** | 2–3 | core platform, module, integration |
| **AI/ML Engineer** | 1–2 | agent runtime, RAG, router, prompt/eval |
| **DevOps/SRE** | 1 | infra, CI/CD, security ops |
| **Product/BA** | 1 | requirement, process, ลูกค้า (เริ่มจาก cleaning biz) |
| **Domain expert (part-time/ที่ปรึกษา)** | — | บัญชี (ผู้ทำบัญชี), กฎหมาย, ISO — เรียกตามจำเป็น |

**ปรัชญา:** AI Agents ทำงานซ้ำ คนโฟกัสการตัดสินใจ/ออกแบบ/ความสัมพันธ์/ความรับ
ผิดชอบตามกฎหมาย — ขยายทีมเมื่อรายได้พิสูจน์แล้วเท่านั้น

---

## 14. Revenue Model

10 ขารายได้ จัดเป็น 3 กลุ่มตามจังหวะเข้าตลาด:

| กลุ่ม | ขารายได้ | จังหวะ |
|-------|----------|--------|
| **A. พิสูจน์ก่อน (ปีที่ 1)** | 1) Internal ERP (ใช้เองในกลุ่ม BEST) | dogfood — ลดต้นทุน + พิสูจน์ของ |
| **B. ขยายเชิงพาณิชย์ (ปี 2–3)** | 2) SaaS · 3) White Label · 4) Enterprise License · 9) Workflow Automation · 10) Custom Development | รายได้ recurring + project |
| **C. บริการมูลค่าสูง (ปี 2+)** | 5) Managed Service · 6) Consulting · 7) ISO Consulting · 8) AI Consulting | margin สูง, ผูกลูกค้า, feed กลับเป็น template |

**Flywheel:** ทำของจริงในกลุ่ม → templatize → ขาย SaaS/white-label → consulting
+ managed service สร้างรายได้สูงและ requirement ใหม่ → ป้อนกลับเป็น module/agent
ใหม่ใน NirvaForge → ขายได้มากขึ้น

---

## 15. Final Recommendation

1. **เริ่มแคบ-ลึก ไม่กว้าง-ตื้น:** Phase 1 ทำ **HR + Payroll + Attendance + Site
   Management** ของบริษัททำความสะอาดให้ใช้งานจริง — เพราะเป็นงานที่เจ็บปวดที่สุด,
   ทำซ้ำทุกเดือน, มีกฎหมายชัด (พิสูจน์ความถูกต้องได้), และเป็น data รากของทุก
   module ต่อไป

   **ลำดับ module แนะนำ (Phase 1):**
   `Attendance → Payroll → HR → Site/Contract → Asset → Procurement →
   Accounting → KPI/Audit`
   *(เหตุผล: ต้องมีข้อมูลเวลาก่อนคิดเงินเดือนได้; HR/Site เป็น master data;
   Accounting/Audit มาทีหลังเมื่อมี transaction พอ)*

2. **สร้างบนสถาปัตยกรรม multi-tenant + modular ตั้งแต่วันแรก** — แม้จะใช้ภายใน
   ก่อน เพื่อให้ templatize ขายต่อได้โดยไม่ต้องเขียนใหม่

3. **AI ช่วย ไม่ใช่ AI แทน** — งานกระทบเงิน/คน/กฎหมายผ่าน human gate เสมอ; ปิดงบ/
   สอบบัญชี = มนุษย์ผู้มีวิชาชีพ (🔴)

4. **Open-source-first + multi-LLM** — คุมต้นทุนและหลีกเลี่ยง vendor lock-in;
   self-host สิ่งที่กระทบข้อมูลสำคัญ (PDPA)

5. **Tech stack แนะนำ (สรุปจาก Phase 5):**
   - **Frontend:** **Next.js** (React, SSR/SSG, ecosystem ใหญ่, เหมาะ enterprise
     app + SEO หน้า public) — เหนือ Vue/Nuxt/Angular ในแง่ talent pool + ecosystem
   - **Backend:** **NestJS** (TypeScript, โครงสร้าง enterprise ชัด, แชร์ภาษากับ
     frontend) เป็นแกน + **FastAPI** สำหรับงาน AI/ML (Python ecosystem) — สอง
     ภาษาแบบมีเหตุผล ไม่ใช่กระจัดกระจาย
   - **Database:** **PostgreSQL** (มาตรฐาน enterprise, JSONB, row-level security
     สำหรับ multi-tenant, extension เยอะ) — เหนือ MySQL/SQL Server/Oracle ในแง่
     ราคา-ความสามารถ-open source
   - **Cache:** Redis · **Search:** OpenSearch (open-source, เลี่ยง license ของ
     Elasticsearch) · **Storage:** MinIO (self-host) / S3 (cloud) ·
     **Message Queue:** **Kafka** สำหรับ event backbone ปริมาณสูง + **NATS**
     สำหรับ messaging เบา/เร็ว (RabbitMQ เป็น option ถ้าทีมคุ้นกว่า)

6. **อย่าขายก่อนพิสูจน์** — ใช้ flywheel: dogfood → templatize → SaaS →
   consulting/managed service

> **บรรทัดเดียว:** สร้าง NirvaForge เป็น "แพลตฟอร์มที่ผลิตแพลตฟอร์ม" โดยเริ่มจาก
> แก้ปัญหาจริงของบริษัทในกลุ่มก่อน แล้วเปลี่ยนทุกสิ่งที่เรียนรู้ให้กลายเป็น
> reusable asset ที่ขายซ้ำได้

---

*Living document — ปรับปรุงเมื่อสถาปัตยกรรม/กลยุทธ์เปลี่ยน*
