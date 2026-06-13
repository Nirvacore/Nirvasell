"""Unit tests for the NIRVA payroll engine — proves each catalogue formula.

Runs with the plain interpreter (no pytest required)::

    python -m nirva_research.test_payroll_engine

…and is also pytest-discoverable (def test_*). Values are computed from an
explicit StatutoryConfig so the tests assert FORMULA correctness, not the
current legal figures (which live in config and are [verify]).
"""
from __future__ import annotations

from nirva_research.payroll_engine import (
    StatutoryConfig, Worker, hourly_rate, daily_rate, overtime_pay,
    holiday_work_pay, holiday_overtime_pay, minimum_wage_ok, social_security,
    apply_deduction_limits, severance_days, severance_pay, compute_payslip,
)

CFG = StatutoryConfig()  # defaults; deterministic


# ---- wage maths ----------------------------------------------------------
def test_hourly_rate_monthly():
    assert hourly_rate("monthly", 30000, CFG) == 125.0      # 30000/30/8

def test_hourly_rate_daily():
    assert hourly_rate("daily", 400, CFG) == 50.0           # 400/8

def test_daily_rate_monthly():
    assert daily_rate("monthly", 30000, CFG) == 1000.0      # 30000/30

def test_overtime_monthly():
    assert overtime_pay("monthly", 30000, 10, CFG) == 1875.0  # 125*1.5*10

def test_overtime_daily():
    assert overtime_pay("daily", 400, 2, CFG) == 150.0        # 50*1.5*2


# ---- holiday pay: the daily vs monthly distinction (the #1 Thai error) ----
def test_holiday_work_daily_is_2x():
    # daily-paid working a holiday (8h) earns an extra 2× the daily wage
    assert holiday_work_pay("daily", 400, 8, CFG) == 800.0    # 50*2*8 = 2*400

def test_holiday_work_monthly_is_1x_extra():
    # monthly-paid already paid for the day → only +1× hourly
    assert holiday_work_pay("monthly", 30000, 8, CFG) == 1000.0  # 125*1*8

def test_holiday_overtime_is_3x():
    assert holiday_overtime_pay("daily", 400, 2, CFG) == 300.0   # 50*3*2


# ---- statutory deductions & checks ---------------------------------------
def test_sso_caps_high_wage():
    assert social_security(30000, CFG) == 750.0   # base capped at 15000 → 5%

def test_sso_floors_low_wage():
    assert social_security(1000, CFG) == 82.5     # floored to 1650 → 5%

def test_sso_midrange():
    assert social_security(8000, CFG) == 400.0    # 8000*0.05

def test_minimum_wage_pass_and_fail():
    assert minimum_wage_ok(400.0, None, CFG) is True
    assert minimum_wage_ok(300.0, None, CFG) is False  # below default 360


def test_deduction_each_cap_without_consent():
    # wage 10000 → 10% cap = 1000; a 1500 unconsented loan is capped to 1000
    allowed, viol = apply_deduction_limits(10000, [("loan", 1500, False)], CFG)
    assert allowed == [("loan", 1000.0)]
    assert len(viol) == 1

def test_deduction_consent_passes_through():
    allowed, viol = apply_deduction_limits(10000, [("loan", 1500, True)], CFG)
    assert allowed == [("loan", 1500.0)] and viol == []

def test_deduction_total_aggregate_cap():
    # each 800 ≤10% ok, but third exceeds 20% aggregate (2000); 2000-1600=400 left
    items = [("a", 800, False), ("b", 800, False), ("c", 800, False)]
    allowed, viol = apply_deduction_limits(10000, items, CFG)
    assert allowed[2] == ("c", 400.0)
    assert any("aggregate" in v for v in viol)


# ---- severance bands (§118 boundaries) -----------------------------------
def test_severance_band_boundaries():
    cases = {119: 0, 120: 30, 364: 30, 365: 90, 1094: 90, 1095: 180,
             2189: 180, 2190: 240, 3649: 240, 3650: 300, 7299: 300, 7300: 400}
    for days, expected in cases.items():
        assert severance_days(days, CFG) == expected, f"{days}->{expected}"

def test_severance_pay_amount():
    # 4 years (1460 days) monthly 30000 → 180 days × (30000/30) = 180*1000
    assert severance_pay("monthly", 30000, 1460, CFG) == 180000.0


# ---- payslip integration -------------------------------------------------
def test_payslip_monthly_full_period():
    w = Worker(pay_type="monthly", base_wage=30000)
    p = compute_payslip(w, CFG)
    assert p["gross"] == 30000.0
    assert p["deductions"]["social_security"] == 750.0
    assert p["net"] == 29250.0
    assert p["flags"] == []

def test_payslip_daily_with_overtime():
    w = Worker(pay_type="daily", base_wage=400, days_worked=26, ot_hours=10)
    p = compute_payslip(w, CFG)
    assert p["earnings"]["base"] == 10400.0      # 400*26
    assert p["earnings"]["overtime"] == 750.0    # 50*1.5*10
    assert p["gross"] == 11150.0
    assert p["deductions"]["social_security"] == 557.5  # 11150*0.05
    assert p["net"] == 10592.5

def test_payslip_minimum_wage_block_flag():
    w = Worker(pay_type="daily", base_wage=300)   # below default 360 floor
    p = compute_payslip(w, CFG)
    assert any("BLOCK PR-EARN-001" in f for f in p["flags"])


# ---- runner --------------------------------------------------------------
def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {t.__name__}: {type(e).__name__}: {e}")
    print(f"\nPayroll engine tests: {passed} passed, {failed} failed ({len(tests)} total)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
