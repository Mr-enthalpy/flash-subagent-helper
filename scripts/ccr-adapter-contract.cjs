"use strict";

// CCR-SENSITIVE:
// WHY: gateway_plugin_v1 promises an executable transformRequest contract.
// VERIFIED AGAINST: packaged adapter and plugins[] surface, 2026-08-09.
// FAILURE SYMPTOM: this probe exits non-zero before deployment.
const fs = require("node:fs");

async function main() {
  const [pluginPath, profilePath] = process.argv.slice(2);
  if (!pluginPath || !profilePath) throw new Error("plugin and profile required");
  const createPlugin = require(pluginPath);
  const profile = JSON.parse(fs.readFileSync(profilePath, "utf8"));
  const transform = createPlugin({ profile })?.providerPlugins?.[0]?.transformRequest;
  if (typeof transform !== "function") throw new Error("transformRequest missing");
  const upstream = { url: `https://fixture.invalid/v1${profile.responses_endpoint_suffix}`, body: { tools: [{ type: "namespace", name: "remove_me", tools: [] }, { type: "function", name: "keep_me", parameters: { type: "object" } }], tool_choice: { type: "namespace", name: "remove_me" } } };
  const result = await transform({ request: { body: { model: profile.model_selectors[0] } }, upstreamRequest: upstream });
  if (!result?.ok || result.value.body.tools.length !== 1 || result.value.body.tools[0].type !== "function" || result.value.body.tool_choice !== "auto") throw new Error("behavioral contract failed");
  process.stdout.write("CCR ADAPTER CONTRACT PASS\n");
}
main().catch((error) => { process.stderr.write(`${error.name}: ${error.message}\n`); process.exitCode = 1; });
