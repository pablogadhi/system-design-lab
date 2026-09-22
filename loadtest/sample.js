// k6 load test for the sample design.   make load   (S=loadtest/<file>.js for others)
// Pattern for designs: express the spec's scaled-down NFRs as `thresholds` so the run fails when
// the design misses them — e.g. "p95 write latency < 100ms at 200 rps".
import http from "k6/http";
import { check } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8080";

export const options = {
  scenarios: {
    writes: {
      executor: "constant-arrival-rate",
      rate: 100, timeUnit: "1s", duration: "1m",
      preAllocatedVUs: 50, maxVUs: 200,
      exec: "write",
    },
    reads: {
      executor: "constant-arrival-rate",
      rate: 200, timeUnit: "1s", duration: "1m",
      preAllocatedVUs: 50, maxVUs: 200,
      exec: "read",
    },
  },
  thresholds: {
    "http_req_failed": ["rate<0.01"],
    "http_req_duration{scenario:writes}": ["p(95)<150"],
    "http_req_duration{scenario:reads}": ["p(95)<100"],
  },
};

export function write() {
  const res = http.post(`${BASE}/api/sample-api/items`, JSON.stringify({ name: `k6-${__VU}-${__ITER}` }), {
    headers: { "Content-Type": "application/json" },
  });
  check(res, { "201": (r) => r.status === 201 });
}

export function read() {
  const res = http.get(`${BASE}/api/sample-api/items?limit=10&source=replica`);
  check(res, { "200": (r) => r.status === 200 });
}
