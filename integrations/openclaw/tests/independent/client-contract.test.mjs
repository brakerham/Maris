import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";

import {
  DEFAULT_BACKEND_BASE_URL,
  DEFAULT_TIMEOUT_MS,
  FinanceProbeClient,
} from "../../dist/client.js";
import { FinanceProbeError } from "../../dist/errors.js";
import {
  SUCCESS_PROBE,
  assertProbeRequest,
  createFakeBackend,
  jsonResponse,
  textResponse,
} from "./fake-backend.mjs";

async function expectProbeError(promise, code, retryable) {
  await assert.rejects(
    promise,
    (error) =>
      error instanceof FinanceProbeError &&
      error.code === code &&
      error.retryable === retryable &&
      error.message.length > 0 &&
      !error.message.includes("PRIVATE_"),
  );
}

test("B2B-C01/C02: real HTTP success and replay preserve the backend response", async () => {
  const replies = [SUCCESS_PROBE, { ...SUCCESS_PROBE, replayed: true }];
  const backend = await createFakeBackend((request, call) => {
    assertProbeRequest(request, { challenge: "V001", idempotencyKey: "trusted-call-001" });
    assert.equal(request.headers.accept, "application/json");
    assert.equal(request.headers["content-type"], "application/json");
    assert.deepEqual(Object.keys(request.json), ["challenge"]);
    return jsonResponse(200, replies[call - 1]);
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: backend.baseUrl });
    assert.deepEqual(await client.createProbe("V001", "trusted-call-001"), SUCCESS_PROBE);
    assert.deepEqual(await client.createProbe("V001", "trusted-call-001"), replies[1]);
    assert.equal(backend.requests.length, 2);
  } finally {
    await backend.close();
  }
});

test("health accepts only the exact frozen payload", async (t) => {
  const cases = [
    [{ status: "ok", service: "wife-system" }, true],
    [{ status: "ok", service: "wife-system", private: "PRIVATE_HEALTH" }, false],
    [{ status: "ok", service: "other" }, false],
  ];
  for (const [index, [payload, valid]] of cases.entries()) {
    await t.test(String(index), async () => {
      const backend = await createFakeBackend((request) => {
        assert.equal(request.method, "GET");
        assert.equal(request.url, "/healthz");
        assert.equal(request.rawBody, "");
        return jsonResponse(200, payload);
      });
      try {
        const result = new FinanceProbeClient({ baseUrl: backend.baseUrl }).health();
        if (valid) {
          assert.deepEqual(await result, payload);
        } else {
          await expectProbeError(result, "invalid_backend_response", false);
        }
      } finally {
        await backend.close();
      }
    });
  }
});

test("B2B-C03/C04/C05: status mapping is stable and never retries implicitly", async (t) => {
  for (const [status, code, retryable] of [
    [409, "duplicate_request_conflict", false],
    [422, "invalid_request", false],
    [500, "backend_unavailable", true],
    [503, "backend_unavailable", true],
  ]) {
    await t.test(String(status), async () => {
      const backend = await createFakeBackend(() =>
        jsonResponse(status, {
          request_id: SUCCESS_PROBE.request_id,
          detail: "PRIVATE_BACKEND_BODY",
        }),
      );
      try {
        const client = new FinanceProbeClient({ baseUrl: backend.baseUrl });
        await expectProbeError(client.createProbe("V001", `status-${status}`), code, retryable);
        assert.equal(backend.requests.length, 1);
      } finally {
        await backend.close();
      }
    });
  }
});

