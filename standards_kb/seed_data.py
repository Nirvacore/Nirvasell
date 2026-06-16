"""Generate the standards_kb/data/ JSON layer from the documented matrices.

Run once after clone, or when refreshing the seed dataset::

    python -m standards_kb.seed_data

The generated files power ``python -m standards_kb.graph`` validation and the
Standards browser page in nirva.sell.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

DOMAINS = [
    ("L1", "Governance & Strategy", []),
    ("L2", "Risk Management", ["ISO31000"]),
    ("L3", "Finance & Accounting", ["COSOIC", "SOX"]),
    ("L4", "People & HR", ["ISO9001"]),
    ("L5", "Financial Controls", ["COSOIC"]),
    ("L6", "Operations & Quality", ["ISO9001"]),
    ("L7", "Asset Management", ["ISO55001"]),
    ("L8", "Customer & Product", ["ISO9001"]),
    ("L9", "Supply Chain & Procurement", ["ISO37001"]),
    ("L10", "Environment", ["ISO14001"]),
    ("L11", "Occupational Health & Safety", ["ISO45001"]),
    ("L12", "Information Security", ["ISO27001"]),
    ("L13", "Privacy & Data Protection", ["GDPR"]),
    ("L14", "AI & Algorithm Governance", ["ISO42001"]),
    ("L15", "Knowledge & Documentation", ["ISO9001"]),
    ("L16", "IT Service & Change", ["ITIL"]),
    ("L17", "ESG & Sustainability", ["ESRS"]),
    ("L18", "Audit & Assurance", ["ISO19011"]),
    ("L19", "Business Continuity & Resilience", ["ISO22301"]),
    ("L20", "Legal & Regulatory Compliance", ["GDPR"]),
]

REQUIREMENTS = [
    ("REQ-POLICY", "Policy", "5.2", 0.92,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "NISTCSF", "GDPR"]),
    ("REQ-RACI", "Roles, Responsibilities & Authorities", "5.3", 0.90,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "ITIL", "NISTCSF", "GDPR"]),
    ("REQ-CONTEXT", "Context & Interested Parties", "4.1-4.2", 0.95,
     ["ISO9001", "ISO27001", "ISO42001"]),
    ("REQ-RISK", "Risk Assessment", "6.1", 0.85,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "NISTCSF", "GDPR"]),
    ("REQ-OBJECTIVES", "Objectives & Planning", "6.2", 0.91,
     ["ISO9001", "ISO27001", "ISO42001", "COBIT"]),
    ("REQ-COMPETENCE", "Competence", "7.2", 0.93,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2"]),
    ("REQ-AWARENESS", "Awareness & Training", "7.3", 0.88,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "NISTCSF", "GDPR"]),
    ("REQ-COMM", "Communication", "7.4", 0.86,
     ["ISO9001", "ISO27001", "ISO42001", "ITIL", "NISTCSF"]),
    ("REQ-DOC", "Documented Information", "7.5", 0.94,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "ITIL"]),
    ("REQ-OPS", "Operational Planning & Control", "8.1", 0.80,
     ["ISO9001", "ISO27001", "ISO42001", "ITIL"]),
    ("REQ-MONITOR", "Monitoring, Measurement & KPI", "9.1", 0.84,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "ITIL", "NISTCSF"]),
    ("REQ-EVIDENCE", "Evidence / Records of Conformity", "9.1/7.5", 0.82,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "GDPR"]),
    ("REQ-AUDIT", "Internal Audit", "9.2", 0.90,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT"]),
    ("REQ-MGMTREVIEW", "Management Review", "9.3", 0.93,
     ["ISO9001", "ISO27001", "ISO42001"]),
    ("REQ-NC", "Nonconformity & Corrective Action", "10.2", 0.91,
     ["ISO9001", "ISO27001", "ISO42001", "SOC2", "ITIL"]),
    ("REQ-CI", "Continual Improvement", "10.1/10.3", 0.89,
     ["ISO9001", "ISO27001", "ISO42001", "COBIT", "ITIL"]),
    ("REQ-INCIDENT", "Incident / Event Management", "8.x", 0.78,
     ["ISO27001", "SOC2", "ITIL", "NISTCSF", "GDPR"]),
    ("REQ-TPDD", "Third-Party Due Diligence", "8.x", 0.76,
     ["ISO27001", "SOC2", "GDPR"]),
    ("REQ-IMPACT", "Impact Assessment (DPIA/AIA)", "6.1.x", 0.72,
     ["ISO42001", "GDPR"]),
]

CONTROLS = [
    ("UC-IM", "Incident Management", ["L12", "L19", "L6"],
     ["REQ-INCIDENT", "REQ-COMM", "REQ-NC"],
     {"ISO27001": "A.5.24-A.5.28", "ISO22301": "8.4", "SOC2": "CC7.3-CC7.5",
      "NISTCSF": "RS,DE", "NIST80053": "IR family", "GDPR": "Art.33-34",
      "NIS2": "Art.23", "DORA": "Ch.III", "ITIL": "Incident Mgmt"}),
    ("UC-AC", "Access Control & Identity Management", ["L12", "L13", "L4"],
     ["REQ-RACI", "REQ-DOC", "REQ-MONITOR"],
     {"ISO27001": "A.5.15-A.5.18", "NIST80053": "AC family", "SOC2": "CC6.1-CC6.3",
      "PCIDSS": "Req 7,8", "CISV8": "Control 5,6", "GDPR": "Art.32",
      "NISTCSF": "PR.AA", "HIPAA": "164.312(a)"}),
    ("UC-TRN", "Training & Competence Management", ["L4", "L15"],
     ["REQ-COMPETENCE", "REQ-AWARENESS", "REQ-DOC"],
     {"ISO9001": "7.2-7.3", "ISO27001": "7.2-7.3", "ISO45001": "7.2-7.3",
      "ISO42001": "7.2", "SOC2": "CC1.4", "PCIDSS": "Req 12.6",
      "GDPR": "Art.39", "NIST80053": "AT family"}),
    ("UC-RM", "Risk Management", ["L2", "L1"],
     ["REQ-RISK", "REQ-OBJECTIVES", "REQ-MONITOR", "REQ-IMPACT"],
     {"ISO31000": "full", "ISO27001": "6.1.2-6.1.3", "ISO22301": "6.1",
      "COSOERM": "full", "NISTCSF": "GV.RM,ID.RA", "NIST80053": "RA family",
      "NISTAIRMF": "Map/Measure", "EUAIACT": "Art.9"}),
    ("UC-ESG", "ESG & Sustainability Disclosure", ["L17", "L1", "L18"],
     ["REQ-CONTEXT", "REQ-MONITOR", "REQ-EVIDENCE", "REQ-MGMTREVIEW"],
     {"ESRS": "full", "GRISTD": "full", "IFRSS1": "full", "IFRSS2": "full",
      "SASBSTD": "metrics", "CSRD": "ref", "TNFDREC": "LEAP", "ISO26000": "guidance"}),
    ("UC-CM", "Change Management", ["L6", "L16", "L12"],
     ["REQ-OPS", "REQ-DOC", "REQ-INCIDENT"],
     {"ISO27001": "A.8.32", "ISO9001": "8.5.6", "ISO20000": "8.5.1",
      "SOC2": "CC8.1", "ITIL": "Change Enablement", "COBIT": "BAI06",
      "PCIDSS": "Req 6.5"}),
    ("UC-SUP", "Supplier & Third-Party Management", ["L9", "L2", "L12"],
     ["REQ-TPDD", "REQ-RISK", "REQ-MONITOR"],
     {"ISO27001": "A.5.19-A.5.23", "ISO9001": "8.4", "SOC2": "CC9.2",
      "NIST800171": "3.x supply chain", "DORA": "Art.28-30",
      "CSACCM": "STA domain", "ISO37001": "8.x"}),
    ("UC-PM", "Privacy Management & Data Subject Rights", ["L13", "L20", "L8"],
     ["REQ-IMPACT", "REQ-DOC", "REQ-COMM", "REQ-EVIDENCE"],
     {"ISO27701": "full", "GDPR": "Art.12-23", "PDPA_TH": "full",
      "PDPA_SG": "full", "CCPA": "full", "NISTPF": "Control-P", "HIPAA": "Privacy Rule"}),
    ("UC-AUD", "Internal Audit & Management Review", ["L18", "L1", "L16"],
     ["REQ-AUDIT", "REQ-MGMTREVIEW", "REQ-NC", "REQ-CI"],
     {"ISO19011": "full", "ISO9001": "9.2-9.3", "ISO27001": "9.2-9.3",
      "SOC2": "CC4.1", "SOX": "404", "COBIT": "MEA02", "COSOIC": "Monitoring"}),
    ("UC-DOC", "Documented Information / Document Control", ["L15", "L6", "L18"],
     ["REQ-DOC", "REQ-EVIDENCE"],
     {"ISO9001": "7.5", "ISO27001": "7.5", "ISO13485": "4.2",
      "SOC2": "CC2.1", "COBIT": "BAI08", "NIST80053": "DM/PM"}),
    ("UC-AM", "Asset Management & Inventory", ["L7", "L12"],
     ["REQ-DOC", "REQ-RACI", "REQ-MONITOR"],
     {"ISO27001": "A.5.9-A.5.14", "ISO55001": "full", "CISV8": "Control 1,2",
      "NIST80053": "CM-8", "NISTCSF": "ID.AM", "SOC2": "CC6.1"}),
    ("UC-BCM", "Business Continuity & Resilience", ["L19", "L2", "L6"],
     ["REQ-RISK", "REQ-OPS", "REQ-INCIDENT", "REQ-MONITOR"],
     {"ISO22301": "full", "ISO27001": "A.5.29-A.5.30", "SOC2": "A1.2-A1.3",
      "NISTCSF": "RC", "DORA": "Art.11-12", "NIST80053": "CP family"}),
    ("UC-AIG", "AI Governance & Model Lifecycle", ["L14", "L1", "L2"],
     ["REQ-IMPACT", "REQ-RISK", "REQ-RACI", "REQ-MONITOR", "REQ-DOC"],
     {"ISO42001": "full", "NISTAIRMF": "full", "EUAIACT": "Art.9-15",
      "ISO23894": "full", "OECDAI": "principles", "OWASPLLM": "LLM01-10"}),
    ("UC-DG", "Data Governance & Classification", ["L13", "L12", "L15"],
     ["REQ-DOC", "REQ-RACI", "REQ-MONITOR"],
     {"ISO27001": "A.5.12-A.5.13", "ISO27701": "full", "COBIT": "APO14",
      "GDPR": "Art.5", "NIST80053": "DM"}),
    ("UC-LOG", "Logging, Monitoring & Detection", ["L12", "L18", "L19"],
     ["REQ-MONITOR", "REQ-EVIDENCE", "REQ-INCIDENT"],
     {"ISO27001": "A.8.15-A.8.16", "SOC2": "CC7.1-CC7.2", "PCIDSS": "Req 10",
      "NIST80053": "AU family", "NISTCSF": "DE.CM", "CISV8": "Control 8"}),
    ("UC-CRYPTO", "Cryptography & Key Management", ["L12", "L13"],
     ["REQ-OPS", "REQ-DOC"],
     {"ISO27001": "A.8.24", "NIST80053": "SC-12,SC-13", "PCIDSS": "Req 3,4",
      "TLS13": "ref", "SOC2": "CC6.1", "GDPR": "Art.32"}),
    ("UC-VULN", "Vulnerability & Patch Management", ["L12", "L6"],
     ["REQ-RISK", "REQ-OPS", "REQ-MONITOR"],
     {"ISO27001": "A.8.8", "NIST80053": "RA-5,SI-2", "PCIDSS": "Req 6,11",
      "CISV8": "Control 7", "NISTCSF": "ID.RA,PR.PS", "SOC2": "CC7.1"}),
    ("UC-ENV", "Environmental & Energy Management", ["L10", "L17", "L6"],
     ["REQ-CONTEXT", "REQ-OBJECTIVES", "REQ-MONITOR", "REQ-CI"],
     {"ISO14001": "full", "ISO50001": "full", "GHGP_CORP": "ref",
      "ESRS": "E1-E5", "IFRSS2": "metrics"}),
    ("UC-OHS", "Occupational Health & Safety", ["L11", "L4", "L6"],
     ["REQ-RISK", "REQ-COMPETENCE", "REQ-INCIDENT", "REQ-OPS"],
     {"ISO45001": "full", "TISI_OHS": "ref", "ISO22000": "safety prereq",
      "ESRS": "S1", "NFPA": "life-safety"}),
    ("UC-FIN", "Financial Controls & ICFR", ["L5", "L3", "L18"],
     ["REQ-EVIDENCE", "REQ-MONITOR", "REQ-AUDIT"],
     {"COSOIC": "full", "SOX": "302,404", "SOC1": "full",
      "IFRS_ACC": "ref", "COBIT": "align"}),
]

EVIDENCE = [
    ("EV-POLICY", "Approved Policy Document (versioned, signed)",
     ["UC-AC", "UC-CM", "UC-RM", "UC-PM", "UC-AIG", "UC-ESG"], True),
    ("EV-RACI", "Roles/RACI & Org Chart with control ownership",
     ["UC-AC", "UC-RM", "UC-AIG", "UC-DG"], True),
    ("EV-RISKREG", "Risk Register with assessments & treatments",
     ["UC-RM", "UC-SUP", "UC-BCM", "UC-AIG", "UC-VULN"], True),
    ("EV-TRAINLOG", "Training completion & awareness records", ["UC-TRN"], True),
    ("EV-ACCESSREVIEW", "Periodic access review / recertification logs",
     ["UC-AC", "UC-LOG"], True),
    ("EV-CHANGETICKET", "Change tickets with approvals & rollback",
     ["UC-CM", "UC-VULN"], True),
    ("EV-INCIDENT", "Incident/breach records with timeline & RCA",
     ["UC-IM", "UC-BCM", "UC-LOG"], True),
    ("EV-VENDORDD", "Vendor due-diligence & contracts (DPA/SLAs)",
     ["UC-SUP", "UC-PM"], True),
    ("EV-LOGS", "System/audit logs (retained, tamper-evident)",
     ["UC-LOG", "UC-AC", "UC-IM"], True),
    ("EV-SCAN", "Vulnerability scan & pen-test reports",
     ["UC-VULN", "UC-CRYPTO"], True),
    ("EV-AUDITREPORT", "Internal audit reports & management review minutes",
     ["UC-AUD", "UC-FIN"], False),
    ("EV-DSAR", "DSAR/consent records & RoPA (Art.30)",
     ["UC-PM", "UC-DG"], True),
    ("EV-MODELCARD", "Model card, AI impact assessment & eval results",
     ["UC-AIG"], True),
    ("EV-BCPTEST", "BC/DR test & exercise results, RTO/RPO evidence",
     ["UC-BCM"], False),
    ("EV-GHG", "GHG inventory & ESG data with assurance trail",
     ["UC-ENV", "UC-ESG"], True),
    ("EV-FINCTRL", "ICFR control evidence (reconciliations, approvals)",
     ["UC-FIN", "UC-AUD"], True),
    ("EV-ASSETINV", "Asset/CMDB inventory with classification",
     ["UC-AM", "UC-DG"], True),
    ("EV-HAZARD", "Hazard assessments & safety incident logs", ["UC-OHS"], False),
]

CONFLICTS = [
    {"id": "CON-LOCALIZATION-GLOBAL", "standards": ["GDPR", "CSRD"],
     "summary": "Data must stay in-region vs global analytics graph",
     "resolution": "Regional data planes with global metadata only"},
    {"id": "CON-RETENTION-RTBF", "standards": ["GDPR", "SOX"],
     "summary": "Erasure rights vs mandatory retention for audit",
     "resolution": "Legal-hold workflow with pseudonymization"},
    {"id": "CON-COMPLIANCE-INNOVATION", "standards": ["SOC2", "ISO27001"],
     "summary": "Change velocity vs change-control gates",
     "resolution": "Compliance gates in CI/CD pipeline"},
    {"id": "CON-AUTOMATION-HUMAN", "standards": ["EUAIACT", "ISO42001"],
     "summary": "Efficiency vs mandated human oversight",
     "resolution": "Human-in-the-loop checkpoints for high-risk AI"},
    {"id": "CON-TRANSPARENCY-IP", "standards": ["EUAIACT", "ISO42001"],
     "summary": "Model transparency vs trade secrets",
     "resolution": "Tiered disclosure with regulator-only annexes"},
    {"id": "CON-ESG-COST", "standards": ["ESRS", "ISO14001"],
     "summary": "Decarbonization capex vs short-term margin",
     "resolution": "Internal carbon pricing and phased targets"},
    {"id": "CON-SPEED-AUDIT", "standards": ["SOC2", "ISO9001"],
     "summary": "Ship fast vs documented change evidence",
     "resolution": "Automated evidence harvest from ITSM/CI-CD"},
    {"id": "CON-PRIVACY-SECURITY", "standards": ["GDPR", "ISO27001"],
     "summary": "Minimize data vs security monitoring needs",
     "resolution": "Pseudonymized logs with strict access control"},
    {"id": "CON-VENDOR-AGILITY", "standards": ["DORA", "ISO37001"],
     "summary": "Vendor due diligence depth vs onboarding speed",
     "resolution": "Tiered vendor risk with proportional checks"},
    {"id": "CON-AI-SAFETY-SPEED", "standards": ["EUAIACT", "NISTAIRMF"],
     "summary": "Model eval rigor vs time-to-market",
     "resolution": "Risk-tiered eval gates before production"},
    {"id": "CON-ESG-METRICS-BURDEN", "standards": ["ESRS", "GRISTD"],
     "summary": "Disclosure breadth vs SME reporting capacity",
     "resolution": "Materiality assessment scopes required metrics"},
    {"id": "CON-MULTI-JURISDICTION", "standards": ["GDPR", "CCPA", "PDPA_TH"],
     "summary": "Conflicting privacy obligations across regions",
     "resolution": "Strictest-common-denominator baseline + overlays"},
]

ERP_MODULES = [
    ("GRC", ["L1", "L2", "L3", "L18"],
     ["COBIT", "ISO37301", "COSOIC", "ISO38500"],
     ["UC-RM", "UC-AUD", "UC-DOC"]),
    ("HCM", ["L4", "L11", "L15"],
     ["ISO30414", "ISO45001", "ISO9001", "GDPR"],
     ["UC-TRN", "UC-OHS", "UC-AC"]),
    ("Finance", ["L5", "L3", "L18"],
     ["COSOIC", "SOX", "SOC1", "IFRS_ACC"],
     ["UC-FIN", "UC-AUD", "UC-AC"]),
    ("Procurement", ["L9", "L2", "L20"],
     ["ISO37001", "NIST800171", "DORA", "ISO9001"],
     ["UC-SUP", "UC-RM", "UC-DOC"]),
    ("Quality", ["L6", "L16", "L8"],
     ["ISO9001", "IATF16949", "AS9100", "ISO13485"],
     ["UC-CM", "UC-AUD", "UC-DOC"]),
    ("EHS", ["L10", "L11", "L17"],
     ["ISO14001", "ISO45001", "ISO50001", "ESRS"],
     ["UC-ENV", "UC-OHS"]),
    ("ITSM", ["L6", "L12", "L16"],
     ["ISO20000", "ITIL", "COBIT"],
     ["UC-CM", "UC-IM", "UC-AM"]),
    ("InfoSec", ["L12", "L19"],
     ["ISO27001", "NIST80053", "SOC2", "PCIDSS", "CISV8", "NIS2"],
     ["UC-AC", "UC-LOG", "UC-CRYPTO", "UC-VULN", "UC-IM", "UC-BCM"]),
    ("Privacy", ["L13", "L20"],
     ["ISO27701", "GDPR", "PDPA_TH", "PDPA_SG", "CCPA", "HIPAA"],
     ["UC-PM", "UC-DG"]),
    ("AI_Governance", ["L14", "L2"],
     ["ISO42001", "NISTAIRMF", "EUAIACT", "OECDAI", "OWASPLLM"],
     ["UC-AIG", "UC-RM"]),
    ("Risk", ["L2", "L1"],
     ["ISO31000", "COSOERM", "NISTCSF"],
     ["UC-RM", "UC-BCM"]),
    ("BCM", ["L19", "L6"],
     ["ISO22301", "DORA", "NISTCSF"],
     ["UC-BCM", "UC-IM"]),
    ("ESG", ["L17", "L10", "L1"],
     ["ESRS", "GRISTD", "IFRSS1", "IFRSS2", "GHGP_CORP", "CSRD", "TNFDREC"],
     ["UC-ESG", "UC-ENV"]),
    ("EAM", ["L7", "L6"],
     ["ISO55001", "ISO27001"],
     ["UC-AM"]),
    ("CRM", ["L8", "L13"],
     ["ISO9001", "WCAG", "GDPR"],
     ["UC-PM"]),
    ("Audit", ["L18", "L3"],
     ["ISO19011", "SOC2", "SOX"],
     ["UC-AUD"]),
]

ORG_NAMES = {
    "ISO": "International Organization for Standardization",
    "IEC": "International Electrotechnical Commission",
    "NIST": "National Institute of Standards and Technology",
    "ISACA": "ISACA (COBIT)",
    "AXELOS": "AXELOS (ITIL)",
    "AICPA": "American Institute of CPAs",
    "EU": "European Union",
    "GRI": "Global Reporting Initiative",
    "IFRS": "IFRS Foundation",
    "OECD": "OECD",
    "OWASP": "OWASP Foundation",
    "PCI": "PCI Security Standards Council",
    "CSA": "Cloud Security Alliance",
    "CIS": "Center for Internet Security",
    "COSO": "COSO",
    "NFPA": "NFPA",
    "TISI": "Thai Industrial Standards Institute",
    "PDPC": "Personal Data Protection Commission (Thailand)",
    "GHGP": "GHG Protocol",
    "TNFD": "Taskforce on Nature-related Financial Disclosures",
    "SASB": "SASB Standards",
    "DAMA": "DAMA International",
    "IETF": "IETF",
    "MITRE": "MITRE",
    "WCAG": "W3C (WCAG)",
    "IATF": "IATF",
    "SAE": "SAE International",
    "MISC": "Other / consortium",
}


def _org_for(std_id: str) -> str:
    if std_id.startswith("ISO"):
        return "ISO"
    if std_id.startswith("IEC"):
        return "IEC"
    if std_id.startswith("NIST"):
        return "NIST"
    if std_id in ("COBIT",):
        return "ISACA"
    if std_id == "ITIL":
        return "AXELOS"
    if std_id in ("SOC1", "SOC2"):
        return "AICPA"
    if std_id in ("EUAIACT", "NIS2", "DORA", "CSRD"):
        return "EU"
    if std_id.startswith("GRI") or std_id == "GRISTD":
        return "GRI"
    if std_id.startswith("IFRS"):
        return "IFRS"
    if std_id == "OECDAI":
        return "OECD"
    if std_id.startswith("OWASP"):
        return "OWASP"
    if std_id == "PCIDSS":
        return "PCI"
    if std_id == "CSACCM":
        return "CSA"
    if std_id.startswith("CIS"):
        return "CIS"
    if std_id.startswith("COSO"):
        return "COSO"
    if std_id == "NFPA":
        return "NFPA"
    if std_id == "TISI_OHS":
        return "TISI"
    if std_id == "PDPA_TH":
        return "PDPC"
    if std_id == "GHGP_CORP":
        return "GHGP"
    if std_id == "TNFDREC":
        return "TNFD"
    if std_id == "SASBSTD":
        return "SASB"
    if std_id == "DAMA-DMBOK":
        return "DAMA"
    if std_id == "TLS13":
        return "IETF"
    if std_id == "WCAG":
        return "WCAG"
    if std_id == "IATF16949":
        return "IATF"
    if std_id == "AS9100":
        return "SAE"
    if std_id == "MITRE":
        return "MITRE"
    return "MISC"


def _collect_standard_ids() -> set[str]:
    ids: set[str] = set()
    for _, _, _, _, present in REQUIREMENTS:
        ids.update(present)
    for _, _, _, _, satisfies in CONTROLS:
        ids.update(satisfies)
    for _, _, stds, _ in ERP_MODULES:
        ids.update(stds)
    for dom in DOMAINS:
        ids.update(dom[2])
    return ids


def _domains_for(std_id: str) -> list[str]:
    out: set[str] = set()
    for _, _, domains, _, satisfies in CONTROLS:
        if std_id in satisfies:
            out.update(domains)
    for dom_id, _, anchors in DOMAINS:
        if std_id in anchors:
            out.add(dom_id)
    return sorted(out) or ["L20"]


def write_all() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    std_ids = _collect_standard_ids()
    org_ids = {_org_for(s) for s in std_ids}
    org_ids.update(ORG_NAMES)

    orgs = [{"id": oid, "name": ORG_NAMES.get(oid, oid), "scope": "global"}
            for oid in sorted(org_ids)]

    standards = []
    for sid in sorted(std_ids):
        standards.append({
            "id": sid,
            "org": _org_for(sid),
            "name": sid.replace("_", " "),
            "code": sid,
            "status": "active",
            "type": "standard",
            "taxonomy": _domains_for(sid),
        })

    taxonomy = {
        "domains": [
            {"id": did, "name": name, "anchor_standards": anchors}
            for did, name, anchors in DOMAINS
        ]
    }

    requirements = {
        "requirements": [
            {
                "id": rid,
                "name": name,
                "hs_clause": clause,
                "similarity": sim,
                "present_in": present,
            }
            for rid, name, clause, sim, present in REQUIREMENTS
        ]
    }

    controls = {
        "controls": [
            {
                "id": cid,
                "name": name,
                "domains": domains,
                "requirements": reqs,
                "satisfies": satisfies,
            }
            for cid, name, domains, reqs, satisfies in CONTROLS
        ]
    }

    evidence = {
        "evidence": [
            {
                "id": eid,
                "name": name,
                "controls": ctrls,
                "auto_collectable": auto,
            }
            for eid, name, ctrls, auto in EVIDENCE
        ]
    }

    erp = {
        "modules": [
            {
                "module": mod,
                "domains": domains,
                "standards": stds,
                "controls": ctrls,
            }
            for mod, domains, stds, ctrls in ERP_MODULES
        ]
    }

    files = {
        "organizations.json": {"organizations": orgs},
        "standards.json": {"standards": standards},
        "taxonomy.json": taxonomy,
        "common_requirements.json": requirements,
        "controls.json": controls,
        "evidence.json": evidence,
        "conflicts.json": {"conflicts": CONFLICTS},
        "erp_mapping.json": erp,
    }

    for fname, payload in files.items():
        (DATA / fname).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Wrote {len(files)} files to {DATA}")


def main() -> int:
    write_all()
    from standards_kb.graph import Graph
    g = Graph.load()
    errs = g.validate()
    if errs:
        print(f"Validation failed ({len(errs)} errors):")
        for e in errs[:20]:
            print(" ", e)
        return 1
    summary = g.summary()
    print("Graph summary:", summary)
    print("✅ Referential integrity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
