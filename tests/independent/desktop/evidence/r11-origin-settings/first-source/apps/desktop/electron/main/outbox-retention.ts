import type { MessageBoxOptions } from "electron";
import type { EncryptedOutbox } from "./outbox";

export interface RetentionWindow {
  isDestroyed(): boolean;
  once(event: "ready-to-show" | "closed", listener: () => void): unknown;
}
export interface RetentionDialog {
  showMessageBox(window: RetentionWindow, options: MessageBoxOptions): Promise<{ response: number }>;
}

/** One startup prompt, scheduled after window readiness independently of Host. */
export class OutboxRetentionController {
  #attached = false;
  #stopped = false;
  constructor(private readonly outbox: EncryptedOutbox, private readonly dialog: RetentionDialog, private readonly isQuitting: () => boolean) {}
  attach(window: RetentionWindow): void {
    if (this.#attached || this.#stopped) return;
    this.#attached = true;
    window.once("closed", () => this.stop());
    window.once("ready-to-show", () => { void this.#prompt(window); });
  }
  stop(): void { this.#stopped = true; }
  async #prompt(window: RetentionWindow): Promise<void> {
    const active = () => !this.#stopped && !this.isQuitting() && !window.isDestroyed();
    try {
      const candidates = await this.outbox.retentionCandidates();
      if (!candidates.length || !active()) return;
      const result = await this.dialog.showMessageBox(window, {
        type: "question", title: "Maris", message: `发现 ${candidates.length} 条超过 30 天的未发送草稿`,
        detail: "保留不会改变草稿。明确删除将永久删除这些尚未发送的内容；期间新增或改变的草稿会继续保留。",
        buttons: ["保留", "明确删除"], defaultId: 0, cancelId: 0, noLink: true,
      });
      if (result.response === 1 && active()) await this.outbox.deleteConfirmed(candidates, active);
    } catch {
      // Dialog/storage failures retain data. Never expose body, IDs or raw errors.
    }
  }
}