test("B2B-C06/C07/C08/C09: every malformed success response is rejected", async (t) => {
  const badPayloads = [
    textResponse(200, "PRIVATE_TRUNCATED_{"),
    jsonResponse(200, { ...SUCCESS_PROBE, request_id: undefined }),
    jsonResponse(200, { ...SUCCESS_PROBE, challenge: undefined }),
    jsonResponse(200, { ...SUCCESS_PROBE, receipt: undefined }),
    jsonResponse(200, { ...SUCCESS_PROBE, created_at: undefined }),
    jsonResponse(200, { ...SUCCESS_PROBE, replayed: undefined }),
    jsonResponse(200, { ...SUCCESS_PROBE, request_id: "not-a-uuid" }),
    jsonResponse(200, { ...SUCCESS_PROBE, challenge: "PRIVATE_OTHER_CHALLENGE" }),
    jsonResponse(200, { ...SUCCESS_PROBE, receipt: "" }),
    jsonResponse(200, { ...SUCCESS_PROBE, created_at: "2026-09-14T21:40:00" }),
    jsonResponse(200, { ...SUCCESS_PROBE, created_at: "not-a-time+08:00" }),
    jsonResponse(200, { ...SUCCESS_PROBE, replayed: "false" }),
    jsonResponse(200, { ...SUCCESS_PROBE, private: "PRIVATE_EXTRA_FIELD" }),
  ];
  for (const [index, planned] of badPayloads.entries()) {
    await t.test(String(index), async () => {
      const logs = [];
      const backend = await createFakeBackend(() => planned);
      try {
        const client = new FinanceProbeClient({
          baseUrl: backend.baseUrl,
          logger: { info: (value) => logs.push(value), warn: (value) => logs.push(value) },
        });
        await expectProbeError(
          client.createProbe("V001", `bad-response-${index}`),
          "invalid_backend_response",
          false,
        );
        assert.equal(backend.requests.length, 1);
        assert.equal(JSON.stringify(logs).includes("PRIVATE_"), false);
      } finally {
        await backend.close();
      }
    });
  }
});

test("B2B-C10: timeout aborts one request and does not return a late success", async () => {
  const backend = await createFakeBackend(() => jsonResponse(200, SUCCESS_PROBE));
  await backend.close();

  let calls = 0;
  let observedAbort = false;
  const client = new FinanceProbeClient({
    baseUrl: backend.baseUrl,
    timeoutMs: 20,
    fetchImpl: async (_url, init) => {
      calls += 1;
      await new Promise((resolve) => {
        init.signal.addEventListener("abort", () => {
          observedAbort = true;
          resolve();
        }, { once: true });
      });
      throw new DOMException("PRIVATE_TIMEOUT_DETAIL", "AbortError");
    },
  });
  await expectProbeError(client.createProbe("V001", "timeout-once"), "backend_timeout", true);
  assert.equal(calls, 1);
  assert.equal(observedAbort, true);
});

test("B2B-C11: refused loopback connection is safe, retryable, and attempted once", async () => {
  const server = createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert(address && typeof address === "object");
  const baseUrl = `http://127.0.0.1:${address.port}`;
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));

  let calls = 0;
  const client = new FinanceProbeClient({
    baseUrl,
    timeoutMs: 250,
    fetchImpl: async (...args) => {
      calls += 1;
      return fetch(...args);
    },
  });
  await expectProbeError(client.createProbe("V001", "offline-once"), "backend_unavailable", true);
  assert.equal(calls, 1);
});

test("B2B-C12: caller-controlled retry reuses the same key and takes success from backend", async () => {
  const backend = await createFakeBackend((_request, call) =>
    call === 1
      ? jsonResponse(503, { detail: "PRIVATE_FIRST_FAILURE" })
      : jsonResponse(200, { ...SUCCESS_PROBE, replayed: true }),
  );
  try {
    const client = new FinanceProbeClient({ baseUrl: backend.baseUrl });
    await expectProbeError(client.createProbe("V001", "caller-retry-key"), "backend_unavailable", true);
    const result = await client.createProbe("V001", "caller-retry-key");
    assert.deepEqual(result, { ...SUCCESS_PROBE, replayed: true });
    assert.deepEqual(
      backend.requests.map((request) => request.headers["idempotency-key"]),
      ["caller-retry-key", "caller-retry-key"],
    );
  } finally {
    await backend.close();
  }
});

