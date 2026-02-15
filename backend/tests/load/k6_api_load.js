/**
 * Control Tower – k6 Load Test Suite
 *
 * Profiles:
 *   - smoke:  5 VUs, 30s  (CI gate)
 *   - load:   50 VUs, 5m  (pre-release)
 *   - stress: 200 VUs, 10m (capacity planning)
 *   - soak:   30 VUs, 1h  (memory leak detection)
 *
 * Run: k6 run --env PROFILE=load backend/tests/load/k6_api_load.js
 */

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const PROFILE = __ENV.PROFILE || "smoke";

const profiles = {
  smoke:  { vus: 5,   duration: "30s",  thresholds: { p95: 1000, p99: 2000, error_rate: 0.01 } },
  load:   { vus: 50,  duration: "5m",   thresholds: { p95: 500,  p99: 1500, error_rate: 0.01 } },
  stress: { vus: 200, duration: "10m",  thresholds: { p95: 2000, p99: 5000, error_rate: 0.05 } },
  soak:   { vus: 30,  duration: "60m",  thresholds: { p95: 500,  p99: 1500, error_rate: 0.01 } },
};

const cfg = profiles[PROFILE];

export const options = {
  vus: cfg.vus,
  duration: cfg.duration,
  thresholds: {
    http_req_duration: [`p(95)<${cfg.thresholds.p95}`, `p(99)<${cfg.thresholds.p99}`],
    http_req_failed: [`rate<${cfg.thresholds.error_rate}`],
    checks: ["rate>0.99"],
  },
  tags: { profile: PROFILE },
};

const errorRate = new Rate("errors");
const apiDuration = new Trend("api_duration");

export default function () {
  group("Health Check", () => {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { "health 200": (r) => r.status === 200 });
    apiDuration.add(res.timings.duration);
  });

  group("Dashboard Summary", () => {
    const res = http.get(`${BASE_URL}/api/v1/dashboard/summary`);
    check(res, {
      "dashboard 200": (r) => r.status === 200,
      "has inventory": (r) => JSON.parse(r.body).inventory !== undefined,
    });
    errorRate.add(res.status !== 200);
    apiDuration.add(res.timings.duration);
  });

  group("List Models", () => {
    const res = http.get(`${BASE_URL}/api/v1/models?page=1&page_size=20`);
    check(res, { "models 200": (r) => r.status === 200 });
    apiDuration.add(res.timings.duration);
  });

  group("List Use Cases", () => {
    const res = http.get(`${BASE_URL}/api/v1/use-cases?page=1&page_size=20`);
    check(res, { "use-cases 200": (r) => r.status === 200 });
    apiDuration.add(res.timings.duration);
  });

  group("List Evaluations", () => {
    const res = http.get(`${BASE_URL}/api/v1/evaluations?page=1&page_size=20`);
    check(res, { "evals 200": (r) => r.status === 200 });
    apiDuration.add(res.timings.duration);
  });

  group("List Findings", () => {
    const res = http.get(`${BASE_URL}/api/v1/findings?page=1&page_size=20`);
    check(res, { "findings 200": (r) => r.status === 200 });
    apiDuration.add(res.timings.duration);
  });

  group("Compliance Matrix", () => {
    const res = http.get(`${BASE_URL}/api/v1/dashboard/compliance-matrix`);
    check(res, {
      "compliance 200": (r) => r.status === 200,
      "has owasp": (r) => JSON.parse(r.body).owasp_llm_top10_2025 !== undefined,
    });
    apiDuration.add(res.timings.duration);
  });

  group("Create + Read Vendor", () => {
    const payload = JSON.stringify({
      name: `Load Test Vendor ${Date.now()}`,
      security_posture: "under_review",
    });
    const createRes = http.post(`${BASE_URL}/api/v1/vendors`, payload, {
      headers: { "Content-Type": "application/json" },
    });
    check(createRes, { "vendor created": (r) => r.status === 201 });

    if (createRes.status === 201) {
      const id = JSON.parse(createRes.body).id;
      const getRes = http.get(`${BASE_URL}/api/v1/vendors/${id}`);
      check(getRes, { "vendor read": (r) => r.status === 200 });
    }
    apiDuration.add(createRes.timings.duration);
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    "load-test-results.json": JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
  };
}

function textSummary(data, opts) {
  // k6 built-in summary handles this
  return "";
}
