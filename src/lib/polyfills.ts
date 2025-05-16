import 'react-native-url-polyfill/auto';
import 'react-native-stream';

// Polyfill for Node.js stream module
if (typeof global.process === 'undefined') {
  global.process = {
    env: {},
    nextTick: (fn: Function) => setTimeout(fn, 0),
    platform: 'react-native',
    version: '',
  } as any;
}

// Polyfill for Node.js Buffer
if (typeof global.Buffer === 'undefined') {
  global.Buffer = require('buffer').Buffer;
}

// Polyfill for Node.js stream
if (typeof global.stream === 'undefined') {
  const stream = require('react-native-stream');
  global.stream = stream;
  global.Stream = stream.Stream;
  global.Readable = stream.Readable;
  global.Writable = stream.Writable;
  global.Duplex = stream.Duplex;
  global.Transform = stream.Transform;
  global.PassThrough = stream.PassThrough;
  global.finished = stream.finished;
  global.pipeline = stream.pipeline;
}

export {}; 