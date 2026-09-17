import assert from "node:assert/strict";
import { createServer } from "node:http";

export const SUCCESS_PROBE = Object.freeze({
  request_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  challenge: "V001",
  receipt: "POC-C2-B2B-BACKEND-RECEIPT",
  created_at: "2026-09-14T21:40:00+08:00",
  replayed: false,
});

export function jsonResponse(status, payload, headers = {}) {
  return {
    status,
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(payload),
  };
}

export function textResponse(status, body, headers = {}) {
  return {
    status,
    headers: { "content-type": "text/plain; charset=utf-8", ...headers },
    body,
  };
}

export async function createFakeBackend(handler) {
  const requests = [];
  const waiters = [];
  const server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) {
      chunks.push(chunk);
    }
    const rawBody = Buffer.concat(chunks).toString("utf8");
    let json;
    try {
      json = JSON.parse(rawBody);
    } catch {
      json = undefined;
    }
    const observed = {
      method: request.method,
      url: request.url,
      headers: { ...request.headers },
      rawBody,
      json,
      aborted: request.aborted,
      responseClosed: false,
    };
    request.once("aborted", () => {
      observed.aborted = true;
    });
    response.once("close", () => {
      observed.responseClosed = true;
    });
    requests.push(observed);
    for (const waiter of waiters.splice(0)) {
      waiter();
    }

    const planned = await handler(observed, requests.length);
    if (planned.delayMs) {
      await new Promise((resolve) => setTimeout(resolve, planned.delayMs));
    }
    if (response.destroyed) {
      return;
    }
    response.writeHead(planned.status, planned.headers ?? {});
    response.end(planned.body ?? "");
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert(address && typeof address === "object");

  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    requests,
    async waitForRequests(count, timeoutMs = 1_000) {
      const deadline = Date.now() + timeoutMs;
      while (requests.length < count) {
        const remaining = deadline - Date.now();
        assert(remaining > 0, `expected ${count} requests, observed ${requests.length}`);
        await Promise.race([
          new Promise((resolve) => waiters.push(resolve)),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error("fake backend request timeout")), remaining),
          ),
        ]);
      }
      return requests;
    },
    async close() {
      if (!server.listening) {
        return;
      }
      await new Promise((resolve, reject) =>
        server.close((error) => (error ? reject(error) : resolve())),
      );
    },
  };
}

export function assertProbeRequest(request, { challenge, idempotencyKey }) {
  assert.equal(request.method, "POST");
  assert.equal(request.url, "/api/v1/probes");
  assert.deepEqual(request.json, { challenge });
  assert.equal(request.headers["idempotency-key"], idempotencyKey);
}
