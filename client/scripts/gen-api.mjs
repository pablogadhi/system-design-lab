// Generates TypeScript types for every contract in design/contracts/openapi/*.yaml
//   pnpm gen:api   ->  src/api/<service>.ts
// The contract is the source of truth shared with the services; regenerate after it changes.
import { execFileSync } from "node:child_process";
import { mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const contracts = join(here, "..", "..", "design", "contracts", "openapi");
const out = join(here, "..", "src", "api");
mkdirSync(out, { recursive: true });

for (const file of readdirSync(contracts).filter((f) => /\.ya?ml$/.test(f))) {
  const name = file.replace(/\.ya?ml$/, "");
  execFileSync(join(here, "..", "node_modules", ".bin", "openapi-typescript"), [join(contracts, file), "-o", join(out, `${name}.ts`)], {
    stdio: "inherit",
  });
}
