export type TokenPair = Readonly<{ accessToken: string; refreshToken: string }>;
export interface OwnerAuthPort {
  bootstrapStatus(): Promise<{ needsInitialization: boolean }>;
  initialize(credentials: { handle: string; password: string }): Promise<void>;
  login(credentials: { handle: string; password: string }): Promise<TokenPair>;
  refresh(refreshToken: string): Promise<TokenPair>;
}
export interface OwnerSecretPort {
  read(): Promise<{ handle: string; password: string; refreshToken: string | null; repairRequired: boolean } | null>;
  stage(value: { handle: string; password: string }): Promise<void>;
  commit(value: { handle: string; password: string; refreshToken: string }): Promise<void>;
  markRepair(): Promise<void>;
}

export class LocalOwnerSession {
  #tokens: TokenPair | null = null;
  #state: "authenticated" | "offline" | "needs_repair" = "offline";
  #establishFlight: Promise<string> | null = null;
  #refreshFlight: Promise<string> | null = null;
  constructor(private readonly host: OwnerAuthPort, private readonly secrets: OwnerSecretPort, private readonly randomCredential: () => { handle: string; password: string }) {}

  get safeState(): "authenticated" | "offline" | "needs_repair" { return this.#state; }
  accessToken(): string {
    if (!this.#tokens) throw new Error("owner_session_needs_repair");
    return this.#tokens.accessToken;
  }
  establish(): Promise<string> {
    if (this.#establishFlight) return this.#establishFlight;
    this.#establishFlight = this.#doEstablish().finally(() => { this.#establishFlight = null; });
    return this.#establishFlight;
  }
  async #doEstablish(): Promise<string> {
    const saved = await this.secrets.read();
    if (saved?.repairRequired) { this.#state = "needs_repair"; return this.#state; }
    if (saved?.refreshToken) {
      try { const pair = await this.host.refresh(saved.refreshToken); await this.#accept(saved.handle, saved.password, pair); return "authenticated"; } catch { /* login fallback */ }
    }
    try {
      if (saved) { const pair = await this.host.login(saved); await this.#accept(saved.handle, saved.password, pair); return "authenticated"; }
      if (!(await this.host.bootstrapStatus()).needsInitialization) { await this.#repair(); return this.#state; }
      const credentials = this.randomCredential();
      await this.secrets.stage(credentials);
      await this.host.initialize(credentials);
      const pair = await this.host.login(credentials);
      await this.#accept(credentials.handle, credentials.password, pair);
      return "authenticated";
    } catch {
      await this.#repair();
      return this.#state;
    }
  }
  refresh(): Promise<string> {
    if (this.#refreshFlight) return this.#refreshFlight;
    this.#refreshFlight = this.#doRefresh().finally(() => { this.#refreshFlight = null; });
    return this.#refreshFlight;
  }
  async revoke(): Promise<void> { await this.#repair(); }
  async #doRefresh(): Promise<string> {
    const saved = await this.secrets.read();
    if (!saved?.refreshToken || saved.repairRequired) throw new Error("owner_session_needs_repair");
    const pair = await this.host.refresh(saved.refreshToken);
    await this.#accept(saved.handle, saved.password, pair);
    return pair.accessToken;
  }
  async #accept(handle: string, password: string, pair: TokenPair): Promise<void> {
    await this.secrets.commit({ handle, password, refreshToken: pair.refreshToken });
    this.#tokens = pair;
    this.#state = "authenticated";
  }
  async #repair(): Promise<void> {
    this.#tokens = null;
    this.#state = "needs_repair";
    await this.secrets.markRepair();
  }
}
