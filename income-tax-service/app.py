"""
income-tax-service  (Python + Flask)  -> listens on port 5000

Endpoints
  GET  /health             liveness/readiness check used by Docker & Kubernetes
  POST /calculate          {"annual_income": 1500000, "regime": "new", "deductions": 0}
  POST /compare            {"annual_income": 1500000, "deductions": 200000}
"""
import os
import socket

from flask import Flask, jsonify, request

from tax_logic import calculate_tax, compare_regimes

app = Flask(__name__)
MAX_INCOME = 10_000_000_000  # 1000 crore sanity cap


def _read_number(payload, key, default=None):
    value = payload.get(key, default)
    if value is None:
        raise ValueError(f"'{key}' is required")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a number")
    if value < 0 or value > MAX_INCOME:
        raise ValueError(f"'{key}' must be between 0 and {MAX_INCOME}")
    return value


@app.get("/health")
def health():
    # hostname shows WHICH pod/container answered - handy to demo load balancing in K8s
    return jsonify(status="UP", service="income-tax-service",
                   version=os.getenv("APP_VERSION", "dev"), host=socket.gethostname())


@app.post("/calculate")
def calculate():
    payload = request.get_json(silent=True) or {}
    try:
        income = _read_number(payload, "annual_income")
        deductions = _read_number(payload, "deductions", 0)
        regime = str(payload.get("regime", "new")).lower()
        salaried = bool(payload.get("salaried", True))
        return jsonify(calculate_tax(income, regime, deductions, salaried))
    except ValueError as err:
        return jsonify(error=str(err)), 400


@app.post("/compare")
def compare():
    payload = request.get_json(silent=True) or {}
    try:
        income = _read_number(payload, "annual_income")
        deductions = _read_number(payload, "deductions", 0)
        salaried = bool(payload.get("salaried", True))
        return jsonify(compare_regimes(income, deductions, salaried))
    except ValueError as err:
        return jsonify(error=str(err)), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
