import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { z } from "zod";
import type { OwnedChild, SupervisorPort } from "./backend-supervisor";

const handshakeSchema = z.strictObject({
  protocol: z.literal("maris-desktop-sidecar@1"),
  instance_id: z.string().uuid(),
  host: z.literal("127.0.0.1"),
  port: z.number().int().min(1).max(65535),
  nonce_digest: z.string().regex(/^[0-9a-f]{64}$/),
});

export type ManagedHostConfiguration = Readonly<{
  pythonExecutable: string;
  projectRoot: string;
  databaseUrl: string;
  secrets: Readonly<{
    bootstrapToken: string;
    bindingHmacKey: string;
    adapterToken: string;
    hostStateKey: string;
    cursorKey: string;
    agentDigestKey: string;
    financeReceiptKey: string;
  }>;
  externalUrl?: URL;
}>;

class ManagedChild implements OwnedChild {
  readonly handle: object;
  #exited: Promise<void>;

  constructor(
    readonly instanceId: string,
    readonly nonceDigest: string,
    readonly port: number,
    private readonly process: ChildProcessWithoutNullStreams
  ) {
    this.handle = process;
    this.#exited = new Promise((resolve) => process.once("exit", () => resolve()));
  }

  async stop(): Promise<void> {
    if (this.process.exitCode !== null || this.process.killed) return;
    this.process.stdin.write("shutdown\n");
    await this.#exited;
  }

  async forceStopTree(): Promise<void> {
    if (this.process.exitCode === null && !this.process.killed) this.process.kill();
    await this.#exited;
  }

  onExit(listener: () => void): () => void {
    this.process.on("exit", listener);
    return () => this.process.off("exit", listener);
  }
}

export class ManagedHostPort implements SupervisorPort {
  readonly #owned = new WeakSet<object>();

  constructor(private readonly config: ManagedHostConfiguration) {
    if (config.externalUrl && (config.externalUrl.protocol !== "http:" || config.externalUrl.hostname !== "127.0.0.1")) {
      throw new Error("invalid_external_host_url");
    }
  }

  async start(input: { instanceId: string; nonce: string }): Promise<OwnedChild> {
    const child = spawn(this.config.pythonExecutable, ["-m", "wife_system.api.desktop_sidecar"], {
      cwd: this.config.projectRoot,
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: `${this.config.projectRoot}\\src`,
        MARIS_HOST_PROJECT_ROOT: this.config.projectRoot,
        MARIS_DESKTOP_INSTANCE_ID: input.instanceId,
        WIFE_DESKTOP_PROFILE: "managed",
        WIFE_DESKTOP_STARTUP_NONCE: input.nonce,
        WIFE_DATABASE_URL: this.config.databaseUrl,
        FINANCE_DATABASE_URL: this.config.databaseUrl,
        WIFE_BOOTSTRAP_TOKEN: this.config.secrets.bootstrapToken,
        WIFE_BINDING_HMAC_KEY: this.config.secrets.bindingHmacKey,
        WIFE_ADAPTER_TOKEN: this.config.secrets.adapterToken,
        WIFE_HOST_STATE_KEY: this.config.secrets.hostStateKey,
        WIFE_CURSOR_KEY: this.config.secrets.cursorKey,
        WIFE_AGENT_DIGEST_KEY: this.config.secrets.agentDigestKey,
        WIFE_FINANCE_RECEIPT_KEY: this.config.secrets.financeReceiptKey,
      },
    });
    try {
      const handshake = await readHandshake(child, 30_000);
      const owned = new ManagedChild(
        handshake.instance_id,
        handshake.nonce_digest,
        handshake.port,
        child
      );
      this.#owned.add(owned.handle);
      return owned;
    } catch (error) {
      if (child.exitCode === null) child.kill();
      throw error;
    }
  }

  async ready(child: OwnedChild, nonce: string, timeoutMs: number): Promise<boolean> {
    if (!this.#owned.has(child.handle)) return false;
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const health = await requestStatus(this.baseUrl(child), "/healthz");
      const ready = health && await requestStatus(
        this.baseUrl(child),
        "/api/v1/desktop/readyz",
        { "X-Maris-Startup-Nonce": nonce }
      );
      if (ready) return true;
      await this.delay(100);
    }
    return false;
  }

  health(child: OwnedChild): Promise<boolean> {
    if (!this.#owned.has(child.handle)) return Promise.resolve(false);
    return requestStatus(this.baseUrl(child), "/healthz");
  }

  baseUrl(child: OwnedChild): URL {
    if (!this.#owned.has(child.handle)) throw new Error("backend_identity_rejected");
    return new URL(`http://127.0.0.1:${child.port}`);
  }

  delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async observeExternal(nonce: string, timeoutMs: number): Promise<OwnedChild> {
    if (!this.config.externalUrl || nonce.length < 32) throw new Error("external_host_unavailable");
    const observed: OwnedChild = {
      instanceId: "00000000-0000-4000-8000-000000000000",
      nonceDigest: "0".repeat(64),
      port: Number(this.config.externalUrl.port),
      handle: {},
      stop: async () => undefined,
      forceStopTree: async () => undefined,
    };
    this.#owned.add(observed.handle);
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (
        await requestStatus(this.config.externalUrl, "/healthz") &&
        await requestStatus(this.config.externalUrl, "/api/v1/desktop/readyz", { "X-Maris-Startup-Nonce": nonce })
      ) return observed;
      await this.delay(100);
    }
    throw new Error("external_host_not_ready");
  }
}

async function readHandshake(child: ChildProcessWithoutNullStreams, timeoutMs: number) {
  return new Promise<z.infer<typeof handshakeSchema>>((resolve, reject) => {
    let buffer = "";
    const cleanup = () => {
      clearTimeout(timer);
      child.stdout.off("data", onData);
      child.off("exit", onExit);
    };
    const fail = (error: Error) => { cleanup(); reject(error); };
    const onExit = () => fail(new Error("sidecar_exited_before_handshake"));
    const onData = (chunk: Buffer) => {
      buffer += chunk.toString("utf8");
      if (buffer.length > 4096) return fail(new Error("sidecar_handshake_too_large"));
      const newline = buffer.indexOf("\n");
      if (newline < 0) return;
      try {
        const parsed = handshakeSchema.parse(JSON.parse(buffer.slice(0, newline)));
        cleanup();
        resolve(parsed);
      } catch {
        fail(new Error("sidecar_handshake_invalid"));
      }
    };
    const timer = setTimeout(() => fail(new Error("sidecar_handshake_timeout")), timeoutMs);
    child.stdout.on("data", onData);
    child.once("exit", onExit);
  });
}

async function requestStatus(baseUrl: URL, path: string, headers: HeadersInit = {}): Promise<boolean> {
  try {
    const response = await fetch(new URL(path, baseUrl), {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(2_000),
    });
    if (!response.ok) return false;
    const value = await response.json() as { status?: unknown };
    return value.status === "ok" || value.status === "ready";
  } catch {
    return false;
  }
}
