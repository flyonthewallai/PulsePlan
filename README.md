<p align="center">
  <img src="https://github.com/user-attachments/assets/0833a286-ba32-42a2-a5ca-4ae8bda63168" alt="PulsePlan" width="355"/>
</p>

# PulsePlan – AI-Powered Planner

PulsePlan is a mobile-first academic planning assistant that integrates with Canvas, Google Calendar, Apple Calendar, and Outlook to create adaptive schedules using AI. Designed for students, it streamlines planning with intelligent time-blocking, real-time task updates, and personalized assistance.

> 📱 Let your schedule find its rhythm.

---

## ✨ Features

- **Canvas Sync** – Automatically sync assignments, exams, and grades
- **AI Agent Assistant** – Conversational AI powered by GPT-4o and n8n automation
- **Natural Language Scheduling** – Create and manage tasks through chat interface
- **Real-Time Adjustments** – Reacts to task status changes and calendar updates
- **Calendar Integration** – Connects with Google, Outlook, and Apple with bidirectional sync
- **Smart Task Management** – Tap to complete, skip, or reschedule with AI recommendations
- **Connected Account Automation** – Seamless integration with email, calendar, and academic platforms
- **Authentication** – Google sign-in via Supabase Auth
- **Freemium Model** – Free weekly plans; premium unlocks advanced scheduling and automation

---

## 🤖 AI Agent: Design & Strategy

### 🧠 Purpose

- Enable intelligent conversational task management and scheduling
- Process natural language queries for complex workflow automation
- Integrate with connected accounts (Google, Microsoft, Canvas) for contextual assistance
- Provide personalized AI-powered productivity insights

### 🏗️ Architecture

- **Framework**: n8n-powered agent hosted on Fly.dev (`https://pulseplan-agent.fly.dev/`)
- **Backend Integration**: Express.js server with dedicated agent service layer
- **Authentication**: JWT-based with Supabase Auth integration
- **Inputs**:

  - Natural language queries and conversational prompts
  - User context (current page, preferences, recent tasks)
  - Connected account data (calendars, emails, assignments)
  - Real-time task status and completion history

- **Outputs**:

  - Conversational responses with actionable insights
  - Automated task creation and scheduling
  - Calendar event management and conflict resolution
  - Intelligent deadline analysis and priority recommendations

### ⚙️ Integration with GPT-4o

- GPT-4o handles:

  - Natural language understanding and generation
  - Contextual conversation management
  - Complex reasoning for multi-step workflows

- n8n Agent handles:

  - Workflow automation and orchestration
  - Connected service integrations
  - Real-time data processing and sync
  - Background task scheduling and optimization

### 🌟 Capabilities

- **Conversational Interface**: Chat-based task management with context awareness
- **Smart Scheduling**: Intelligent time-blocking with calendar integration
- **Batch Processing**: Handle multiple tasks with optimized scheduling
- **Connected Services**: Direct integration with Google, Microsoft, and Canvas APIs
- **Quick Actions**: Pre-built workflows for common productivity tasks

---

## 🗺️ Project Structure

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

## 🔠 Tech Stack

| Layer         | Technology                              |
| ------------- | --------------------------------------- |
| Frontend      | React Native (Expo 53) + TypeScript     |
| Backend       | Node.js + Express.js + TypeScript       |
| Auth          | Supabase Auth                           |
| Database      | Supabase (PostgreSQL)                   |
| AI Assistant  | OpenAI GPT-4o + Google Gemini 1.5 Flash |
| AI Automation | n8n (hosted on Fly.dev)                 |
| Real-time     | Socket.IO                               |
| Payments      | Apple Pay                               |
| Calendar APIs | Google Calendar + Microsoft Graph       |
| Web Scraping  | Puppeteer + Cheerio                     |
| Development   | Concurrent dev setup + ts-node          |

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/flyonthewall-dev/pulseplan.git
cd PulsePlan
```

### 2. Configure Environment Variables

Create `.env` files in `/web/`, `/server/`, and :

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

---

## 🔐 Authentication

- Apple Sign-in via Supabase
- JWTs for session management
- Auto-refresh and secure token storage

---

## 🧠 AI + Scheduling

- **Agent-Powered Scheduling**: `POST /agent/query` and `POST /agent/chat` endpoints for natural language task management
- **Connected Account Integration**: Leverages real-time data from Google Calendar, Microsoft Outlook, and Canvas
- **Intelligent Automation**: n8n workflows handle complex scheduling logic and calendar synchronization
- **Context-Aware Responses**: Uses task metadata, calendar availability, and user behavior patterns for personalized scheduling

---

## 🗓 Calendar Integration

- Syncs with Google, Outlook, and Apple
- Handles bidirectional sync and event conflict resolution
- Background tasks manage token refresh and error handling
- Focused on user-friendly connection setup and real-time performance

---

PulsePlan is built by **Fly on the Wall** — AI-powered products with personality. Visit us at [flyonthewalldev.com](https://flyonthewalldev.com) and [pulseplan.app](https://pulseplan.app).
