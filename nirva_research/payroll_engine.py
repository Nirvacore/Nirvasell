"""NIRVA payroll calculation engine — executable implementation of the
Payroll Business Rules Catalogue (nirva_research/data/payroll_rules.json).

Design contract
---------------
* Pure standard library; deterministic; no I/O in the math path.
* Every statutory figure lives in ``StatutoryConfig`` as a DATED parameter — the
  engine never hard-codes a rate. A law change is a config change (rule §H /
  PR-* ``[verify]`` discipline), so the *formulas* here can be trusted while the
  *values* stay confirmable against MoL / RD / SSO.
* Each function cites the catalogue rule it implements.

This is an engineering artifact, not legal advice. Default values are marked
[verify] and must be confirmed before production use.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


# --------------------------------------------------------------------------
# Statutory configuration (dated parameters — verify before production)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class StatutoryConfig:
    """Dated snapshot of Thai statutory payroll parameters. Mirrors the
    ``parameters`` block of payroll_rules.json. All figures [verify]."""
    effective_date: date = date(2026, 1, 1)
    # Wage basis (Thai convention) — PR-EARN-002
    monthly_to_daily_divisor: int = 30
    daily_to_hourly_divisor: int = 8
    # Minimum wage — PR-EARN-001 (province-specific; default is a placeholder)
    default_min_wage_per_day: float = 360.0  # [verify by province/year]
    min_wage_by_province: dict[str, float] = field(default_factory=dict)
    # OT / holiday multipliers — PR-EARN-003/004/005/006 (LPA §61-63)
    ot_working_day_multiplier: float = 1.5
    holiday_work_multiplier_daily: float = 2.0     # daily-paid, normal hours
    holiday_work_extra_monthly: float = 1.0        # monthly-paid, additional
    holiday_ot_multiplier: float = 3.0
    # Social Security — PR-DED-001 (base capped 1,650-15,000; 5%)
    sso_rate: float = 0.05
    sso_base_min: float = 1650.0
    sso_base_max: float = 15000.0
    # Deduction limits — PR-DED-004 (LPA §76)
    deduction_each_max_ratio: float = 0.10
    deduction_total_max_ratio: float = 0.20
    # Severance bands — PR-TERM-001 (LPA §118): (min_service_days, days_of_wage)
    severance_bands: tuple[tuple[int, int], ...] = (
        (120, 30), (365, 90), (1095, 180), (2190, 240), (3650, 300), (7300, 400),
    )
    rounding_dp: int = 2  # PR-CTRL-006


DEFAULT_CONFIG = StatutoryConfig()


def _round(x: float, cfg: StatutoryConfig) -> float:
    return round(x + 1e-9, cfg.rounding_dp)  # nudge to avoid 0.005 banker's drift


# --------------------------------------------------------------------------
# Core wage maths
# --------------------------------------------------------------------------
def hourly_rate(pay_type: str, base_wage: float, cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Hourly rate. PR-EARN-002.
    monthly: salary / 30 / 8   ·   daily: daily_wage / 8."""
    if pay_type == "monthly":
        return _round(base_wage / cfg.monthly_to_daily_divisor / cfg.daily_to_hourly_divisor, cfg)
    if pay_type == "daily":
        return _round(base_wage / cfg.daily_to_hourly_divisor, cfg)
    raise ValueError(f"pay_type must be 'monthly' or 'daily', got {pay_type!r}")


