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
    # Personal income tax / PND.1 — PR-DED-002 (Revenue Code). All [verify].
    # Brackets as (upper_bound_of_band, marginal_rate); last band upper = inf.
    pit_brackets: tuple[tuple[float, float], ...] = (
        (150000, 0.00), (300000, 0.05), (500000, 0.10), (750000, 0.15),
        (1000000, 0.20), (2000000, 0.25), (5000000, 0.30), (float("inf"), 0.35),
    )
    pit_expense_rate: float = 0.50          # employment-income expense deduction
    pit_expense_cap: float = 100000.0       # capped at 100k/yr
    pit_personal_allowance: float = 60000.0
    pit_spouse_allowance: float = 60000.0   # if spouse has no income
    pit_child_allowance: float = 30000.0    # per child
    pit_sso_deduction_cap: float = 9000.0   # SSO is tax-deductible, capped/yr
    # Termination — PR-TERM-002 (LPA §17): advance notice ≥ one pay period.
    notice_period_days: int = 30             # [verify per contract]
    final_pay_deadline_days: int = 3         # PR-TERM-003 (§70): pay within 3 days


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


@dataclass
class TaxProfile:
    """Per-employee inputs for PIT (PR-DED-002). Personal allowance & the
    employment-expense deduction are automatic; these are the variable parts."""
    spouse_no_income: bool = False
    children: int = 0
    extra_deductions: float = 0.0   # annual: provident fund, life/health insurance, donations, etc.


def annual_income_tax(taxable: float, cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Progressive PIT on net taxable income. PR-DED-002 (Revenue Code §48)."""
    tax = 0.0
    lower = 0.0
    for upper, rate in cfg.pit_brackets:
        if taxable <= lower:
            break
        band = min(taxable, upper) - lower
        tax += band * rate
        lower = upper
    return _round(tax, cfg)


def pit_allowances(profile: TaxProfile, annual_income: float, sso_annual: float,
                   cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Total deductions & allowances applied before the tax brackets. PR-DED-002."""
    expense = min(annual_income * cfg.pit_expense_rate, cfg.pit_expense_cap)
    allow = cfg.pit_personal_allowance
    if profile.spouse_no_income:
        allow += cfg.pit_spouse_allowance
    allow += max(0, profile.children) * cfg.pit_child_allowance
    allow += min(sso_annual, cfg.pit_sso_deduction_cap)
    allow += max(0.0, profile.extra_deductions)
    return _round(expense + allow, cfg)


def pit_withholding_monthly(monthly_income: float, profile: TaxProfile,
                            monthly_sso: float, cfg: StatutoryConfig = DEFAULT_CONFIG) -> float:
    """Monthly PND.1 withholding via the standard annualization method:
    annual tax on (12 × monthly income), divided by 12. PR-DED-002.
    Simplified for regular monthly income; irregular pay needs re-estimation."""
    annual_income = monthly_income * 12
    deductions = pit_allowances(profile, annual_income, monthly_sso * 12, cfg)
    taxable = max(0.0, annual_income - deductions)
    return _round(annual_income_tax(taxable, cfg) / 12, cfg)


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


def compute_final_pay(pay_type: str, base_wage: float, service_days: int,
                      termination_type: str, unused_leave_days: float = 0.0,
                      notice_given: bool = True, final_worked_days: float = 0.0,
                      period_days: int = 30, cfg: StatutoryConfig = DEFAULT_CONFIG) -> dict:
    """Compose an employee's final settlement. Combines:
      • pro-rata final wage for days worked but unpaid
      • severance by tenure        — PR-TERM-001 (§118)
      • payment in lieu of notice  — PR-TERM-002 (§17)
      • unused annual-leave payout — PR-TERM-004 (§67)
    and flags the statutory payment deadline — PR-TERM-003 (§70).

    termination_type:
      'without_cause' — employer dismissal w/o serious cause → severance + (lieu if no notice)
      'with_cause'    — §119 serious misconduct → no severance, no lieu
      'resignation'   — employee-initiated → no severance, no lieu
    Leave payout and earned final wages are owed in all cases.
    """
    if termination_type not in {"without_cause", "with_cause", "resignation"}:
        raise ValueError(f"unknown termination_type {termination_type!r}")

    dr = daily_rate(pay_type, base_wage, cfg)
    rules: list[str] = []

    if pay_type == "monthly":
        final_wage = _round(base_wage * (final_worked_days / period_days), cfg)
    else:
        final_wage = _round(dr * final_worked_days, cfg)

    severance = 0.0
    if termination_type == "without_cause":
        severance = severance_pay(pay_type, base_wage, service_days, cfg)
        rules.append("PR-TERM-001")

    pay_in_lieu = 0.0
    if termination_type == "without_cause" and not notice_given:
        pay_in_lieu = _round(dr * cfg.notice_period_days, cfg)
        rules.append("PR-TERM-002")

    leave_payout = _round(dr * unused_leave_days, cfg)
    if unused_leave_days:
        rules.append("PR-TERM-004")

    total = _round(final_wage + severance + pay_in_lieu + leave_payout, cfg)
    rules.append("PR-TERM-003")

    return {
        "components": {
            "final_wage": final_wage,
            "severance": severance,
            "severance_days": severance_days(service_days, cfg) if severance else 0,
            "pay_in_lieu_of_notice": pay_in_lieu,
            "unused_leave_payout": leave_payout,
        },
        "total": total,
        "termination_type": termination_type,
        "rules_applied": sorted(set(rules)),
        "flags": [f"PR-TERM-003 (§70): pay within {cfg.final_pay_deadline_days} days of termination"],
    }


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
    tax_profile: "TaxProfile | None" = None  # if set, PIT/PND.1 is withheld (PR-DED-002)


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

    pit = 0.0
    if w.tax_profile is not None:
        pit = pit_withholding_monthly(gross, w.tax_profile, sso, cfg)
        rules.append("PR-DED-002")

    allowed_other, viol = apply_deduction_limits(gross, w.other_deductions, cfg)
    if w.other_deductions:
        rules.append("PR-DED-004")
    flags += [f"WARN PR-DED-004: {v}" for v in viol]
    other_total = _round(sum(a for _, a in allowed_other), cfg)

    total_deductions = _round(sso + pf + pit + other_total, cfg)
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
            "social_security": sso, "provident_fund": pf, "income_tax": pit,
            "other": allowed_other, "total": total_deductions,
        },
        "net": net,
        "rules_applied": sorted(set(rules)),
        "flags": flags,
        "config_effective": cfg.effective_date.isoformat(),
    }
