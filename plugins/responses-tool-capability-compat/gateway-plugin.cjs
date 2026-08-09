"use strict";

const fs = require("node:fs");
const path = require("node:path");
const compat = require("./capability-compat.cjs");

// CCR-SENSITIVE:
// WHY: Verified CCR builds call providerPlugins[].transformRequest with the
// final upstream request. Hook shape is not stable across all CCR versions.
// VERIFIED AGAINST: providerPlugins.transformRequest interface, 2026-08-09.
// FAILURE SYMPTOM: unit tests pass but the live upstream request is unchanged.

function readProfile(profilePath) {
  const resolved = profilePath || process.env.CCR_CAPABILITY_PROFILE_PATH || path.join(__dirname, "capability-profile.json");
  return compat.compileProfile(JSON.parse(fs.readFileSync(resolved, "utf8")));
}

function isResponsesEndpoint(value, suffix) {
  if (typeof value !== "string" || !value.trim()) return false;
  const expected = suffix || "/responses";
  try {
    return new URL(value).pathname.replace(/\/+$/, "").endsWith(expected);
  } catch {
    return value.split("?", 1)[0].replace(/\/+$/, "").endsWith(expected);
  }
}

function createGatewayPlugin(options = {}) {
  const profile = options.profile ? compat.compileProfile(options.profile) : readProfile(options.profilePath);
  return {
    providerPlugins: [{
      key: `responses-tool-capability-compat:${profile.profile_id}`,
      // "openai" identifies the CCR protocol adapter, not an upstream vendor.
      provider: "openai",
      async transformRequest(context) {
        const upstream = context?.upstreamRequest;
        const selector = context?.request?.body?.model;
        if (!upstream || !isResponsesEndpoint(upstream.url, profile.responses_endpoint_suffix) || !compat.selectorMatches(profile, selector)) {
          return { ok: true, value: upstream };
        }
        compat.applyCompatibility(upstream.body, selector, profile, context?.request?.log);
        return { ok: true, value: upstream };
      }
    }]
  };
}

module.exports = createGatewayPlugin;
module.exports.createGatewayPlugin = createGatewayPlugin;
module.exports.isResponsesEndpoint = isResponsesEndpoint;
module.exports.readProfile = readProfile;
