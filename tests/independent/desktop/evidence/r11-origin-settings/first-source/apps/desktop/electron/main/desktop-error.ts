export class DesktopError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly requestId: string | null = null,
    public readonly retryable = false
  ) {
    super(message);
    this.name = "DesktopError";
  }

  toSafePayload() {
    return { code: this.code, message: this.message, requestId: this.requestId, retryable: this.retryable } as const;
  }
}
