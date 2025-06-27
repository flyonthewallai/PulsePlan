# PulsePlan Frontend - React Native App

A modern, cross-platform productivity application built with React Native and Expo, featuring intelligent task management, AI-powered scheduling, and seamless calendar integration.

## 🌟 Features

### 📱 Core Functionality

- **Smart Task Management**: Create, edit, and track tasks with AI assistance
- **Intelligent Scheduling**: AI-powered schedule optimization and planning
- **Calendar Sync**: Seamless integration with Google Calendar and Microsoft Outlook
- **Real-time Updates**: Live synchronization across devices
- **Offline Support**: Full functionality without internet connection
- **Apple Pay Integration**: Secure premium subscription management

### ✨ Advanced Features

- **AI Assistant**: Natural language task creation and scheduling queries
- **Canvas LMS Sync**: Automatic academic assignment import
- **Multi-theme Support**: Customizable app themes (free + premium)
- **Progress Analytics**: Detailed completion statistics and streak tracking
- **Smart Notifications**: Intelligent reminders and schedule updates
- **Performance Optimization**: Advanced caching and offline synchronization

### 🎨 User Experience

- **Modern UI/UX**: Clean, intuitive interface with smooth animations
- **Accessibility**: Full support for screen readers and accessibility features
- **Dark/Light Modes**: Automatic theme switching based on system preferences
- **Gesture Navigation**: Swipe actions and intuitive touch interactions
- **Loading States**: Smooth loading animations and skeleton screens

## 🛠 Technology Stack

- **Framework**: React Native 0.79.x with Expo SDK 53
- **Navigation**: Expo Router (file-based routing system)
- **State Management**: React Context API with AsyncStorage persistence
- **UI Components**: Custom components with Expo Linear Gradient and Blur
- **Authentication**: Supabase Auth with Google OAuth
- **Data Storage**: Supabase (remote) + AsyncStorage (local cache)
- **Animations**: React Native Reanimated 3
- **Icons**: Lucide React Native
- **Development**: TypeScript, Metro bundler, Hot reloading

## 📦 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- iOS Simulator (for iOS development)
- Android Studio/Emulator (for Android development)
- Expo CLI (`npm install -g @expo/cli`)

### Installation

1. **Clone and Setup**

   ```bash
   git clone <repository-url>
   cd PulsePlan
   npm install
   ```

2. **Environment Configuration**

   The app uses Expo's configuration system. Key settings are in `app.json`:

   ```json
   {
     "expo": {
       "extra": {
         "apiUrl": "http://your-api-server.com",
         "supabaseUrl": "https://your-project.supabase.co",
         "supabaseAnonKey": "your-anon-key"
       }
     }
   }
   ```

3. **Start Development Server**

   ```bash
   npm start
   # or
   expo start
   ```

4. **Run on Device/Emulator**
   ```bash
   npm run ios      # iOS Simulator
   npm run android  # Android Emulator
   npm run web      # Web browser
   ```

## 📱 App Architecture

### 🗂 Project Structure

```
src/
├── app/                    # Expo Router pages
│   ├── (tabs)/            # Main tab navigation
│   │   ├── home.tsx       # Today's schedule
│   │   ├── week.tsx       # Weekly calendar view
│   │   ├── agent.tsx      # AI assistant
│   │   └── settings.tsx   # App settings
│   ├── (settings)/        # Settings sub-pages
│   │   ├── profile.tsx
│   │   ├── integrations/
│   │   └── appearance.tsx
│   ├── auth.tsx           # Authentication screen
│   ├── onboarding.tsx     # First-time user setup
│   └── _layout.tsx        # Root layout with providers
├── components/            # Reusable UI components
│   ├── TaskCard.tsx
│   ├── AgentModal.tsx
│   ├── CalendarIntegrationModal.tsx
│   └── LoadingScreen.tsx
├── contexts/              # React Context providers
│   ├── AuthContext.tsx    # Authentication state
│   ├── TaskContext.tsx    # Task management
│   ├── ThemeContext.tsx   # UI theming
│   └── SettingsContext.tsx
├── services/              # API and business logic
│   ├── calendarService.ts
│   ├── taskService.ts
│   └── agentService.ts
├── types/                 # TypeScript definitions
├── constants/             # App constants and configuration
└── utils/                 # Utility functions
```

### 🔄 Navigation Flow

```
App Launch → Authentication Check → Onboarding (if needed) → Main App

Main App Structure:
├── (tabs)                 # Bottom tab navigation
│   ├── Home              # Today's tasks and schedule
│   ├── Week              # Weekly calendar view
│   ├── Agent             # AI assistant chat
│   └── Settings          # User preferences
└── Modals                # Overlay screens
    ├── Task Creation
    ├── Task Details
    ├── Calendar Integration
    └── Subscription
```

