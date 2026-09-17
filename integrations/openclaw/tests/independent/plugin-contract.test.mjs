import assert from "node:assert/strict";
import test from "node:test";

import plugin, { registerFinanceProbePlugin } from "../../dist/index.js";
import { FinanceProbeError } from "../../dist/errors.js";
import {
  SUCCESS_PROBE,
  createFakeBackend,
  jsonResponse,
} from "./fake-backend.mjs";

function createApi(pluginConfig) {
  const commands = [];
  const tools = [];
  const logs = [];
  return {
    api: {
      pluginConfig,
      logger: {
        info(value) { logs.push(value); },
        warn(value) { logs.push(value); },
        error(value) { logs.push(value); },
      },
      registerCommand(command) { commands.push(command); },
      registerTool(tool) { tools.push(tool); },
    },
    commands,
    tools,
    logs,
  };
}

function registerWithPort(port, options = {}) {
  const fixture = createApi(options.pluginConfig);
  registerFinanceProbePlugin(fixture.api, {
    clientFactory: () => port,
    ...(options.invocationIdFactory
      ? { invocationIdFactory: options.invocationIdFactory }
      : {}),
  });
  return fixture;
}

test("B2B-P01/P02: entry registers exactly one authenticated command and one strict tool", () => {
  const fixture = registerWithPort({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async () => SUCCESS_PROBE,
  });

  assert.equal(plugin.id, "wife-system-finance-probe");
  assert.equal(typeof plugin.register, "function");
  assert.equal(fixture.commands.length, 1);
  assert.equal(fixture.commands[0].name, "finance-probe");
  assert.equal(fixture.commands[0].acceptsArgs, true);
  assert.equal(fixture.commands[0].requireAuth, true);
  assert.equal(typeof fixture.commands[0].handler, "function");
  assert.equal(fixture.tools.length, 1);
  assert.equal(fixture.tools[0].name, "finance_probe");
  assert.equal(fixture.tools[0].parameters.additionalProperties, false);
  assert.deepEqual(Object.keys(fixture.tools[0].parameters.properties), ["challenge"]);
  assert.equal(fixture.tools[0].parameters.properties.challenge.minLength, 1);
  assert.equal(fixture.tools[0].parameters.properties.challenge.maxLength, 128);
  assert.ok(fixture.tools[0].outputSchema);
});

test("B2B-P03/P04: command uses a fresh invocation UUID and only backend success fields", async () => {
  const invocationIds = [
    "10000000-0000-4000-8000-000000000001",
    "10000000-0000-4000-8000-000000000002",
  ];
  const calls = [];
  const fixture = registerWithPort(
    {
      health: async () => ({ status: "ok", service: "wife-system" }),
      createProbe: async (challenge, key) => {
        calls.push({ challenge, key });
        return { ...SUCCESS_PROBE, replayed: calls.length > 1 };
      },
    },
    { invocationIdFactory: () => invocationIds.shift() },
  );
  const privateContext = {
    args: " V001 ",
    senderId: "PRIVATE_SENDER_801",
    from: "PRIVATE_FROM_802",
    to: "PRIVATE_TO_803",
    accountId: "PRIVATE_ACCOUNT_804",
    sessionKey: "PRIVATE_SESSION_805",
    commandBody: "PRIVATE_COMMAND_BODY_806",
  };

  const first = await fixture.commands[0].handler(privateContext);
  const second = await fixture.commands[0].handler(privateContext);
  assert.deepEqual(calls, [
    { challenge: "V001", key: "10000000-0000-4000-8000-000000000001" },
    { challenge: "V001", key: "10000000-0000-4000-8000-000000000002" },
  ]);
  assert.equal(first.text, [
    `request_id: ${SUCCESS_PROBE.request_id}`,
    `receipt: ${SUCCESS_PROBE.receipt}`,
    `created_at: ${SUCCESS_PROBE.created_at}`,
    "replayed: false",
  ].join("\n"));
  assert.match(second.text, /replayed: true$/);
  const observable = JSON.stringify({ first, second, logs: fixture.logs });
  for (const value of Object.values(privateContext).filter((value) => String(value).startsWith("PRIVATE_"))) {
    assert.equal(observable.includes(value), false);
  }
});

test("B2B-P06/P07: tool passes the exact call ID and returns backend fields unchanged", async () => {
  const calls = [];
  const replay = { ...SUCCESS_PROBE, replayed: true };
  const fixture = registerWithPort({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async (challenge, key, signal) => {
      calls.push({ challenge, key, signal });
      return replay;
    },
  });
  const signal = new AbortController().signal;
  const results = await Promise.all([
    fixture.tools[0].execute("trusted-tool-call-901", { challenge: "V001" }, signal),
    fixture.tools[0].execute("trusted-tool-call-901", { challenge: "V001" }, signal),
  ]);

  assert.deepEqual(calls.map(({ challenge, key }) => ({ challenge, key })), [
    { challenge: "V001", key: "trusted-tool-call-901" },
    { challenge: "V001", key: "trusted-tool-call-901" },
  ]);
  assert.equal(calls.every((call) => call.signal === signal), true);
  for (const result of results) {
    assert.deepEqual(result.details, replay);
    assert.equal(result.isError, undefined);
    assert.equal(result.content.length, 1);
    assert.equal(result.content[0].type, "text");
    assert.match(result.content[0].text, new RegExp(SUCCESS_PROBE.receipt));
    assert.equal(result.content[0].text.includes("trusted-tool-call-901"), false);
  }
});

