module.exports = function (api) {
  api.cache(true);
  
  // Check if we're running in web environment
  const isWeb = process.env.EXPO_PUBLIC_PLATFORM === 'web';
  
  return {
    presets: ["babel-preset-expo"],
    plugins: [
      "react-native-reanimated/plugin",
      "@babel/plugin-proposal-export-namespace-from",
      [
        "module:react-native-dotenv",
        {
          moduleName: "@env",
          path: ".env",
          blacklist: null,
          whitelist: null,
          safe: false,
          allowUndefined: true,
        },
      ],
      // Add a plugin to handle Stripe imports in web environment
      isWeb && [
        'module-resolver',
        {
          alias: {
            '@stripe/stripe-react-native': './src/services/stripe/empty-module.js',
          },
        },
      ],
    ].filter(Boolean), // Filter out false values for conditional plugins
  };
};
