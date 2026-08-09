"use strict";

// CCR-SENSITIVE:
// WHY: this validates the distributable plugin's setup() registration and its
// transformRequest behavior. It intentionally does not claim that an installed
// CCR instance loaded or enabled the plugin.
// VERIFIED AGAINST: packaged plugin contract, 2026-08-10.
// FAILURE SYMPTOM: this probe exits non-zero before files are copied.
const fs = require("node:fs");
const path = require("node:path");

async function main() {
  const [pluginDir, profilePath] = process.argv.slice(2);
  if (!pluginDir || !profilePath) throw new Error("plugin directory and profile required");
  const manifest = JSON.parse(fs.readFileSync(path.join(pluginDir, "plugin.json"), "utf8"));
  const pluginModule = require(path.join(pluginDir, manifest.module));
  const registration = pluginModule.setup();
  const gatewayRegistration = registration?.coreGateway?.config?.plugins?.[0];
  if (!gatewayRegistration?.modulePath) throw new Error("CCR native setup() coreGateway registration missing");
  const createPlugin = require(gatewayRegistration.modulePath);
  const profile = JSON.parse(fs.readFileSync(profilePath, "utf8"));
  const transform = createPlugin({ profile })?.providerPlugins?.[0]?.transformRequest;
  if (typeof transform !== "function") throw new Error("transformRequest missing");
  const upstream = { url: `https://fixture.invalid/v1${profile.responses_endpoint_suffix}`, body: { tools: [{ type: "namespace", name: "remove_me", tools: [] }, { type: "function", name: "keep_me", parameters: { type: "object" } }], tool_choice: { type: "namespace", name: "remove_me" } } };
  const result = await transform({ request: { body: { model: profile.model_selectors[0] } }, upstreamRequest: upstream });
  if (!result?.ok || result.value.body.tools.length !== 1 || result.value.body.tools[0].type !== "function" || result.value.body.tool_choice !== "auto") throw new Error("behavioral contract failed");
  process.stdout.write("CCR PLUGIN PACKAGE CONTRACT PASS\n");
}
main().catch((error) => { process.stderr.write(`${error.name}: ${error.message}\n`); process.exitCode = 1; });
