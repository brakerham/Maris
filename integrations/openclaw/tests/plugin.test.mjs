import assert from "node:assert/strict";
import test from "node:test";

import plugin, { registerFinanceProbePlugin } from "../dist/index.js";
import { FinanceProbeError } from "../dist/errors.js";

const RECEIPT = {
  request_id: "123e4567-e89b-42d3-a456-426614174000",
  challenge: "V001",
  receipt: "POC-0123456789abcdef01234567",
  created_at: "2026-09-14T21:00:00+08:00",
  replayed: false,
};

function createFakeApi(options = {}) {
  const commands = [];
  const tools = [];
  const logs = [];
  return {
    api: {
      pluginConfig: options.pluginConfig,
      logger: {
        info(message) { logs.push(message); },
        warn(message) { logs.push(message); },
        error() {},
      },
      registerCommand(command) { commands.push(command); },
      registerTool(tool) { tools.push(tool); },
    },
    commands,
    tools,
    logs,
  };
}

function registerWithClient(client, options = {}) {
  const fixture = createFakeApi(options);
  registerFinanceProbePlugin(fixture.api, {
    clientFactory: () => client,
    invocationIdFactory: options.invocationIdFactory,
  });
  return fixture;
}

test("entry identity matches the manifest and exposes registration", () => {
  assert.equal(plugin.id, "wife-system-finance-probe");
  assert.equal(plugin.name, "Wife System Finance Probe");
  assert.equal(typeof plugin.register, "function");
});

test("registers one authenticated deterministic command and one labeled tool", () => {
  const fixture = registerWithClient({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async () => RECEIPT,
  });
  assert.deepEqual(fixture.commands.map((value) => value.name), ["finance-probe"]);
  assert.equal(fixture.commands[0].requireAuth, true);
  assert.equal(fixture.commands[0].acceptsArgs, true);
  assert.deepEqual(fixture.tools.map((value) => value.name), ["finance_probe"]);
  assert.equal(fixture.tools[0].label, "Finance Probe");
  assert.equal(fixture.tools[0].parameters.additionalProperties, false);
  assert.ok(fixture.tools[0].outputSchema);
});

test("command returns backend receipt fields and uses a fresh invocation UUID", async () => {
  const calls = [];
  const ids = [
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000002",
  ];
  const fixture = registerWithClient(
    {
      health: async () => ({ status: "ok", service: "wife-system" }),
      createProbe: async (challenge, key) => {
        calls.push({ challenge, key });
        return RECEIPT;
      },
    },
    { invocationIdFactory: () => ids.shift() },
  );
  const privateContext = {
    args: " V001 ",
    senderId: "PRIVATE_SENDER",
    from: "PRIVATE_FROM",
    accountId: "PRIVATE_ACCOUNT",
    commandBody: "PRIVATE_COMMAND_BODY",
  };
  const first = await fixture.commands[0].handler(privateContext);
  await fixture.commands[0].handler(privateContext);
  assert.match(first.text, /123e4567-e89b-42d3-a456-426614174000/);
  assert.match(first.text, /POC-0123456789abcdef01234567/);
  assert.match(first.text, /2026-09-14T21:00:00\+08:00/);
  assert.match(first.text, /replayed: false/);
  assert.deepEqual(calls, [
    { challenge: "V001", key: "00000000-0000-4000-8000-000000000001" },
    { challenge: "V001", key: "00000000-0000-4000-8000-000000000002" },
  ]);
});

test("tool passes the trusted tool call ID through unchanged", async () => {
  const calls = [];
  const fixture = registerWithClient({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async (challenge, key) => {
      calls.push({ challenge, key });
      return RECEIPT;
    },
  });
  const tool = fixture.tools[0];
  const [first, second] = await Promise.all([
    tool.execute("trusted-call-001", { challenge: "V001" }),
    tool.execute("trusted-call-001", { challenge: "V001" }),
  ]);
  assert.deepEqual(calls, [
    { challenge: "V001", key: "trusted-call-001" },
    { challenge: "V001", key: "trusted-call-001" },
  ]);
  assert.deepEqual(first.details, RECEIPT);
  assert.deepEqual(second.details, RECEIPT);
  assert.equal(first.content[0].text.includes("trusted-call-001"), false);
});

test("command and tool failures expose stable safe errors", async () => {
  const privateValues = ["PRIVATE_CHALLENGE_901", "PRIVATE_EXCEPTION_902"];
  const fixture = registerWithClient({
    health: async () => ({ status: "ok", service: "wife-system" }),
    createProbe: async () => {
      throw new FinanceProbeError("backend_unavailable");
    },
  });
  const commandResult = await fixture.commands[0].handler({ args: privateValues[0] });
  const toolResult = await fixture.tools[0].execute("private-tool-call", {
    challenge: privateValues[0],
  });
  const observable = JSON.stringify({ commandResult, toolResult, logs: fixture.logs });
  assert.match(commandResult.text, /^backend_unavailable:/);
  assert.equal(commandResult.isError, true);
  assert.equal(toolResult.isError, true);
  assert.equal(toolResult.details.error.code, "backend_unavailable");
  for (const value of privateValues) {
    assert.equal(observable.includes(value), false);
  }
});

test("configured backend and timeout are passed to the shared client factory", () => {
  let observed;
  const fixture = createFakeApi({
    pluginConfig: { backendBaseUrl: "http://127.0.0.1:8123/", timeoutMs: 25 },
  });
  registerFinanceProbePlugin(fixture.api, {
    clientFactory: (options) => {
      observed = options;
      return {
        health: async () => ({ status: "ok", service: "wife-system" }),
        createProbe: async () => RECEIPT,
      };
    },
  });
  assert.equal(observed.baseUrl, "http://127.0.0.1:8123/");
  assert.equal(observed.timeoutMs, 25);
  assert.equal(observed.logger, fixture.api.logger);
});
