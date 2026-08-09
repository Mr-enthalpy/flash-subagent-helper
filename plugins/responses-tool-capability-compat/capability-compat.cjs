"use strict";

// COMPAT-SENSITIVE:
// WHY: Some OpenAI Responses-compatible routes reject top-level tool objects
// with type "namespace", while Codex may emit them for grouped tool surfaces.
// VERIFIED AGAINST: deepseek_responses_v4@1.0.0 and Codex CLI 0.146.0.
// FAILURE SYMPTOM: RESPONSES_FEATURE_NOT_SUPPORTED tool.namespace.

function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function nonEmpty(value) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function compileProfile(profile) {
  if (!isRecord(profile)) throw new TypeError("profile must be an object");
  const unsupported = new Set(profile.unsupported_tool_types || []);
  const selectors = new Set(profile.model_selectors || []);
  const fallback = nonEmpty(profile.namespace_tool_choice_fallback) || "auto";
  return { ...profile, unsupported, selectors, fallback };
}

function selectorMatches(compiled, selector) {
  const value = nonEmpty(selector);
  return Boolean(value && compiled.selectors.has(value));
}

function choiceReferencesRemoved(value, removedNames, unsupportedTypes, seen = new Set()) {
  if (typeof value === "string") return removedNames.has(value);
  if (!isRecord(value) || seen.has(value)) return false;
  seen.add(value);
  if (unsupportedTypes.has(nonEmpty(value.type))) return true;
  if (removedNames.has(nonEmpty(value.name))) return true;
  return Object.values(value).some((item) => choiceReferencesRemoved(item, removedNames, unsupportedTypes, seen));
}

function sanitizeRequestBody(body, compiled) {
  if (!isRecord(body) || !Array.isArray(body.tools)) {
    return { toolsBefore: 0, removedByType: {}, toolsAfter: 0, toolChoiceChanged: false };
  }
  const retained = [];
  const removedNames = new Set();
  const removedByType = {};
  for (const tool of body.tools) {
    const type = isRecord(tool) ? nonEmpty(tool.type) : undefined;
    if (type && compiled.unsupported.has(type)) {
      const name = nonEmpty(tool.name);
      if (name) removedNames.add(name);
      removedByType[type] = (removedByType[type] || 0) + 1;
    } else {
      retained.push(tool);
    }
  }
  const toolsBefore = body.tools.length;
  if (retained.length !== toolsBefore) body.tools = retained;
  const changed = choiceReferencesRemoved(body.tool_choice, removedNames, compiled.unsupported);
  if (changed) body.tool_choice = compiled.fallback;
  return { toolsBefore, removedByType, toolsAfter: retained.length, toolChoiceChanged: changed };
}

function applyCompatibility(body, selector, compiled, log) {
  if (!selectorMatches(compiled, selector)) return undefined;
  const diagnostics = sanitizeRequestBody(body, compiled);
  if (log && typeof log.info === "function") {
    log.info({
      profile_id: compiled.profile_id,
      selector,
      tools_before: diagnostics.toolsBefore,
      removed_by_type: diagnostics.removedByType,
      tools_after: diagnostics.toolsAfter,
      tool_choice_changed: diagnostics.toolChoiceChanged
    }, "Responses tool capability compatibility applied.");
  }
  return diagnostics;
}

module.exports = { applyCompatibility, compileProfile, sanitizeRequestBody, selectorMatches };