test("B2B-P05/P09: actual client errors expose stable safe output and safe logs", async () => {
  const privateValues = [
    "PRIVATE_CHALLENGE_911",
    "PRIVATE_SENDER_912",
    "PRIVATE_FROM_913",
    "PRIVATE_ACCOUNT_914",
    "PRIVATE_BACKEND_BODY_915",
  ];
  const backend = await createFakeBackend(() =>
    jsonResponse(503, { detail: privateValues[4], stack: "PRIVATE_STACK_916" }),
  );
  try {
    const fixture = createApi({ backendBaseUrl: backend.baseUrl, timeoutMs: 500 });
    const ids = [
      "20000000-0000-4000-8000-000000000001",
      "20000000-0000-4000-8000-000000000002",
    ];
    registerFinanceProbePlugin(fixture.api, { invocationIdFactory: () => ids.shift() });

    const commandResult = await fixture.commands[0].handler({
      args: privateValues[0],
      senderId: privateValues[1],
      from: privateValues[2],
      accountId: privateValues[3],
    });
    const toolResult = await fixture.tools[0].execute("trusted-tool-error-917", {
      challenge: privateValues[0],
    });

    assert.equal(commandResult.text, "backend_unavailable: The probe service is unavailable.");
    assert.deepEqual(toolResult.details, {
      error: {
        code: "backend_unavailable",
        message: "The probe service is unavailable.",
        retryable: true,
      },
    });
    assert.equal(toolResult.isError, true);
    assert.equal(backend.requests.length, 2);
    const observable = JSON.stringify({ commandResult, toolResult, logs: fixture.logs });
    for (const value of [...privateValues, "PRIVATE_STACK_916", "trusted-tool-error-917"]) {
      assert.equal(observable.includes(value), false);
    }
  } finally {
    await backend.close();
  }
});

test("B2B-P08: tool forwards cancellation and returns a safe retryable error", async () => {
  let receivedSignal;
  const fixture = registerWithPort({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async (_challenge, _key, signal) => {
      receivedSignal = signal;
      throw new FinanceProbeError("backend_unavailable");
    },
  });
  const controller = new AbortController();
  controller.abort();
  const result = await fixture.tools[0].execute(
    "cancelled-tool-call",
    { challenge: "PRIVATE_ABORT_CHALLENGE" },
    controller.signal,
  );
  assert.equal(receivedSignal, controller.signal);
  assert.equal(receivedSignal.aborted, true);
  assert.equal(result.isError, true);
  assert.deepEqual(result.details.error, {
    code: "backend_unavailable",
    message: "The probe service is unavailable.",
    retryable: true,
  });
  assert.equal(JSON.stringify(result).includes("PRIVATE_ABORT_CHALLENGE"), false);
});

test("configuration is passed exactly and invalid shapes fail before registration", () => {
  let observedOptions;
  const fixture = createApi({ backendBaseUrl: "http://127.0.0.1:8123/prefix", timeoutMs: 25 });
  registerFinanceProbePlugin(fixture.api, {
    clientFactory: (options) => {
      observedOptions = options;
      return {
        health: async () => ({ status: "ok", service: "wife-system" }),
        createProbe: async () => SUCCESS_PROBE,
      };
    },
  });
  assert.equal(observedOptions.baseUrl, "http://127.0.0.1:8123/prefix");
  assert.equal(observedOptions.timeoutMs, 25);
  assert.equal(observedOptions.logger, fixture.api.logger);

  for (const pluginConfig of [
    null,
    [],
    "PRIVATE_CONFIG",
    { extra: true },
    { backendBaseUrl: 123 },
    { timeoutMs: "5000" },
  ]) {
    const invalid = createApi(pluginConfig);
    assert.throws(
      () => registerFinanceProbePlugin(invalid.api),
      (error) => error instanceof FinanceProbeError && error.code === "invalid_request",
    );
    assert.equal(invalid.commands.length, 0);
    assert.equal(invalid.tools.length, 0);
  }
});

test("default plugin registration uses the runtime API without extra host dependencies", () => {
  const fixture = createApi({ backendBaseUrl: "http://127.0.0.1:8000", timeoutMs: 5000 });
  assert.doesNotThrow(() => plugin.register(fixture.api));
  assert.equal(fixture.commands.length, 1);
  assert.equal(fixture.tools.length, 1);
});
