// Unit tests using Node's built-in test runner (no extra libraries). Run: npm test
const test = require("node:test");
const assert = require("node:assert");
const { calculateGst } = require("./gst");

test("18% exclusive intra-state splits into CGST + SGST", () => {
  const r = calculateGst({ amount: 1000, rate: 18 });
  assert.strictEqual(r.cgst, 90);
  assert.strictEqual(r.sgst, 90);
  assert.strictEqual(r.igst, 0);
  assert.strictEqual(r.total_amount, 1180);
});

test("18% inter-state goes fully to IGST", () => {
  const r = calculateGst({ amount: 1000, rate: 18, interstate: true });
  assert.strictEqual(r.igst, 180);
  assert.strictEqual(r.cgst, 0);
});

test("inclusive amount extracts the base price", () => {
  const r = calculateGst({ amount: 1050, rate: 5, inclusive: true });
  assert.strictEqual(r.base_amount, 1000);
  assert.strictEqual(r.total_gst, 50);
});

test("0% rate means no tax", () => {
  assert.strictEqual(calculateGst({ amount: 500, rate: 0 }).total_amount, 500);
});

test("invalid rate is rejected", () => {
  assert.throws(() => calculateGst({ amount: 100, rate: 12.5 }));
});

test("negative amount is rejected", () => {
  assert.throws(() => calculateGst({ amount: -1, rate: 5 }));
});
