"use strict";

const path = require("node:path");
const CORE_PLUGIN_KEY = "responses-tool-capability-compat-core";

module.exports = {
  setup() {
    return {
      coreGateway: {
        config: {
          plugins: [{ enabled: true, key: CORE_PLUGIN_KEY, modulePath: path.join(__dirname, "gateway-plugin.cjs") }]
        }
      }
    };
  },
  adapters: {
    providerTransformer: { entry: path.join(__dirname, "gateway-plugin.cjs") },
    customRouter: { entry: path.join(__dirname, "router-adapter.cjs") }
  }
};
