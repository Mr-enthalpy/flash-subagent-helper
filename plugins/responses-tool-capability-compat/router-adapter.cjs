"use strict";

const fs = require("node:fs");
const path = require("node:path");
const compat = require("./capability-compat.cjs");
const profilePath = process.env.CCR_CAPABILITY_PROFILE_PATH || path.join(__dirname, "capability-profile.json");
const profile = compat.compileProfile(JSON.parse(fs.readFileSync(profilePath, "utf8")));

// CCR-SENSITIVE:
// WHY: Some CCR builds expose CUSTOM_ROUTER_PATH instead of a transformer.
// VERIFIED AGAINST: CUSTOM_ROUTER_PATH interface, 2026-08-09.
// FAILURE SYMPTOM: router loads but does not see the final upstream body.
module.exports = async function customRouter(request) {
  compat.applyCompatibility(request?.body, request?.body?.model, profile, request?.log);
  return undefined;
};
