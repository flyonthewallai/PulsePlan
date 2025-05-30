# 📆 PulsePlan – AI-Powered Academic Scheduler

PulsePlan is a mobile-first, AI-powered academic planning assistant that syncs with Canvas, Google Calendar, Apple Calendar (EventKit), and Outlook to generate personalized, adaptive schedules for students. Powered by GPT-4o and real-time data from your academic sources, PulsePlan takes the stress out of time management so you can focus on what matters most.

> 📱 Let your schedule find its rhythm.

---

## ✨ Features

- 📚 **Canvas Sync** – Automatically imports assignments via a browser extension
- 🧠 **AI-Powered Scheduling** – Uses GPT-4o to intelligently plan your week
- ↻ **Real-Time Adjustments** – Reschedules based on missed or completed tasks
- 🗓️ **Calendar Integration** – Syncs with Google, Outlook, and Apple Calendars
- ✅ **Task Management** – Mark complete, skip, or reschedule in a single tap
- 🔒 **Auth Support** – Google Sign-In, Supabase Auth, and session-based security
- 💸 **Freemium Model** – Free weekly planning; premium unlocks long-term control

---

## 🧱 Architecture

```
/PulsePlan
🖇️ extension/          # Chrome extension to scrape Canvas assignments
🖇️ web/                # React Native frontend (Expo)
🖇️ backend/            # API layer (FastAPI / Supabase functions)
🖇️ supabase/           # SQL schema, auth policies, and seed data
🖇️ public/             # Landing page assets
🖇️ docs/               # Diagrams, architecture, flowcharts
```

---

## 💠 Tech Stack

| Layer         | Technology                                                   |
| ------------- | ------------------------------------------------------------ |
| Frontend      | React Native (Expo)                                          |
| Backend       | FastAPI / Node.js (via API routes or standalone)             |
| AI Assistant  | OpenAI GPT-4o API                                            |
| Auth          | Supabase Auth (OAuth with Google)                            |
| Database      | Supabase (PostgreSQL)                                        |
| Payments      | Stripe                                                       |
| Browser Sync  | Chrome Extension (Canvas integration)                        |
| Calendar APIs | Google Calendar, Outlook (Microsoft Graph), EventKit (Apple) |

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/flyonthewall-dev/pulseplan.git
cd PulsePlan
```

### 2. Set up environment variables

Create a `.env` file in `/backend/` and `/web/` with:

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
STRIPE_SECRET_KEY=
```

> For mobile development, also set Expo config with your bundle ID.

---

### 3. Supabase Setup

1. Install Supabase CLI:

```bash
npm install -g supabase
```

2. Start Supabase locally:

```bash
supabase start
```

3. Push the schema:

```bash
supabase db push
```

4. Seed the database (optional):

```bash
psql -h localhost -U postgres -d pulseplan < supabase/seed.sql
```

---

### 4. Run the Frontend

```bash
cd web
npm install
npx expo start
```

---

### 5. Run the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### 6. Run the Chrome Extension (Canvas Sync)

```bash
cd extension
```

1. Visit `chrome://extensions`
2. Enable Developer Mode
3. Click "Load Unpacked"
4. Select the `/extension/` folder

---

## 🔐 Authentication

- Sign in with Google (via Supabase OAuth)
- JWTs are stored and sent with API requests
- Stripe handles plan-level access via webhooks and user metadata

---

## 💬 AI Assistant (GPT-4o)

The scheduling logic leverages OpenAI's GPT-4o:

- Input: task list, time availability, past behavior
- Output: structured plan with reasoning
- Auto-adjusts based on completion history

Backend route: `POST /generate_schedule`

---

## 💳 Payments (Stripe)

### Setting up Stripe Subscriptions

