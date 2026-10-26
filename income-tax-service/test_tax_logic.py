"""Unit tests - these run in the CI pipeline (GitHub Actions / Jenkins) on every push."""
import pytest

from app import app
from tax_logic import calculate_tax, compare_regimes


def test_zero_income_has_zero_tax():
    assert calculate_tax(0)["total_tax"] == 0


def test_new_regime_12_75_lakh_salaried_is_tax_free():
    # 12,75,000 - 75,000 std deduction = 12,00,000 taxable -> full 87A rebate
    r = calculate_tax(1_275_000, "new")
    assert r["taxable_income"] == 1_200_000
    assert r["tax_before_rebate"] == 60_000
    assert r["total_tax"] == 0


def test_new_regime_20_lakh():
    # taxable 19,25,000: 0 + 20k + 40k + 60k + 65k(3.25L @20%) = 1,85,000 ; +4% cess = 1,92,400
    r = calculate_tax(2_000_000, "new")
    assert r["tax_before_rebate"] == 185_000
    assert r["total_tax"] == 192_400


def test_new_regime_marginal_relief():
    # taxable 12,10,000 -> slab tax 61,500 but tax can't exceed 10,000 earned above 12L
    r = calculate_tax(1_285_000, "new")
    assert r["taxable_income"] == 1_210_000
    assert r["tax_after_rebate"] == 10_000


def test_old_regime_with_deductions():
    # 10L - 50k std - 1.5L 80C = 8L taxable: 12,500 + 60,000 = 72,500 ; + cess = 75,400
    r = calculate_tax(1_000_000, "old", deductions=150_000)
    assert r["taxable_income"] == 800_000
    assert r["total_tax"] == 75_400


def test_old_regime_rebate_up_to_5_lakh():
    assert calculate_tax(550_000, "old")["total_tax"] == 0


def test_new_regime_ignores_deductions():
    assert calculate_tax(1_500_000, "new", deductions=200_000)["other_deductions"] == 0


def test_compare_recommends_cheaper_regime():
    result = compare_regimes(1_500_000)
    assert result["recommended"] == "new"


def test_invalid_regime_raises():
    with pytest.raises(ValueError):
        calculate_tax(100, "weird")


# ---------- API (HTTP) tests using Flask's test client ----------
@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "UP"


def test_calculate_endpoint(client):
    resp = client.post("/calculate", json={"annual_income": 2_000_000, "regime": "new"})
    assert resp.status_code == 200
    assert resp.get_json()["total_tax"] == 192_400


def test_calculate_rejects_bad_input(client):
    resp = client.post("/calculate", json={"annual_income": "abc"})
    assert resp.status_code == 400
