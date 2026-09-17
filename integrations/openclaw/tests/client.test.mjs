import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";

import {
  DEFAULT_BACKEND_BASE_URL,
  DEFAULT_TIMEOUT_MS,
  FinanceProbeClient,
} from "../dist/client.js";
import { FinanceProbeError } from "../dist/errors.js";

const RECEIPT = {
  request_id: "123e4567-e89b-42d3-a456-426614174000",
  challenge: "V001",
  receipt: "POC-0123456789abcdef01234567",
  created_at: "2026-09-14T21:00:00+08:00",
  replayed: false,
};

async function startServer(handler) {
  const server = createServer(handler);
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert.equal(typeof address, "object");
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve()))),
  };
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function sendJson(response, status, value) {
  response.writeHead(status, { "content-type": "application/json" });
  response.end(JSON.stringify(value));
}

async function expectCode(promise, code) {
  await assert.rejects(promise, (error) => error instanceof FinanceProbeError && error.code === code);
}

test("defaults are fixed to the local Python service and five seconds", async () => {
  let observedUrl;
  const client = new FinanceProbeClient({
    fetchImpl: async (url) => {
      observedUrl = String(url);
      return new Response(JSON.stringify({ status: "ok", service: "wife-system" }));
    },
  });
  assert.equal(DEFAULT_TIMEOUT_MS, 5000);
  assert.equal(DEFAULT_BACKEND_BASE_URL, "http://127.0.0.1:8000");
  await client.health();
  assert.equal(observedUrl, "http://127.0.0.1:8000/healthz");
});

