import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createAppServer } from "../scripts/start.mjs";

async function withServer(t) {
  const temporary = await mkdtemp(path.join(os.tmpdir(), "pitwall-test-"));
  const root = path.join(temporary, "dist");
  await mkdir(root);
  await writeFile(path.join(root, "index.html"), "<title>Pitwall</title>");
  await writeFile(path.join(root, "app.js"), "export const ok=true;");
  await writeFile(path.join(temporary, "private.txt"), "must not be exposed");
  const app = createAppServer(root);
  await new Promise((resolve) => app.listen(0, "127.0.0.1", resolve));
  t.after(async () => {
    await new Promise((resolve) => app.close(resolve));
    await rm(temporary, { recursive: true, force: true });
  });
  return `http://127.0.0.1:${app.address().port}`;
}
test("local app serves built files with correct content types and HEAD support", async (t) => {
  const base = await withServer(t);
  const page = await fetch(base + "/");
  assert.equal(page.status, 200);
  assert.match(await page.text(), /Pitwall/);
  const script = await fetch(base + "/app.js");
  assert.match(script.headers.get("content-type"), /javascript/);
  const head = await fetch(base + "/app.js", { method: "HEAD" });
  assert.equal(head.status, 200);
  assert.equal(await head.text(), "");
});
test("repository files and encoded traversal stay outside the local app", async (t) => {
  const base = await withServer(t);
  assert.equal((await fetch(base + "/%2e%2e%2fprivate.txt")).status, 403);
  assert.equal((await fetch(base + "/private.txt")).status, 404);
  assert.equal((await fetch(base + "/.env")).status, 404);
});
test("local app supports navigation fallback and rejects unexpected writes", async (t) => {
  const base = await withServer(t);
  assert.equal((await fetch(base + "/session/planner")).status, 200);
  assert.equal(
    (await fetch(base + "/", { method: "POST", body: "unused" })).status,
    405,
  );
  assert.deepEqual(await (await fetch(base + "/__pitwall_health")).json(), {
    app: "pitwall",
    mode: "localhost",
  });
});
