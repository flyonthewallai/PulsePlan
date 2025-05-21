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