test("B2B-C13/C14: concurrent calls preserve keys and do not cross-wire results", async () => {
  const backend = await createFakeBackend((request) => {
    const key = request.headers["idempotency-key"];
    const suffix = key === "same-key" ? "SAME" : key.endsWith("a") ? "A" : "B";
    return jsonResponse(200, {
      ...SUCCESS_PROBE,
      receipt: `POC-C2-B2B-${suffix}`,
      replayed: key === "same-key",
    });
  });
  try {
    const client = new FinanceProbeClient({ baseUrl: backend.baseUrl });
    const same = await Promise.all([
      client.createProbe("V001", "same-key"),
      client.createProbe("V001", "same-key"),
    ]);
    assert.deepEqual(same.map((value) => value.receipt), ["POC-C2-B2B-SAME", "POC-C2-B2B-SAME"]);

    const [a, b] = await Promise.all([
      client.createProbe("V001", "different-a"),
      client.createProbe("V001", "different-b"),
    ]);
    assert.equal(a.receipt, "POC-C2-B2B-A");
    assert.equal(b.receipt, "POC-C2-B2B-B");
    assert.deepEqual(
      backend.requests.map((request) => request.headers["idempotency-key"]).sort(),
      ["different-a", "different-b", "same-key", "same-key"].sort(),
    );
  } finally {
    await backend.close();
  }
});

test("external cancellation is safe and retryable", async () => {
  let observedAbort = false;
  const client = new FinanceProbeClient({
    fetchImpl: async (_url, init) => {
      await new Promise((resolve) => init.signal.addEventListener("abort", () => {
        observedAbort = true;
        resolve();
      }, { once: true }));
      throw new DOMException("PRIVATE_ABORT_DETAIL", "AbortError");
    },
  });
  const controller = new AbortController();
  const pending = client.createProbe("V001", "cancelled-call", controller.signal);
  controller.abort();
  await expectProbeError(pending, "backend_unavailable", true);
  assert.equal(observedAbort, true);
});

test("B2B-C15: invalid configuration and input fail before network access", async () => {
  assert.equal(DEFAULT_BACKEND_BASE_URL, "http://127.0.0.1:8000");
  assert.equal(DEFAULT_TIMEOUT_MS, 5000);
  for (const baseUrl of [
    "file:///PRIVATE_PATH",
    "http://127.0.0.1.evil.invalid",
    "http://localhost.evil.invalid",
    "http://user:pass@127.0.0.1:8000",
    "http://127.0.0.1:8000?PRIVATE_QUERY=1",
    "http://127.0.0.1:8000/#PRIVATE_FRAGMENT",
  ]) {
    assert.throws(() => new FinanceProbeClient({ baseUrl }), FinanceProbeError);
  }
  for (const timeoutMs of [0, -1, Number.NaN, Number.POSITIVE_INFINITY, 1.5]) {
    assert.throws(() => new FinanceProbeClient({ timeoutMs }), FinanceProbeError);
  }

  let calls = 0;
  const client = new FinanceProbeClient({ fetchImpl: async () => {
    calls += 1;
    throw new Error("network must not run");
  } });
  for (const [challenge, key] of [
    ["", "key"],
    [" ", "key"],
    ["x".repeat(129), "key"],
    ["V001", ""],
    ["V001", " "],
    ["V001", "x".repeat(257)],
  ]) {
    await expectProbeError(client.createProbe(challenge, key), "invalid_request", false);
  }
  assert.equal(calls, 0);
});

test("success and failure logs contain only allowlisted operational fields", async () => {
  const canaries = [
    "PRIVATE_CHALLENGE_701",
    "PRIVATE_KEY_702",
    "PRIVATE_BACKEND_BODY_703",
    "PRIVATE_SENDER_704",
    "PRIVATE_ACCOUNT_705",
  ];
  const logs = [];
  let call = 0;
  const client = new FinanceProbeClient({
    logger: { info: (value) => logs.push(value), warn: (value) => logs.push(value) },
    fetchImpl: async () => {
      call += 1;
      if (call === 1) {
        return new Response(JSON.stringify({ ...SUCCESS_PROBE, challenge: canaries[0] }), { status: 200 });
      }
      return new Response(JSON.stringify({ detail: canaries[2] }), { status: 500 });
    },
  });
  await client.createProbe(canaries[0], canaries[1]);
  await expectProbeError(client.createProbe(canaries[0], canaries[1]), "backend_unavailable", true);

  assert.equal(logs.length, 2);
  const parsed = logs.map((entry) => JSON.parse(entry));
  assert.deepEqual(Object.keys(parsed[0]).sort(), ["duration_ms", "event", "receipt", "replayed", "request_id"].sort());
  assert.deepEqual(Object.keys(parsed[1]).sort(), ["code", "duration_ms", "event", "retryable"].sort());
  const output = JSON.stringify(logs);
  for (const canary of canaries) {
    assert.equal(output.includes(canary), false);
  }
});
