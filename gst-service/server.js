/**
 * gst-service  (Node.js + Express)  -> listens on port 3000
 *
 * Endpoints
 *   GET  /health      liveness/readiness check used by Docker & Kubernetes
 *   GET  /rates       list of valid GST rates
 *   POST /calculate   {"amount": 1000, "rate": 18, "inclusive": false, "interstate": false}
 */
const express = require("express");
const os = require("os");
const { calculateGst, ALLOWED_RATES } = require("./gst");

const app = express();
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({
    status: "UP",
    service: "gst-service",
    version: process.env.APP_VERSION || "dev",
    host: os.hostname(), // shows which pod answered
  });
});

app.get("/rates", (req, res) => res.json({ rates: ALLOWED_RATES }));

app.post("/calculate", (req, res) => {
  try {
    res.json(calculateGst(req.body || {}));
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// only start listening when run directly (not when imported by tests)
if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`gst-service listening on ${port}`));
}

module.exports = app;
