<p align="center">
  <img src="https://github.com/user-attachments/assets/0833a286-ba32-42a2-a5ca-4ae8bda63168" alt="PulsePlan" width="355"/>
</p>

# PulsePlan – AI-Powered Academic Scheduler

PulsePlan is a mobile-first academic planning assistant that integrates with Canvas, Google Calendar, Apple Calendar, and Outlook to create adaptive schedules using AI. Designed for students, it streamlines planning with intelligent time-blocking, real-time task updates, and personalized assistance.

> 📱 Let your schedule find its rhythm.

---

## ✨ Features

* **Canvas Sync** – Browser extension imports assignments
* **AI Scheduling** – Vector model with GPT-4o insights for smart planning
* **Real-Time Adjustments** – Reacts to task status changes
* **Calendar Integration** – Google, Outlook, Apple (EventKit)
* **Task Management** – Tap to complete, skip, or reschedule
* **Authentication** – Google sign-in via Supabase Auth
* **Freemium Model** – Free weekly plans; premium unlocks advanced scheduling

---

## 🤖 Machine Learnng 

### 🧠 Purpose

* Power adaptive scheduling and prioritization logic
* Enable offline and fallback suggestions when GPT is unavailable
* Learn user behavior patterns to enhance suggestions

### 📆 Architecture

* **Framework**: Lightweight PyTorch model
* **Embedding Memory**: Vectorized task embeddings using transformer encodings or sentence embeddings
* **Inputs**:

  * Task metadata (type, due date, estimated time, course)
  * User behavior (on-time, skipped, completed, streaks)
  * Time-of-day performance trends
* **Outputs**:

  * Suggested task time blocks
  * Personalized priorities
  * Recurring task timing insights

### ⚙️ Integration with GPT-4o

* GPT-4o handles:

  * Natural language reasoning and user prompts
  * Generating user-facing plans
* Internal ML model handles:

  * Rapid, lightweight predictions
  * Cold start suggestions
  * Real-time re-ranking of schedule blocks

### 🌟 Future Enhancements

* Grade-aware prioritization using Canvas data
* Context tagging with emojis or journaling
* Reinforcement learning with user feedback
* Evaluation metrics: completion rates, consistency, satisfaction

---

## 🗘️ Project Structure

```
flyonthewalldev-pulseplan/
├── README.md
├── app.json
├── babel.config.js
├── index.ts
├── metro.config.js
├── package.json
├── polyfills.js
├── tsconfig.json
├── assets/
├── extension/
│   ├── content.js
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── upload.js
├── server/
│   ├── package.json
│   └── src/
│       ├── config/
│       ├── controllers/
│       ├── middleware/
│       ├── routes/
│       ├── services/
│       ├── types/
│       └── utils/
└── src/
    ├── app/
    ├── assets/
    ├── components/
    ├── config/
    ├── constants/
    ├── contexts/
    ├── hooks/
    ├── lib/
    ├── services/
    ├── types/
    └── utils/
```

---

## 💻 Tech Stack

| Layer         | Technology                        |
| ------------- | --------------------------------- |
| Frontend      | React Native (Expo)               |
| Backend       | FastAPI or Node.js API            |
| Auth          | Supabase Auth                     |
| Database      | Supabase (PostgreSQL)             |
| AI Assistant  | OpenAI GPT-4o                     |
| ML Model      | PyTorch vector-memory model       |
| Payments      | Apple                             |
| Browser Sync  | Chrome Extension for Canvas       |
| Calendar APIs | Google, Microsoft Graph, EventKit |

---

## 🧰 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/flyonthewall-dev/pulseplan.git
cd PulsePlan
```

### 2. Configure Environment Variables

Create `.env` files in `/web/`, `/server/`, and `/extension/`:

```
SUPABASE_URL=
SUPABASE_ANON_KEY=
OPENAI_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PREMIUM_PRICE_ID=
```

### 3. Supabase Setup

```bash
npm install -g supabase
supabase start
supabase db push
psql -h localhost -U postgres -d pulseplan < supabase/seed.sql
```

### 4. Frontend (React Native Expo)

```bash
cd src
npm install
npx expo start
```

### 5. Backend (FastAPI or Node.js)

```bash
cd server
npm install
npm run dev
```

### 6. Chrome Extension

1. Go to `chrome://extensions`
2. Enable Developer Mode
3. Load `/extension/` folder as unpacked extension

---

## 🔐 Authentication

* Apple Sign-in via Supabase
* JWTs for session management
* Auto-refresh and secure token storage

---

## 💳 Stripe Payments via Website

* Freemium model: basic free, premium unlocks long-term scheduling
* Webhook events: `checkout.session.completed`, `customer.subscription.deleted`
* `requirePremium.ts` middleware restricts premium-only routes

---

## 🧠 AI + Scheduling

* GPT-4o powered endpoint: `POST /generate_schedule`
* Uses task metadata, availability, and completion history
* Scheduling logic combined with in-house lightweight ML model

---

## 🗓 Calendar Integration

* Google: `googleapis`
* Outlook: Microsoft Graph with `msal`
* Apple: Local EventKit via React Native

---

PulsePlan is built by **Fly on the Wall** — AI-powered products with personality. Visit us at [flyonthewalldev.com](https://flyonthewalldev.com) and [pulseplan.app](https://pulseplan.app).