test("health check accepts only the exact healthy payload", async () => {
  const fake = await startServer((request, response) => {
    assert.equal(request.url, "/healthz");
    assert.equal(request.method, "GET");
    sendJson(response, 200, { status: "ok", service: "wife-system" });
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
    assert.deepEqual(await client.health(), { status: "ok", service: "wife-system" });
  } finally {
    await fake.close();
  }
});

test("probe forwards the exact body and idempotency header", async () => {
  const fake = await startServer(async (request, response) => {
    assert.equal(request.url, "/api/v1/probes");
    assert.equal(request.method, "POST");
    assert.equal(request.headers["idempotency-key"], "source-event-001");
    assert.deepEqual(await readJson(request), { challenge: "V001" });
    sendJson(response, 200, RECEIPT);
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
    assert.deepEqual(
      await client.createProbe("V001", "source-event-001"),
      RECEIPT,
    );
  } finally {
    await fake.close();
  }
});

test("same key replay is returned from the backend without bridge-generated receipts", async () => {
  let calls = 0;
  const fake = await startServer((_request, response) => {
    calls += 1;
    sendJson(response, 200, { ...RECEIPT, replayed: calls > 1 });
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
    const first = await client.createProbe("V001", "same-event");
    const replay = await client.createProbe("V001", "same-event");
    assert.equal(first.receipt, RECEIPT.receipt);
    assert.equal(replay.receipt, RECEIPT.receipt);
    assert.equal(replay.request_id, RECEIPT.request_id);
    assert.equal(replay.replayed, true);
  } finally {
    await fake.close();
  }
});

test("concurrent calls preserve the backend idempotent result", async () => {
  const keys = [];
  const fake = await startServer((request, response) => {
    keys.push(request.headers["idempotency-key"]);
    setTimeout(() => sendJson(response, 200, RECEIPT), 20);
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
    const results = await Promise.all(
      Array.from({ length: 12 }, () =>
        client.createProbe("V001", "concurrent-event"),
      ),
    );
    assert.equal(new Set(keys).size, 1);
    assert.equal(new Set(results.map((value) => value.receipt)).size, 1);
    assert.equal(results[0].receipt, RECEIPT.receipt);
  } finally {
    await fake.close();
  }
});

test("maps 409, 422, and 500 to stable errors", async (t) => {
  for (const [status, code] of [
    [409, "duplicate_request_conflict"],
    [422, "invalid_request"],
    [500, "backend_unavailable"],
  ]) {
    await t.test(String(status), async () => {
      const fake = await startServer((_request, response) => {
        sendJson(response, status, { detail: "PRIVATE_BACKEND_BODY" });
      });
      try {
        const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
        await expectCode(
          client.createProbe("V001", `event-${status}`),
          code,
        );
      } finally {
        await fake.close();
      }
    });
  }
});

test("rejects malformed JSON, missing fields, extra fields, and challenge mismatch", async (t) => {
  const cases = [
    "not-json",
    JSON.stringify({ ...RECEIPT, receipt: undefined }),
    JSON.stringify({ ...RECEIPT, extra: true }),
    JSON.stringify({ ...RECEIPT, challenge: "PRIVATE_OTHER" }),
  ];
  for (const [index, body] of cases.entries()) {
    await t.test(String(index), async () => {
      const fake = await startServer((_request, response) => {
        response.writeHead(200, { "content-type": "application/json" });
        response.end(body);
      });
      try {
        const client = new FinanceProbeClient({ baseUrl: fake.baseUrl });
        await expectCode(
          client.createProbe("V001", `bad-response-${index}`),
          "invalid_backend_response",
        );
      } finally {
        await fake.close();
      }
    });
  }
});

test("timeout is retryable and does not return success", async () => {
  const fake = await startServer((_request, response) => {
    setTimeout(() => sendJson(response, 200, RECEIPT), 100);
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: fake.baseUrl, timeoutMs: 10 });
    await assert.rejects(
      client.createProbe("V001", "timeout-event"),
      (error) => error instanceof FinanceProbeError && error.code === "backend_timeout" && error.retryable,
    );
  } finally {
    await fake.close();
  }
});

test("refused connection is a retryable unavailable error", async () => {
  const fake = await startServer((_request, response) => sendJson(response, 200, RECEIPT));
  const baseUrl = fake.baseUrl;
  await fake.close();
  const client = new FinanceProbeClient({ baseUrl, timeoutMs: 250 });
  await assert.rejects(
    client.createProbe("V001", "offline-event"),
    (error) => error instanceof FinanceProbeError && error.code === "backend_unavailable" && error.retryable,
  );
});

test("redirects are rejected before probe data can leave the configured loopback service", async () => {
  let redirectedRequests = 0;
  const target = await startServer((_request, response) => {
    redirectedRequests += 1;
    sendJson(response, 200, RECEIPT);
  });
  const source = await startServer((_request, response) => {
    response.writeHead(302, { location: `${target.baseUrl}/private-target` });
    response.end();
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: source.baseUrl });
    await expectCode(client.createProbe("V001", "redirect-event"), "backend_unavailable");
    assert.equal(redirectedRequests, 0);
  } finally {
    await source.close();
    await target.close();
  }
});

test("logs never contain challenge, key, backend body, or exception text", async () => {
  const canaries = ["PRIVATE_CHALLENGE_781", "PRIVATE_KEY_782", "PRIVATE_BACKEND_BODY", "PRIVATE_THROW_783"];
  const entries = [];
  const client = new FinanceProbeClient({
    fetchImpl: async () => new Response(JSON.stringify({ detail: canaries[2] }), { status: 500 }),
    logger: {
      info: (entry) => entries.push(entry),
      warn: (entry) => entries.push(entry),
    },
  });
  await expectCode(
    client.createProbe(canaries[0], canaries[1]),
    "backend_unavailable",
  );
  const output = JSON.stringify(entries);
  for (const canary of canaries) {
    assert.equal(output.includes(canary), false);
  }
  assert.match(output, /backend_unavailable/);
});

test("invalid local configuration and request input fail before fetch", async () => {
  assert.throws(() => new FinanceProbeClient({ baseUrl: "file:///private" }), FinanceProbeError);
  assert.throws(() => new FinanceProbeClient({ timeoutMs: 0 }), FinanceProbeError);
  let fetched = false;
  const client = new FinanceProbeClient({ fetchImpl: async () => {
    fetched = true;
    return new Response();
  } });
  await expectCode(client.createProbe(" ", "valid"), "invalid_request");
  await expectCode(client.createProbe("V001", " ".repeat(3)), "invalid_request");
  assert.equal(fetched, false);
});
