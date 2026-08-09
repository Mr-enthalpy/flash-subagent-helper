"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const compat = require("../capability-compat.cjs");
const createGatewayPlugin = require("../gateway-plugin.cjs");

const profile = {
  profile_id: "fixture-profile",
  model_selectors: ["fixture-provider/fixture-model"],
  responses_endpoint_suffix: "/responses",
  unsupported_tool_types: ["namespace"],
  namespace_tool_choice_fallback: "auto"
};
const compiled = compat.compileProfile(profile);
const namespaceTool = (name) => ({ type: "namespace", name, tools: [] });
const functionTool = (name) => ({ type: "function", name, parameters: { type: "object" } });

test("19 tools with seven namespace types become 12 tools", () => {
  const body = {
    tools: [...Array.from({ length: 12 }, (_, i) => functionTool(`f${i}`)), ...Array.from({ length: 7 }, (_, i) => namespaceTool(`n${i}`))],
    tool_choice: { type: "namespace", name: "n0" }
  };
  const result = compat.sanitizeRequestBody(body, compiled);
  assert.equal(result.toolsBefore, 19);
  assert.equal(result.removedByType.namespace, 7);
  assert.equal(result.toolsAfter, 12);
  assert.equal(body.tool_choice, "auto");
});

test("12 normal tools and custom apply_patch remain unchanged", () => {
  const applyPatch = { type: "custom", name: "apply_patch" };
  const body = { tools: [...Array.from({ length: 12 }, (_, i) => functionTool(`f${i}`)), applyPatch], tool_choice: "auto" };
  const result = compat.sanitizeRequestBody(body, compiled);
  assert.equal(result.toolsAfter, 13);
  assert.strictEqual(body.tools[12], applyPatch);
});

test("nested tool choice referencing removed namespace falls back", () => {
  const body = { tools: [namespaceTool("fixture_group"), functionTool("keep")], tool_choice: { selected: { name: "fixture_group" } } };
  compat.sanitizeRequestBody(body, compiled);
  assert.equal(body.tool_choice, "auto");
});

test("other model selector is untouched", () => {
  const tool = namespaceTool("fixture_group");
  const body = { tools: [tool] };
  assert.equal(compat.applyCompatibility(body, "other-provider/other-model", compiled), undefined);
  assert.strictEqual(body.tools[0], tool);
});

test("gateway transformer is provider-independent and filters final Responses body", async () => {
  const transform = createGatewayPlugin({ profile }).providerPlugins[0].transformRequest;
  const upstream = { url: "https://fixture.invalid/v1/responses", body: { tools: [namespaceTool("n"), functionTool("keep")] } };
  const result = await transform({ request: { body: { model: "fixture-provider/fixture-model" } }, upstreamRequest: upstream });
  assert.equal(result.ok, true);
  assert.deepEqual(result.value.body.tools.map((tool) => tool.type), ["function"]);
});

test("compatibility transform is idempotent", () => {
  const body = { tools: [namespaceTool("n"), functionTool("keep")] };
  compat.sanitizeRequestBody(body, compiled);
  const second = compat.sanitizeRequestBody(body, compiled);
  assert.equal(second.removedByType.namespace, undefined);
  assert.equal(second.toolsAfter, 1);
});
