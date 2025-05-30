const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

// Add Node.js polyfills for React Native
config.resolver.alias = {
  ...config.resolver.alias,
  crypto: "react-native-get-random-values",
  stream: "readable-stream",
  events: "events",
  util: "util",
  assert: "assert",
  buffer: "buffer",
  process: "process/browser",
  // Additional polyfills for Supabase realtime
  "stream/web": "readable-stream",
  "node:stream": "readable-stream",
  "node:events": "events",
  "node:util": "util",
  "node:assert": "assert",
  "node:buffer": "buffer",
  "node:process": "process/browser",
  // WebSocket polyfills - use our mock instead of ws
  ws: path.resolve(__dirname, "src/lib/ws-mock.js"),
  websocket: path.resolve(__dirname, "src/lib/ws-mock.js"),
};

// Configure module resolution
config.resolver.platforms = ["ios", "android", "native", "web"];

// Block Node.js-specific modules that shouldn't be bundled
config.resolver.blockList = [
  /node_modules\/ws\/lib\/.*\.js$/,
  /node_modules\/@supabase\/realtime-js\/node_modules\/ws\/.*\.js$/,
];

// Transform configuration
config.transformer = {
  ...config.transformer,
  minifierConfig: {
    mangle: {
      keep_fnames: true,
    },
  },
};

// Add support for gesture handler and reanimated
config.resolver.assetExts.push("bin");

module.exports = config;
