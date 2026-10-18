// Copies Swagger UI's files into dist/swagger so the API docs page (/api/docs) works without any CDN:
// the backend's Content-Security-Policy only allows scripts and styles from this server.
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const src = dirname(require.resolve("swagger-ui-dist/package.json"));
const out = join(dirname(new URL(import.meta.url).pathname), "..", "dist", "swagger");
mkdirSync(out, { recursive: true });
for (const f of ["swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png"]) copyFileSync(join(src, f), join(out, f));
console.log("swagger-ui copied to dist/swagger");
