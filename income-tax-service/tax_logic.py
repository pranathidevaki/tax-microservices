"""
Pure tax-calculation logic (no web framework here) so it is easy to unit test.

Rules implemented: Indian individual income tax, FY 2026-27 (AY 2027-28).
Budget 2026 kept the FY 2025-26 slabs unchanged.

NEW regime (default regime):
    0 - 4L: 0% | 4-8L: 5% | 8-12L: 10% | 12-16L: 15% | 16-20L: 20% | 20-24L: 25% | >24L: 30%
    Standard deduction (salaried): 75,000
    Sec 87A rebate: taxable income <= 12L -> tax becomes 0 (max 60,000),
                    with marginal relief just above 12L
OLD regime (individual below 60):
    0 - 2.5L: 0% | 2.5-5L: 5% | 5-10L: 20% | >10L: 30%
    Standard deduction (salaried): 50,000, plus other deductions (80C, 80D ...)
    Sec 87A rebate: taxable income <= 5L -> max 12,500
Health & Education cess: 4% on tax after rebate.
Surcharge (income above 50L) is NOT modelled - kept out on purpose for simplicity.
"""

INF = float("inf")

NEW_REGIME_SLABS = [
    (400_000, 0.00),
    (800_000, 0.05),
    (1_200_000, 0.10),
    (1_600_000, 0.15),
    (2_000_000, 0.20),
    (2_400_000, 0.25),
    (INF, 0.30),
]

OLD_REGIME_SLABS = [
    (250_000, 0.00),
    (500_000, 0.05),
    (1_000_000, 0.20),
    (INF, 0.30),
]

CONFIG = {
    "new": {"slabs": NEW_REGIME_SLABS, "std_deduction": 75_000,
            "rebate_limit": 1_200_000, "rebate_max": 60_000, "allows_deductions": False},
    "old": {"slabs": OLD_REGIME_SLABS, "std_deduction": 50_000,
            "rebate_limit": 500_000, "rebate_max": 12_500, "allows_deductions": True},
}

CESS_RATE = 0.04


def slab_tax(taxable_income, slabs):
    """Walk through the slabs and tax each 'slice' of income at its own rate."""
    tax = 0.0
    lower = 0
    breakdown = []
    for upper, rate in slabs:
        if taxable_income <= lower:
            break
        slice_amount = min(taxable_income, upper) - lower
        slice_tax = slice_amount * rate
        tax += slice_tax
        breakdown.append({
            "from": lower,
            "to": None if upper == INF else upper,
            "rate_percent": round(rate * 100),
            "taxable_amount": round(slice_amount),
            "tax": round(slice_tax),
        })
        lower = upper
    return tax, breakdown


def calculate_tax(annual_income, regime="new", deductions=0, salaried=True):
    if regime not in CONFIG:
        raise ValueError("regime must be 'new' or 'old'")
    if annual_income < 0 or deductions < 0:
        raise ValueError("income and deductions must be non-negative")

    cfg = CONFIG[regime]
    std_deduction = cfg["std_deduction"] if salaried else 0
    other_deductions = deductions if cfg["allows_deductions"] else 0

    taxable = max(0, annual_income - std_deduction - other_deductions)
    tax, breakdown = slab_tax(taxable, cfg["slabs"])

    # Section 87A rebate
    rebate = 0.0
    if taxable <= cfg["rebate_limit"]:
        rebate = min(tax, cfg["rebate_max"])
    elif regime == "new":
        # Marginal relief: tax can't exceed the income earned above 12L
        excess = taxable - cfg["rebate_limit"]
        if tax > excess:
            rebate = tax - excess

    tax_after_rebate = tax - rebate
    cess = tax_after_rebate * CESS_RATE
    total = tax_after_rebate + cess

    return {
        "regime": regime,
        "gross_income": round(annual_income),
        "standard_deduction": std_deduction,
        "other_deductions": round(other_deductions),
        "taxable_income": round(taxable),
        "slab_breakdown": breakdown,
        "tax_before_rebate": round(tax),
        "rebate_87a": round(rebate),
        "tax_after_rebate": round(tax_after_rebate),
        "cess": round(cess),
        "total_tax": round(total),
        "effective_rate_percent": round(total / annual_income * 100, 2) if annual_income else 0.0,
        "monthly_take_home": round((annual_income - total) / 12),
    }


def compare_regimes(annual_income, deductions=0, salaried=True):
    new = calculate_tax(annual_income, "new", deductions, salaried)
    old = calculate_tax(annual_income, "old", deductions, salaried)
    better = "new" if new["total_tax"] <= old["total_tax"] else "old"
    return {
        "new": new,
        "old": old,
        "recommended": better,
        "savings": abs(new["total_tax"] - old["total_tax"]),
    }
