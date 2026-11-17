// Production smoke test for the publicly deployed Audio Studio Worker.
// Uses only standard Node 22 APIs; it does not log in, upload audio or mutate data.
import assert from "node:assert/strict";
import { lookup } from "node:dns/promises";

const base = (process.env.AUDIO_STUDIO_URL || "https://audiostudio.vsbalaajee.workers.dev").replace(/\/+$/, "");
const origin = new URL(base);
let failures = 0;
const log = async (name, fn) => {
  try {
    const details = await fn();
    console.log("PASS", name, details ? "- " + details : "");
  } catch (error) {
    failures++;
    console.error("FAIL", name, "-", error?.stack || String(error));
  }
};
async function call(path, options = {}) {
  const url = base + path;
  const response = await fetch(url, { signal: AbortSignal.timeout(15000), redirect: "follow", ...options });
  const body = await response.text();
  return { response, body };
}
async function mcp(method, id, params = {}) {
  const { response, body } = await call("/mcp", {
    method: "POST",
    headers: {
      "Accept": "application/json, text/event-stream",
      "Content-Type": "application/json",
      "MCP-Protocol-Version": "2025-06-18"
    },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params })
  });
  assert.equal(response.status, 200, "MCP " + method + " HTTP " + response.status + ": " + body.slice(0, 1500));
  let payload;
  if ((response.headers.get("content-type") || "").includes("text/event-stream")) {
    const messages = body.split(/\r?\n/).filter(x => x.startsWith("data:")).map(x => x.slice(5).trim());
    assert.ok(messages.length, "MCP SSE response has no data event: " + body.slice(0, 500));
    payload = JSON.parse(messages.at(-1));
  } else payload = JSON.parse(body);
  assert.ok(payload.jsonrpc === "2.0", "Expected JSON-RPC 2.0: " + body.slice(0, 1000));
  assert.ok(!payload.error, "MCP error " + JSON.stringify(payload.error));
  return payload;
}
console.log("Audio Studio production verification");
console.log("Target URL:", base);
console.log("Started:", new Date().toISOString());
await log("DNS resolution", async () => {
  const value = await lookup(origin.hostname);
  return value.address;
});
await log("GET / health JSON", async () => {
  const { response, body } = await call("/health");
  assert.equal(response.status, 200, body.slice(0, 1500));
  const json = JSON.parse(body);
  assert.equal(json.status, "ok");
  assert.equal(json.mcp, "/mcp");
  return JSON.stringify(json);
});
await log("GET / branded browser interface", async () => {
  const { response, body } = await call("/");
  assert.equal(response.status, 200, body.slice(0, 1500));
  assert.match(response.headers.get("content-type") || "", /text\/html/);
  for (const token of ["Audio Studio", 'id="voices"', 'id="music"', 'id="timeline"', "Preview timeline", "Download settings"]) {
    assert.ok(body.includes(token), "Browser form missing: " + token);
  }
  assert.match(body, /Generate MP3 · Coming next/, "Browser MP3 rendering must remain accurately marked unavailable");
  return "HTML and key form controls found";
});
await log("MCP initialize", async () => {
  const result = await mcp("initialize", 101, {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "audio-studio-smoke-test", version: "1.0.0" }
  });
  assert.ok(result.result?.serverInfo?.name, "Missing serverInfo.name");
  return "server=" + result.result.serverInfo.name + " protocol=" + result.result.protocolVersion;
});
await log("MCP tools/list", async () => {
  const response = await mcp("tools/list", 102, {});
  const names = (response.result?.tools || []).map(t => t.name);
  for (const tool of ["start_audio_studio", "get_audio_studio_defaults", "preview_audio_timeline"]) {
    assert.ok(names.includes(tool), "Missing tool " + tool + "; got " + names);
  }
  return names.join(", ");
});
await log("MCP start_audio_studio", async () => {
  const response = await mcp("tools/call", 103, { name: "start_audio_studio", arguments: { project_name: "QA Smoke Test" } });
  assert.ok(!response.result?.isError, "Tool returned isError");
  const body = JSON.parse(response.result.content.find(x => x.type === "text").text);
  const url = new URL(body.app_url);
  assert.equal(url.origin, origin.origin);
  assert.equal(url.searchParams.get("project"), "QA Smoke Test");
  assert.equal(body.status, "browser_form_ready");
  return body.app_url;
});
await log("MCP preview_audio_timeline", async () => {
  const response = await mcp("tools/call", 104, { name: "preview_audio_timeline", arguments: {
    clips: [{ name: "intro.mp3", duration_seconds: 10 }, { name: "body.mp3", duration_seconds: 20 }],
    gap_seconds: 3,
    outro_seconds: 5
  } });
  assert.ok(!response.result?.isError, "Tool returned isError");
  const body = JSON.parse(response.result.content.find(x => x.type === "text").text);
  assert.equal(body.total_seconds, 38);
  assert.equal(body.timeline[1].start_seconds, 13);
  return JSON.stringify(body.timeline);
});
console.log("Finished:", new Date().toISOString(), "failure count:", failures);
process.exitCode = failures ? 1 : 0;
