/**
 * Pure GST logic (no Express here) so it can be unit tested.
 *
 * GST 2.0 (effective 22 Sep 2025): main slabs 0%, 5%, 18% and 40% (sin/luxury),
 * plus special rates 0.25% (rough diamonds/precious stones) and 3% (gold, silver, jewellery).
 *
 * Intra-state sale  -> tax split equally into CGST (Centre) + SGST (State)
 * Inter-state sale  -> single IGST
 */
const ALLOWED_RATES = [0, 0.25, 3, 5, 18, 40];

const round2 = (n) => Math.round(n * 100) / 100;

function calculateGst({ amount, rate, inclusive = false, interstate = false }) {
  amount = Number(amount);
  rate = Number(rate);

  if (!Number.isFinite(amount) || amount < 0) {
    throw new Error("'amount' must be a non-negative number");
  }
  if (!ALLOWED_RATES.includes(rate)) {
    throw new Error(`'rate' must be one of ${ALLOWED_RATES.join(", ")}`);
  }

  // inclusive = the amount already contains GST, so pull the base price out of it
  const base = inclusive ? amount / (1 + rate / 100) : amount;
  const gst = base * (rate / 100);

  return {
    base_amount: round2(base),
    rate_percent: rate,
    supply_type: interstate ? "inter-state" : "intra-state",
    cgst: interstate ? 0 : round2(gst / 2),
    sgst: interstate ? 0 : round2(gst / 2),
    igst: interstate ? round2(gst) : 0,
    total_gst: round2(gst),
    total_amount: round2(base + gst),
  };
}

module.exports = { calculateGst, ALLOWED_RATES };