1. Create a Stripe account at [stripe.com](https://stripe.com)
2. Create a subscription product and pricing plan in your Stripe dashboard
3. Set up your Stripe API keys in the necessary environment files:

#### For the Server

Add the following to your server `.env` file:

```
STRIPE_SECRET_KEY=sk_test_yourStripeSecretKey
STRIPE_WEBHOOK_SECRET=whsec_yourStripeWebhookSecret
STRIPE_PREMIUM_PRICE_ID=price_yourStripePremiumPriceId
```

#### For the Client

Update the `app.json` file with your Stripe publishable key:

```json
"extra": {
  "apiUrl": "http://localhost:3000",
  "stripePublishableKey": "pk_test_yourStripePublishableKey"
}
```

4. Set up a webhook endpoint in your Stripe dashboard:

   - URL: `https://your-api-domain.com/stripe/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.deleted`

5. Test the integration with Stripe test mode before going live
   - Use test card numbers from the [Stripe documentation](https://stripe.com/docs/testing)

---

## 🌐 Calendar APIs

- Google: `googleapis` with full OAuth 2.0 flow
- Outlook: Microsoft Graph API with `msal`
- Apple Calendar: Local iOS EventKit access via React Native

---

## 🧩️ Browser Extension (Canvas Sync)

- Chrome extension scrapes assignments from Canvas dashboard
- Sends structured JSON to `POST /upload_canvas_data`
- CU Boulder and other Canvas domains supported via `host_permissions`

---

## 🚀 Current Status

✅ **Successfully migrated from React Navigation to Expo Router**  
✅ **Integrated Supabase v2 authentication**  
✅ **Fixed React Native compatibility issues**  
✅ **Added comprehensive polyfills for Node.js modules**

## 🔧 Recent Fixes Applied

### 1. Expo Router Migration

- ✅ Updated from React Navigation to Expo Router
- ✅ Restructured app with proper file-based routing
- ✅ Removed unnecessary `src/pages/` and `src/navigation/` directories
- ✅ Updated all navigation to use Expo Router conventions

### 2. Supabase Authentication Integration

- ✅ Updated to Supabase v2 (latest version)
- ✅ Created comprehensive auth context with error handling
- ✅ Implemented sign in, sign up, magic link, and password reset
- ✅ Added proper session management and auth state persistence

### 3. React Native Compatibility

- ✅ Added Node.js polyfills for React Native environment
- ✅ Configured Metro bundler to resolve Node.js modules
- ✅ Installed all required polyfill packages (`events`, `stream`, `buffer`, etc.)
- ✅ Created polyfills setup to handle Supabase dependencies

### 4. Enhanced Error Detection

- ✅ Added JWT token validation to detect wrong Supabase key types
- ✅ Clear console warnings when using service_role instead of anon key
- ✅ Comprehensive logging throughout authentication flow

## ⚠️ CRITICAL: Action Required

**You are currently using a `service_role` key instead of an `anon` key!**

### To Fix:

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Navigate to your project: `jwvohxsgokfcysfqhtzo`
3. Go to **Settings** → **API**
4. Copy the **anon/public** key (NOT the service_role key)
5. Update your `.env` file:

```env
EXPO_PUBLIC_SUPABASE_URL=https://jwvohxsgokfcysfqhtzo.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

The anon key should have `"role":"anon"` when decoded at https://jwt.io

## 🛠 Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI
- iOS Simulator or physical device
- Supabase account

### Installation

1. **Install dependencies:**

```bash
npm install
```

2. **Update environment variables:**

```bash
# Copy and update with your anon key
cp .env.example .env
```

3. **Start the development server:**

```bash
npm start
# or clear cache if needed
npx expo start --clear
```

## 📱 App Structure

```
src/
├── app/                    # Expo Router pages
│   ├── _layout.tsx        # Root layout with auth provider
│   ├── index.tsx          # Entry point with auth check
│   ├── auth.tsx           # Authentication page
│   ├── onboarding.tsx     # User onboarding
│   └── (tabs)/            # Tab navigation
│       ├── _layout.tsx    # Tab layout
│       ├── home.tsx       # Today view
│       ├── week.tsx       # Week view
│       ├── progress.tsx   # Progress tracking
│       └── settings.tsx   # Settings & profile
├── components/            # Reusable UI components
├── contexts/             # React contexts (auth, etc.)
├── lib/                  # Utilities and configurations
│   └── supabase.ts       # Supabase client & auth functions
└── constants/            # App constants and theme
```

## 🔐 Authentication Features

- ✅ Email/password authentication
- ✅ Magic link sign in
- ✅ Password reset functionality
- ✅ Persistent sessions with AsyncStorage
- ✅ Auto token refresh
- ✅ Proper error handling and loading states

## 🎨 UI Components

- Modern, clean design with React Native
- Ionicons for consistent iconography
- Custom theme with dark mode support
- Responsive layouts for different screen sizes

## 📋 Next Steps

1. **CRITICAL**: Update `.env` with correct anon key
2. Test authentication flow
3. Complete onboarding screens
4. Implement task management features
5. Add data persistence with Supabase

## 🐛 Troubleshooting

### "supabase.auth.getSession is not a function"

- You're using the wrong key type. Update to anon key.

### Node.js module errors

- Already fixed with polyfills. Clear cache: `npx expo start --clear`

### Authentication not working

- Verify your Supabase key is the anon key, not service_role

## 📚 Documentation

- [Expo Router Docs](https://docs.expo.dev/router/introduction/)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [React Native Docs](https://reactnative.dev/docs/getting-started)

---

**Need help?** Check `SUPABASE_SETUP.md` for detailed Supabase configuration instructions.
