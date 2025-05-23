// This is an empty module that gets used as a replacement for @stripe/stripe-react-native on web
// It exports mock objects that match the shape of the original module but do nothing
const React = require('react');

const noop = () => {};

// Mock the StripeProvider component to properly return React elements
export const StripeProvider = ({ children }) => React.createElement(React.Fragment, null, children);

// Mock various components to return null React elements
export const CardField = () => React.createElement(React.Fragment, null, null);
export const ApplePayButton = () => React.createElement(React.Fragment, null, null);
export const GooglePayButton = () => React.createElement(React.Fragment, null, null);

// Mock the useStripe hook with all necessary methods
export const useStripe = () => ({
  initPaymentSheet: async () => ({ error: null }),
  presentPaymentSheet: async () => ({ error: null }),
  createPaymentMethod: async () => ({ error: null, paymentMethod: null }),
  createToken: async () => ({ error: null, token: null }),
  handleURLCallback: noop,
  confirmPayment: async () => ({ error: null }),
  retrievePaymentIntent: async () => ({ error: null }),
  retrieveSetupIntent: async () => ({ error: null }),
  confirmSetupIntent: async () => ({ error: null }),
  createTokenForCVCUpdate: async () => ({ error: null, tokenId: null }),
});

// Default export for CommonJS require - include all exports
module.exports = {
  StripeProvider,
  CardField,
  useStripe,
  ApplePayButton,
  GooglePayButton,
}; 