import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { z } from "zod";
import type { OwnerSecretPort } from "./owner-session";
import { SecureStore } from "./secure-store";

const storedSchema = z.strictObject({
  schemaVersion: z.literal(1),
  handle: z.string().max(64),
  password: z.string().max(128),
  refreshToken: z.string().max(128).nullable(),
  repairRequired: z.boolean(),
});
type StoredOwner = z.infer<typeof storedSchema>;

export class OwnerSecretStore implements OwnerSecretPort {
  constructor(private readonly file: string, private readonly secure: SecureStore) {}

  async read(): Promise<Omit<StoredOwner, "schemaVersion"> | null> {
    try {
      const value = storedSchema.parse(this.secure.open<unknown>(await readFile(this.file)));
      const { schemaVersion: _, ...safe } = value;
      return safe;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
      await this.#write({ schemaVersion: 1, handle: "", password: "", refreshToken: null, repairRequired: true });
      return { handle: "", password: "", refreshToken: null, repairRequired: true };
    }
  }

  stage(value: { handle: string; password: string }): Promise<void> {
    return this.#write({ schemaVersion: 1, ...value, refreshToken: null, repairRequired: false });
  }

  commit(value: { handle: string; password: string; refreshToken: string }): Promise<void> {
    return this.#write({ schemaVersion: 1, ...value, repairRequired: false });
  }

  async markRepair(): Promise<void> {
    const existing = await this.read();
    await this.#write({
      schemaVersion: 1,
      handle: existing?.handle ?? "",
      password: existing?.password ?? "",
      refreshToken: null,
      repairRequired: true,
    });
  }

  async #write(value: StoredOwner): Promise<void> {
    const parsed = storedSchema.parse(value);
    await mkdir(path.dirname(this.file), { recursive: true });
    const temporary = `${this.file}.tmp`;
    await writeFile(temporary, this.secure.seal(parsed), { mode: 0o600 });
    await rename(temporary, this.file);
  }
}
