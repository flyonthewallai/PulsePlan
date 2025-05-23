// This script creates a mock module for @stripe/stripe-react-native in node_modules
// to prevent web build errors

const fs = require('fs');
const path = require('path');

console.log('Creating mock module for @stripe/stripe-react-native for web...');

// Create directory for mock
const dir = path.resolve(__dirname, '../node_modules/@stripe/stripe-react-native-web');
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

// Create package.json
const packageJson = {
  "name": "@stripe/stripe-react-native-web",
  "version": "0.1.0",
  "main": "index.js",
  "browser": "index.js",
  "react-native": "index.js"
};

fs.writeFileSync(
  path.join(dir, 'package.json'),
  JSON.stringify(packageJson, null, 2)
);

// Create index.js with mock exports
const indexContent = `// Mock exports for @stripe/stripe-react-native on web
const React = require('react');

// Mock components
exports.StripeProvider = ({ children }) => children; 
exports.CardField = () => null;
exports.ApplePayButton = () => null;
exports.GooglePayButton = () => null;

// Mock hooks
exports.useStripe = () => ({
  initPaymentSheet: async () => ({ error: null }),
  presentPaymentSheet: async () => ({ error: null }),
  createPaymentMethod: async () => ({ error: null }),
  handleURLCallback: () => {},
  confirmPayment: async () => ({ error: null }),
  retrievePaymentIntent: async () => ({ error: null }),
  createToken: async () => ({ error: null }),
});

// Default export
module.exports.default = exports;
`;

fs.writeFileSync(path.join(dir, 'index.js'), indexContent);

console.log('Mock module created successfully!');

// Create browser.js alias in the actual stripe-react-native package
const stripeDir = path.resolve(__dirname, '../node_modules/@stripe/stripe-react-native');
if (fs.existsSync(stripeDir)) {
  const browserField = {
    "./lib/module/index.js": "@stripe/stripe-react-native-web"
  };
  
  // Update package.json or create browser field
  try {
    const pkgPath = path.join(stripeDir, 'package.json');
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    pkg.browser = browserField;
    fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2));
    console.log('Updated Stripe package.json with browser field');
  } catch (err) {
    console.error('Could not update Stripe package.json:', err);
  }
}

console.log('Web compatibility fixes complete!'); 