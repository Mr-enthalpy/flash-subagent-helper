"use strict";

const path = require("node:path");
const manifest = require("./plugin.json");
const CORE_PLUGIN_KEY = `${manifest.id}-core`;

module.exports = {
  setup() {
    return {
      coreGateway: {
        config: {
          plugins: [{ enabled: true, key: CORE_PLUGIN_KEY, modulePath: path.join(__dirname, "gateway-plugin.cjs") }]
        }
      }
    };
  }
};
