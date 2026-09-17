export const FINANCE_PROBE_ERROR_CODES = [
  "invalid_request",
  "duplicate_request_conflict",
  "invalid_backend_response",
  "backend_timeout",
  "backend_unavailable",
] as const;

export type FinanceProbeErrorCode = (typeof FINANCE_PROBE_ERROR_CODES)[number];

const SAFE_MESSAGES: Readonly<Record<FinanceProbeErrorCode, string>> = {
  invalid_request: "The probe request is invalid.",
  duplicate_request_conflict: "The invocation key was already used for different input.",
  invalid_backend_response: "The probe service returned an invalid response.",
  backend_timeout: "The probe service timed out.",
  backend_unavailable: "The probe service is unavailable.",
};

const RETRYABLE: Readonly<Record<FinanceProbeErrorCode, boolean>> = {
  invalid_request: false,
  duplicate_request_conflict: false,
  invalid_backend_response: false,
  backend_timeout: true,
  backend_unavailable: true,
};

export class FinanceProbeError extends Error {
  readonly code: FinanceProbeErrorCode;
  readonly retryable: boolean;
  readonly requestId: string | undefined;

  constructor(code: FinanceProbeErrorCode, requestId?: string) {
    super(SAFE_MESSAGES[code]);
    this.name = "FinanceProbeError";
    this.code = code;
    this.retryable = RETRYABLE[code];
    this.requestId = requestId;
  }
}

export function asFinanceProbeError(error: unknown): FinanceProbeError {
  return error instanceof FinanceProbeError
    ? error
    : new FinanceProbeError("backend_unavailable");
}

export function formatSafeError(error: FinanceProbeError): string {
  return `${error.code}: ${error.message}`;
}

export type FinanceProbeErrorDetails = {
  error: {
    code: FinanceProbeErrorCode;
    message: string;
    retryable: boolean;
  };
};

export function toErrorDetails(error: FinanceProbeError): FinanceProbeErrorDetails {
  return {
    error: {
      code: error.code,
      message: error.message,
      retryable: error.retryable,
    },
  };
}
