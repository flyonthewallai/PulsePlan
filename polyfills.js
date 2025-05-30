// React Native polyfills for Node.js modules
import "react-native-get-random-values";
import "react-native-url-polyfill/auto";

// Buffer polyfill
if (typeof global.Buffer === "undefined") {
  global.Buffer = require("buffer").Buffer;
}

// Process polyfill
if (typeof global.process === "undefined") {
  global.process = require("process");
}

// Events polyfill
if (typeof global.EventEmitter === "undefined") {
  global.EventEmitter = require("events").EventEmitter;
}

console.log("✅ Polyfills loaded for React Native compatibility");