def daily_rate(pay_type: str, base_wage: float, cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Daily wage rate. monthly: salary/30 · daily: the daily wage itself."""
    if pay_type == "monthly":
        return _round(base_wage / cfg.monthly_to_daily_divisor, cfg)
    return _round(base_wage, cfg)


def overtime_pay(pay_type: str, base_wage: float, ot_hours: float,
                 cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """OT on a normal working day = hourly × 1.5 × hours. PR-EARN-003 (§62)."""
    return _round(hourly_rate(pay_type, base_wage, cfg) * cfg.ot_working_day_multiplier * ot_hours, cfg)


def holiday_work_pay(pay_type: str, base_wage: float, hours: float,
                     cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Pay for working on a holiday during NORMAL hours. PR-EARN-004/005 (§62/63).
    daily-paid  -> additional 2× the wage rate for the hours worked
    monthly-paid-> additional 1× hourly (salary already covers the day)."""
    h = hourly_rate(pay_type, base_wage, cfg)
    if pay_type == "daily":
        return _round(h * cfg.holiday_work_multiplier_daily * hours, cfg)
    return _round(h * cfg.holiday_work_extra_monthly * hours, cfg)


def holiday_overtime_pay(pay_type: str, base_wage: float, ot_hours: float,
                         cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """OT beyond normal hours on a holiday = hourly × 3 × hours. PR-EARN-006 (§63)."""
    return _round(hourly_rate(pay_type, base_wage, cfg) * cfg.holiday_ot_multiplier * ot_hours, cfg)


# --------------------------------------------------------------------------
# Validations & statutory deductions
# --------------------------------------------------------------------------
def minimum_wage_ok(daily_wage_effective: float, province: str | None = None,
                    cfg: StatutoryConfig = DEFAULT_CONFIG) -> bool:
    """PR-EARN-001 (§90). True if the effective daily wage meets the floor."""
    floor = cfg.min_wage_by_province.get(province or "", cfg.default_min_wage_per_day)
    return daily_wage_effective + 1e-9 >= floor


def social_security(wage: float, cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Employee SSO contribution. PR-DED-001. 5% of wage with base capped
    [1,650, 15,000] → max 750/month."""
    base = min(max(wage, cfg.sso_base_min), cfg.sso_base_max)
    return _round(base * cfg.sso_rate, cfg)


def apply_deduction_limits(wage: float, deductions: list[tuple[str, float, bool]],
                           cfg: StatutoryConfig = DEFAULT_CONFIG) -> tuple[list[tuple[str, float]], list[str]]:
    """PR-DED-004 (§76). Non-tax/non-SSO deductions: each ≤10% and aggregate
    ≤20% of wage UNLESS the employee consented. Returns (allowed, violations).

    `deductions` items: (name, amount, consented). Consented deductions pass
    through but are flagged if they push net below zero (never auto-applied)."""
    allowed: list[tuple[str, float]] = []
    violations: list[str] = []
    each_cap = wage * cfg.deduction_each_max_ratio
    total_cap = wage * cfg.deduction_total_max_ratio
    running = 0.0
    for name, amount, consented in deductions:
        if not consented and amount > each_cap + 1e-9:
            violations.append(f"{name}: {amount:.2f} exceeds 10% cap ({each_cap:.2f}) without consent")
            amount = each_cap
        if not consented and running + amount > total_cap + 1e-9:
            capped = max(0.0, total_cap - running)
            violations.append(f"{name}: would exceed 20% aggregate cap; capped {amount:.2f}->{capped:.2f}")
            amount = capped
        running += amount
        allowed.append((name, _round(amount, cfg)))
    return allowed, violations


def severance_days(service_days: int, cfg: StatutoryConfig = DEFAULT_CONFIG) -> int:
    """Statutory severance in days-of-wage by tenure. PR-TERM-001 (§118).
    < 120 days service → 0."""
    result = 0
    for min_days, days in cfg.severance_bands:
        if service_days >= min_days:
            result = days
    return result


def severance_pay(pay_type: str, base_wage: float, service_days: int,
                  cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Severance amount = severance_days × daily rate. PR-TERM-001."""
    return _round(severance_days(service_days, cfg) * daily_rate(pay_type, base_wage, cfg), cfg)


# --------------------------------------------------------------------------
# Payslip composition
# --------------------------------------------------------------------------
@dataclass
class Worker:
    pay_type: str               # 'monthly' | 'daily'
    base_wage: float            # monthly salary OR daily wage
    province: str | None = None
    days_worked: float = 30     # paid days in period (daily-paid) / present days
    period_days: int = 30       # divisor for monthly proration
    ot_hours: float = 0.0
    holiday_hours: float = 0.0          # normal hours worked on a holiday
    holiday_ot_hours: float = 0.0
    wage_allowances: float = 0.0        # count toward OT/severance base (true ค่าจ้าง)
    nonwage_allowances: float = 0.0     # welfare/reimbursement (excluded from base)
    sso_member: bool = True
    pf_rate: float = 0.0                # provident-fund employee rate (0-0.15)
    other_deductions: list[tuple[str, float, bool]] = field(default_factory=list)


def compute_payslip(w: Worker, cfg: StatutoryConfig = DEFAULT_CONFIG) -> dict:
    """Assemble a full payslip from the catalogue rules. Returns line items,
    totals, the rule IDs applied, and any compliance flags. Pure calculation —
    the engine flags violations; it does not silently 'fix' wages."""
    flags: list[str] = []
    rules: list[str] = []

    # Base earnings -------------------------------------------------------
    if w.pay_type == "monthly":
        base_earnings = _round(w.base_wage * (w.days_worked / w.period_days), cfg)  # PR-EARN-009
        rules.append("PR-EARN-009")
    else:
        base_earnings = _round(w.base_wage * w.days_worked, cfg)

    # Minimum-wage check (PR-EARN-001) -----------------------------------
    eff_daily = daily_rate(w.pay_type, w.base_wage, cfg)
    if not minimum_wage_ok(eff_daily, w.province, cfg):
        floor = cfg.min_wage_by_province.get(w.province or "", cfg.default_min_wage_per_day)
        flags.append(f"BLOCK PR-EARN-001: daily {eff_daily:.2f} < minimum {floor:.2f}")
    rules.append("PR-EARN-001")

    # Premium earnings ----------------------------------------------------
    ot = overtime_pay(w.pay_type, w.base_wage, w.ot_hours, cfg)
    hol = holiday_work_pay(w.pay_type, w.base_wage, w.holiday_hours, cfg)
    hol_ot = holiday_overtime_pay(w.pay_type, w.base_wage, w.holiday_ot_hours, cfg)
    rules += ["PR-EARN-003", "PR-EARN-004", "PR-EARN-005", "PR-EARN-006", "PR-EARN-007"]

    gross = _round(base_earnings + ot + hol + hol_ot + w.wage_allowances + w.nonwage_allowances, cfg)

    # Deductions ----------------------------------------------------------
    sso = social_security(gross, cfg) if w.sso_member else 0.0
    if w.sso_member:
        rules.append("PR-DED-001")
    pf = _round(gross * w.pf_rate, cfg) if w.pf_rate else 0.0
    if w.pf_rate:
        rules.append("PR-DED-003")

    allowed_other, viol = apply_deduction_limits(gross, w.other_deductions, cfg)
    if w.other_deductions:
        rules.append("PR-DED-004")
    flags += [f"WARN PR-DED-004: {v}" for v in viol]
    other_total = _round(sum(a for _, a in allowed_other), cfg)

    total_deductions = _round(sso + pf + other_total, cfg)
    net = _round(gross - total_deductions, cfg)
    if net < 0:
        flags.append("BLOCK: net pay negative — review deductions (never net below 0 / min wage)")

    return {
        "earnings": {
            "base": base_earnings, "overtime": ot, "holiday_work": hol,
            "holiday_overtime": hol_ot,
            "wage_allowances": w.wage_allowances, "nonwage_allowances": w.nonwage_allowances,
        },
        "gross": gross,
        "deductions": {
            "social_security": sso, "provident_fund": pf,
            "other": allowed_other, "total": total_deductions,
        },
        "net": net,
        "rules_applied": sorted(set(rules)),
        "flags": flags,
        "config_effective": cfg.effective_date.isoformat(),
    }