### 🎯 State Management

```typescript
// Context Hierarchy
AuthProvider
├── ThemeProvider
│   ├── SettingsProvider
│   │   ├── TaskProvider
│   │   │   └── App Components
```

#### Key Contexts

1. **AuthContext**: User authentication and session management
2. **TaskContext**: Task CRUD operations and synchronization
3. **ThemeContext**: UI theming and appearance settings
4. **SettingsContext**: User preferences and configuration

## 🎨 Component Library

### 📦 Core Components

#### TaskCard

```typescript
interface TaskCardProps {
  task: Task;
  onPress: () => void;
  onEdit: () => void;
  onComplete: () => void;
  showSubject?: boolean;
}
```

#### AgentModal

```typescript
interface AgentModalProps {
  visible: boolean;
  onClose: () => void;
  initialQuery?: string;
}
```

#### CalendarIntegrationModal

```typescript
interface CalendarIntegrationModalProps {
  visible: boolean;
  onClose: () => void;
  provider: "google" | "microsoft";
}
```

### 🎭 Theme System

The app supports multiple theme variants:

```typescript
const themes = {
  standard: {
    /* Default theme */
  },
  vibrant: {
    /* High contrast colors */
  },
  minimal: {
    /* Clean, minimal design */
  },
  dark: {
    /* Dark mode variant */
  },
  // Premium themes (subscription required)
  neon: {
    /* Neon/cyberpunk theme */
  },
  nature: {
    /* Green/earth tones */
  },
};
```

## 🔧 Development

### 📜 Available Scripts

```bash
# Development
npm start              # Start Expo development server
npm run dev            # Start both frontend and backend
npm run ios            # Run on iOS simulator
npm run android        # Run on Android emulator
npm run web            # Run in web browser

# Utilities
npm run install:all    # Install frontend and backend dependencies
npm run verify-supabase # Verify Supabase configuration
npm run verify-calendar # Test calendar integration
```

### 🏗 Build Process

```bash
# Development builds
expo build:ios --type simulator    # iOS simulator build
expo build:android --type apk      # Android APK

# Production builds (requires EAS)
eas build --platform ios          # iOS App Store build
eas build --platform android      # Google Play build
eas build --platform all          # Both platforms
```

### 🔍 Testing

```bash
# Component testing (if configured)
npm test

# E2E testing (if configured)
npm run test:e2e

# Type checking
npx tsc --noEmit
```

## 🎯 Key Features Deep Dive

### 🤖 AI Assistant Integration

The AI assistant provides intelligent task management:

```typescript
// Natural language processing
"Schedule my math homework for tomorrow morning"
→ Creates task with optimal time slot

// Smart suggestions
"I have a presentation next week"
→ Suggests preparation tasks and timeline
```

### 📅 Calendar Synchronization

Seamless integration with external calendars:

- **Google Calendar**: OAuth 2.0 integration
- **Microsoft Outlook**: Graph API connectivity
- **Bi-directional Sync**: Events flow both ways
- **Conflict Resolution**: Smart handling of scheduling conflicts

### 📚 Canvas LMS Integration

Automatic academic assignment import:

```typescript
// Browser extension integration
Canvas assignments → API sync → Mobile app tasks
```

### 💳 Apple Pay Subscription

Secure subscription management:

- **In-App Purchases**: Native iOS payment processing
- **Receipt Validation**: Server-side verification
- **Premium Features**: Enhanced themes and AI capabilities
- **Subscription Management**: Easy upgrade/downgrade

## 🔒 Security & Privacy

### 🛡 Data Protection

- **Local Encryption**: Sensitive data encrypted in AsyncStorage
- **Secure API Communication**: HTTPS-only API calls
- **Token Management**: Automatic JWT refresh and secure storage
- **Minimal Data Collection**: Only essential user data stored

### 🔐 Authentication

```typescript
// Supabase Auth integration
const auth = useAuth();

// Login flow
await auth.signIn(email, password);

// OAuth integration
await auth.signInWithOAuth("google");

// Session management
auth.session; // Current user session
auth.isLoading; // Loading state
```

## 📊 Performance Optimization

### ⚡ Caching Strategy

```typescript
// AsyncStorage caching
const cacheManager = {
  // Task caching
  cacheTasks: async (userId: string, tasks: Task[]) => {
    await AsyncStorage.setItem(`tasks_${userId}`, JSON.stringify(tasks));
  },

  // Offline sync
  syncWhenOnline: async () => {
    if (NetInfo.isConnected) {
      await syncCachedData();
    }
  },
};
```

