# ⚡ NexusAI — GenAI-Powered Productivity Platform

A full-featured, GenAI-powered productivity platform combining Notion's functionality with Mission Control's motion design, powered by Grok AI.

## 🚀 Quick Start

### 1. Start the Backend (Python/FastAPI)

```bash
cd backend
pip install -r requirements.txt
# Optional: Set your Grok API key
export GROK_API_KEY="your_grok_api_key_here"
python main.py
```

Backend runs at: **http://localhost:8000**
API Docs at: **http://localhost:8000/docs**

### 2. Open the Frontend

Simply open `frontend/index.html` in your browser — or serve it:

```bash
cd frontend
python3 -m http.server 3000
# Open http://localhost:3000
```

> **Note:** The app works in full demo mode even without the backend running. All AI features fall back to intelligent mock responses.

---

## ✨ Features

### 🧠 AI-Powered (Grok API)
- **Task Analysis** — Break any task into structured subtasks with effort estimates
- **Dynamic Prioritization** — AI re-ranks tasks based on mood, energy, and deadlines
- **AI Schedule Generator** — Optimal time-blocking based on your energy levels
- **AI Chat Assistant** — Full conversational productivity assistant
- **Voice-to-Task** — Speak tasks and AI extracts structured data

### 📋 Task Management
- Create, edit, delete tasks with priorities (Urgent/High/Medium/Low)
- Subtasks, tags, categories, due dates, effort estimates
- Drag-and-drop task ordering
- Priority scoring (0-100) with visual indicators
- Smart deadline detection (overdue, due soon)
- Completion celebrations with confetti! 🎉

### 📅 Calendar & Scheduling
- Interactive mini-calendar with task dots
- Full calendar view with task visualization
- Click any date to schedule a task
- AI-generated daily schedule with time blocks

### 📝 Notes (Notion-like)
- Create rich notes with tags
- Block-based content structure
- Note grid view with preview

### 🎮 Gamification
- XP points earned on task completion
- Level progression (Level 1-50)
- Day streak tracking (🔥)
- Progress ring with completion percentage
- Confetti celebrations on task completion

### 😊 Mood & Energy Tracking
- Set mood: Focused, Creative, Tired, Energized
- Energy slider (1-10)
- AI adapts task priorities based on mood/energy

### 📊 Analytics
- Completion rate tracking
- Priority breakdown visualization
- XP and streak statistics
- Task category analysis

---

## 🏗️ Architecture

```
nexusai/
├── backend/
│   ├── main.py          # FastAPI app (all endpoints)
│   ├── requirements.txt # Python deps
│   └── start.sh         # Startup script
└── frontend/
    └── index.html       # Complete single-file React-style app
```

### Backend (Python/FastAPI)
- **FastAPI** — High-performance async REST API
- **WebSocket** — Real-time updates across tabs
- **In-memory store** — No database setup required (swap for PostgreSQL easily)
- **Grok API** — AI analysis, prioritization, scheduling
- **Fallback system** — Works offline with intelligent mock AI

### Frontend (Vanilla JS + CSS)
- Single-file HTML/CSS/JS app (no build step)
- Custom CSS animations matching Mission Control aesthetic
- WebSocket client for real-time updates
- Web Speech API for voice-to-task
- Drag-and-drop task management
- Responsive design (mobile + desktop)

---

## 🔑 Grok API Setup

1. Get your API key from [x.ai](https://x.ai)
2. Set environment variable: `export GROK_API_KEY="xai-..."`
3. Restart backend

Without the key, the app uses intelligent mock responses for all AI features.

---

## 🎨 Design System

Inspired by Mission Control (missioncontrol.co):
- **Dark theme** with deep navy blues (#080c14)
- **Typography**: Syne (headers) + DM Sans (body) + JetBrains Mono (code)
- **Micro-animations**: Task slide-in, hover effects, confetti, XP popups
- **Glassmorphism** panels with backdrop blur
- **Ambient glow** effects
- **Noise texture** overlay
- Priority color system (🔴 🟠 🔵 🟢)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tasks | Get all user tasks |
| POST | /tasks | Create a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |
| POST | /ai/analyze-task | AI task breakdown |
| POST | /ai/prioritize | AI reprioritization |
| POST | /ai/voice-to-task | Voice transcript → task |
| POST | /ai/suggest-schedule | AI daily schedule |
| POST | /ai/chat | AI assistant chat |
| GET | /notes | Get all notes |
| POST | /notes | Create note |
| GET | /users/{id} | Get user profile |
| PUT | /users/{id}/mood | Update mood/energy |
| GET | /users/{id}/stats | Get user statistics |
| WS | /ws | WebSocket connection |

---

## 🔮 Extending the App

### Add PostgreSQL
Replace in-memory dicts in `main.py` with SQLAlchemy models and PostgreSQL connection.

### Add Redis
Add Redis for session management and caching with `redis-py`.

### Add Authentication
Integrate with FastAPI-Users or implement JWT auth.

### Add Calendar Sync
Use Google Calendar API or CalDAV for external calendar integration.

---

Built with ❤️ using Python FastAPI + Grok AI