### 🔄 Offline Support

- **Complete Offline Functionality**: All core features work without internet
- **Background Sync**: Automatic synchronization when connection restored
- **Conflict Resolution**: Smart merging of offline and online changes
- **Cache Management**: Intelligent cache invalidation and updates

### 📱 Platform Optimizations

#### iOS Specific

- **Native Navigation**: Smooth iOS-style transitions
- **Haptic Feedback**: Touch feedback integration
- **Safe Area Handling**: Proper notch and home indicator spacing

#### Android Specific

- **Material Design**: Android design language compliance
- **Back Button Handling**: Proper Android navigation behavior
- **Status Bar**: Dynamic status bar styling

## 🚀 Deployment

### 📱 App Store Deployment

#### iOS (App Store)

```bash
# Build for App Store
eas build --platform ios --profile production

# Submit to App Store
eas submit --platform ios
```

#### Android (Google Play)

```bash
# Build for Google Play
eas build --platform android --profile production

# Submit to Google Play
eas submit --platform android
```

### 🌐 Web Deployment

```bash
# Build for web
expo build:web

# Deploy to hosting service
# (Vercel, Netlify, etc.)
```

## 🔧 Configuration

### 📁 App Configuration (`app.json`)

```json
{
  "expo": {
    "name": "PulsePlan",
    "slug": "pulseplan",
    "version": "1.0.0",
    "scheme": "pulseplan",
    "platforms": ["ios", "android", "web"],
    "plugins": [
      [
        "expo-location",
        {
          /* location permissions */
        }
      ],
      [
        "@react-native-async-storage/async-storage",
        {
          /* Apple Pay config */
        }
      ]
    ],
    "extra": {
      "apiUrl": "https://your-api.com",
      "supabaseUrl": "https://your-project.supabase.co",
      "supabaseAnonKey": "your-anon-key"
    }
  }
}
```

### 🎨 Theme Configuration

```typescript
// Custom theme system
export const createTheme = (variant: ThemeVariant) => ({
  colors: {
    primary: variant.primary,
    secondary: variant.secondary,
    background: variant.background,
    surface: variant.surface,
    text: variant.text,
    // ... more colors
  },
  typography: {
    fontSize: {
      /* size scale */
    },
    fontWeight: {
      /* weight scale */
    },
    lineHeight: {
      /* line height scale */
    },
  },
  spacing: {
    /* spacing scale */
  },
  borderRadius: {
    /* radius scale */
  },
});
```

## 🐛 Debugging & Troubleshooting

### 🔍 Common Issues

1. **Metro Bundle Issues**

   ```bash
   npx react-native start --reset-cache
   ```

2. **iOS Simulator Issues**

   ```bash
   npx react-native run-ios --simulator="iPhone 14"
   ```

3. **Android Build Issues**
   ```bash
   cd android && ./gradlew clean && cd ..
   npx react-native run-android
   ```

### 📊 Debug Tools

- **Flipper Integration**: Network, database, and state debugging
- **React Native Debugger**: Component tree and state inspection
- **Expo Dev Tools**: Real-time device logs and debugging

## 📚 Learning Resources

### 📖 Documentation

- [React Native Docs](https://reactnative.dev/)
- [Expo Docs](https://docs.expo.dev/)
- [Supabase Docs](https://supabase.com/docs)

### 🎓 Tutorials

- Expo Router navigation patterns
- React Context state management
- AsyncStorage caching strategies
- Apple Pay integration guide

## 🤝 Contributing

### 🔄 Development Workflow

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### 📝 Code Style

- **TypeScript**: Strict type checking enabled
- **ESLint**: Code quality and consistency
- **Prettier**: Automatic code formatting
- **Component Structure**: Functional components with hooks

### 🧪 Testing Guidelines

- **Unit Tests**: Individual component testing
- **Integration Tests**: Feature flow testing
- **E2E Tests**: Complete user journey testing

## 📞 Support

### 🆘 Getting Help

- **Documentation**: Check `/docs` folder for detailed guides
- **Issues**: Create GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

### 🔧 Troubleshooting Steps

1. **Clear Cache**: `expo start -c`
2. **Reinstall Dependencies**: `rm -rf node_modules && npm install`
3. **Check Environment**: Verify `app.json` configuration
4. **Update Expo**: `expo upgrade`

---

**Built with ❤️ using React Native and Expo for the ultimate productivity experience**
