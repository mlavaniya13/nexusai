from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import json, uuid, asyncio, httpx, os
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="NexusAI Productivity Platform", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ─── In-Memory Store ─────────────────────────────────────────────────
tasks_db: Dict[str, dict] = {}
notes_db: Dict[str, dict] = {}
users_db: Dict[str, dict] = {}
active_connections: List[WebSocket] = []

# ─── Models ──────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    user_id: str
    name: Optional[str] = "User"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[int] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = []
    due_date: Optional[str] = None
    estimated_effort: Optional[int] = 30
    category: Optional[str] = "general"
    energy_required: Optional[str] = "medium"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[str] = None
    estimated_effort: Optional[int] = None
    category: Optional[str] = None
    energy_required: Optional[str] = None
    subtasks: Optional[List[dict]] = None

class NoteCreate(BaseModel):
    title: str
    content: Optional[str] = ""
    blocks: Optional[List[dict]] = []
    tags: Optional[List[str]] = []

class MoodUpdate(BaseModel):
    mood: str
    energy: int

class AIRequest(BaseModel):
    prompt: str
    context: Optional[dict] = {}

class VoiceTask(BaseModel):
    transcript: str
    user_id: Optional[str] = None

# ─── WebSocket ────────────────────────────────────────────────────────
async def broadcast(message: dict):
    for conn in active_connections:
        try: await conn.send_json(message)
        except: pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if json.loads(data).get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

# ─── Grok AI ─────────────────────────────────────────────────────────
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_BASE_URL = "https://api.x.ai/v1"

async def call_grok(messages: list, system: str = "", max_tokens: int = 1024) -> str:
    if not GROK_API_KEY:
        return _mock_ai(messages[-1]["content"] if messages else "")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {"model": "grok-vision-beta",
                       "messages": ([{"role":"system","content":system}] if system else []) + messages,
                       "max_tokens": max_tokens, "temperature": 0.7}
            resp = await client.post(f"{GROK_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}, json=payload)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            return _mock_ai(messages[-1]["content"] if messages else "")
    except Exception:
        return _mock_ai(messages[-1]["content"] if messages else "")

def _mock_ai(prompt: str) -> str:
    p = prompt.lower()
    if "prioritize" in p or "priority" in p:
        return "Based on your deadlines and current workload, I recommend focusing on urgent and high-priority tasks first. 📌\n\nHere's my strategy:\n• **Urgent tasks** should get your immediate attention\n• **High-priority** items come next\n• Save medium and low-priority tasks for later\n\nTry completing deadline-sensitive work before moving to less critical tasks. This way, you'll tackle the most important items when your energy is highest!"
    elif "subtask" in p or "break" in p:
        return "Great idea! Breaking down tasks makes them less overwhelming. Here's how I'd suggest structuring this:\n\n📋 **Phase 1: Research** (20 mins)\nGather requirements and understand what needs to be done.\n\n✏️ **Phase 2: Create** (45 mins)\nBuild your initial draft or prototype. This is the main work!\n\n🔍 **Phase 3: Review** (30 mins)\nCheck your work and iterate on improvements.\n\n✅ **Phase 4: Finalize** (15 mins)\nPolish and prepare for delivery.\n\nTotal time: ~2 hours. Take short breaks between phases!"
    elif "schedule" in p or "time" in p:
        return "Let me create an optimal daily schedule for you! ⏰\n\n🌅 **9:00 AM - Deep Work Block** (90 mins)\nFocus on your most important, cognitively demanding tasks. Your brain is freshest!\n\n☕ **11:00 AM - Collaborative Time** (60 mins)\nHandle meetings and teamwork. You're still energized!\n\n🎨 **2:00 PM - Creative Work** (90 mins)\nTackle creative projects and problem-solving.\n\n📋 **4:00 PM - Admin & Emails** (60 mins)\nHandle routine tasks, emails, and administrative work.\n\n💡 Pro tip: Your peak performance window is 9-11 AM. Protect it for your most important work!"
    else:
        return "Here's my advice for staying productive today! 🚀\n\n✨ Focus on high-priority tasks during your peak energy hours (usually mornings).\n\n⏱️ Use time-blocking: Dedicate focused blocks for specific work types.\n\n🔄 Take breaks every 90 minutes to recharge and maintain focus.\n\n📝 Plan tomorrow tonight: Review what you accomplished and prepare for the next day.\n\n⚡ Batch similar tasks together for better flow and efficiency.\n\nRemember, consistency beats perfection. Small progress every day leads to big wins!"

# ─── User Helpers ────────────────────────────────────────────────────
def _make_user(user_id: str, name: str) -> dict:
    name = name.strip() or "User"
    initials = "".join(w[0].upper() for w in name.split()[:2])
    return {"id": user_id, "name": name, "avatar": initials, "xp": 0, "streak": 0, "level": 1,
            "mood": "focused", "energy": 8, "created_at": datetime.now().isoformat(),
            "preferences": {"theme": "dark", "notifications": True}}

def _ensure_user(user_id: str):
    if user_id not in users_db:
        users_db[user_id] = _make_user(user_id, "User")

# ─── User Endpoints ───────────────────────────────────────────────────
@app.post("/users")
async def create_user(payload: UserCreate):
    if payload.user_id in users_db:
        return users_db[payload.user_id]          # idempotent
    user = _make_user(payload.user_id, payload.name or "User")
    users_db[payload.user_id] = user
    return user

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(404, "User not found")
    return users_db[user_id]

@app.put("/users/{user_id}")
async def update_user(user_id: str, payload: UserUpdate):
    _ensure_user(user_id)
    u = users_db[user_id]
    if payload.name is not None:
        u["name"] = payload.name.strip() or u["name"]
        u["avatar"] = "".join(w[0].upper() for w in u["name"].split()[:2])
    if payload.mood is not None: u["mood"] = payload.mood
    if payload.energy is not None: u["energy"] = payload.energy
    return u

@app.put("/users/{user_id}/mood")
async def update_mood(user_id: str, mood_update: MoodUpdate):
    _ensure_user(user_id)
    users_db[user_id]["mood"] = mood_update.mood
    users_db[user_id]["energy"] = mood_update.energy
    asyncio.create_task(_reprioritize_bg(user_id))
    return users_db[user_id]

@app.get("/users/{user_id}/stats")
async def get_user_stats(user_id: str):
    user_tasks = [t for t in tasks_db.values() if t.get("user_id") == user_id]
    completed = [t for t in user_tasks if t.get("status") == "completed"]
    u = users_db.get(user_id, {})
    return {"total_tasks": len(user_tasks), "completed_tasks": len(completed),
            "completion_rate": round(len(completed)/max(len(user_tasks),1)*100,1),
            "xp": u.get("xp",0), "level": u.get("level",1), "streak": u.get("streak",0),
            "by_priority": {p: len([t for t in user_tasks if t.get("priority")==p]) for p in ["urgent","high","medium","low"]}}

# ─── Task Endpoints ───────────────────────────────────────────────────
@app.get("/tasks")
async def get_tasks(user_id: str):
    user_tasks = [t for t in tasks_db.values() if t.get("user_id") == user_id]
    return {"tasks": sorted(user_tasks, key=lambda x: x.get("priority_score",0), reverse=True)}

@app.post("/tasks")
async def create_task(task: TaskCreate, user_id: str):
    _ensure_user(user_id)
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    pm = {"urgent":100,"high":75,"medium":50,"low":25}
    score = pm.get(task.priority, 50)
    if task.due_date:
        try:
            diff = (datetime.fromisoformat(task.due_date) - datetime.now()).days
            if diff <= 1: score += 30
            elif diff <= 3: score += 15
            elif diff <= 7: score += 5
        except: pass
    t = {"id":task_id,"user_id":user_id,"title":task.title,"description":task.description,
         "priority":task.priority,"priority_score":min(score,130),"status":"todo",
         "tags":task.tags,"due_date":task.due_date,"estimated_effort":task.estimated_effort,
         "category":task.category,"energy_required":task.energy_required,"subtasks":[],
         "created_at":now,"updated_at":now,"completed_at":None,"xp_reward":max(10,score//5)}
    tasks_db[task_id] = t
    await broadcast({"type":"task_created","task":t,"user_id":user_id})
    return t

@app.put("/tasks/{task_id}")
async def update_task(task_id: str, update: TaskUpdate, user_id: str):
    if task_id not in tasks_db: raise HTTPException(404,"Task not found")
    t = tasks_db[task_id]
    if t.get("user_id") != user_id: raise HTTPException(403,"Not your task")
    for k,v in update.dict(exclude_none=True).items(): t[k] = v
    t["updated_at"] = datetime.now().isoformat()
    if update.status == "completed" and not t.get("completed_at"):
        t["completed_at"] = datetime.now().isoformat()
        u = users_db.get(user_id)
        if u:
            u["xp"] += t.get("xp_reward",20)
            u["level"] = min(u["xp"]//500+1, 50)
        await broadcast({"type":"task_completed","task":t,"xp_earned":t.get("xp_reward",20),"user_id":user_id})
    else:
        await broadcast({"type":"task_updated","task":t,"user_id":user_id})
    return t

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str):
    if task_id not in tasks_db: raise HTTPException(404,"Task not found")
    if tasks_db[task_id].get("user_id") != user_id: raise HTTPException(403,"Not your task")
    tasks_db.pop(task_id)
    await broadcast({"type":"task_deleted","task_id":task_id,"user_id":user_id})
    return {"deleted":True}

# ─── AI Endpoints ─────────────────────────────────────────────────────
@app.post("/ai/analyze-task")
async def analyze_task(request: AIRequest):
    system = "You are NexusAI. Analyze tasks and return JSON with: subtasks (list with title/effort/priority), priority, energy_required, category, tip."
    response = await call_grok([{"role":"user","content":f"Analyze: {request.prompt}"}], system)
    try: return json.loads(response)
    except: return {"subtasks":[{"title":"Plan approach","effort":20,"priority":"high"},{"title":"Execute","effort":60,"priority":"high"},{"title":"Review","effort":20,"priority":"medium"}],"priority":"medium","energy_required":"medium","category":"work","tip":"Use Pomodoro technique."}

async def _reprioritize_bg(user_id: str):
    try:
        u = users_db.get(user_id,{})
        user_tasks = [t for t in tasks_db.values() if t.get("user_id")==user_id and t.get("status")!="completed"]
        task_summary = [{"id":t["id"],"title":t["title"],"priority":t["priority"],"due_date":t.get("due_date")} for t in user_tasks[:10]]
        prompt = f"Mood:{u.get('mood','neutral')}, Energy:{u.get('energy',5)}/10. Tasks:{json.dumps(task_summary)}. Return JSON: {{\"priorities\":[{{\"id\":\"...\",\"score\":0,\"reason\":\"...\"}}],\"tip\":\"...\"}}"
        response = await call_grok([{"role":"user","content":prompt}], "You are NexusAI optimizer.")
        parsed = json.loads(response)
        for item in parsed.get("priorities",[]):
            if item["id"] in tasks_db and tasks_db[item["id"]].get("user_id")==user_id:
                tasks_db[item["id"]]["priority_score"] = item["score"]
                tasks_db[item["id"]]["ai_reason"] = item.get("reason","")
        await broadcast({"type":"tasks_reprioritized","user_id":user_id})
    except: pass

@app.post("/ai/prioritize")
async def ai_prioritize(user_id: str):
    await _reprioritize_bg(user_id)
    return {"tip": "Tasks reprioritized! Focus on urgent items first."}

@app.post("/ai/voice-to-task")
async def voice_to_task(request: VoiceTask):
    system = "Extract task info from voice. Return JSON: title, description, priority, due_date (ISO or null), tags, category, estimated_effort (minutes)."
    response = await call_grok([{"role":"user","content":f"Extract task: '{request.transcript}'"}], system)
    try: return json.loads(response)
    except: return {"title":request.transcript[:80],"description":"","priority":"medium","due_date":None,"tags":[],"category":"general","estimated_effort":30}

@app.post("/ai/suggest-schedule")
async def suggest_schedule(user_id: str):
    u = users_db.get(user_id,{})
    user_tasks = [t for t in tasks_db.values() if t.get("user_id")==user_id and t.get("status")=="todo"]
    task_list = [{"title":t["title"],"effort":t.get("estimated_effort",30),"priority":t["priority"]} for t in user_tasks[:8]]
    prompt = f"Energy:{u.get('energy',7)}/10, Mood:{u.get('mood','focused')}. Schedule:{json.dumps(task_list)}"
    response = await call_grok([{"role":"user","content":prompt}], "You are a productivity scheduler. Return JSON with schedule array.")
    try: return json.loads(response)
    except: return {"schedule":[
        {"time":"09:00","duration":90,"task":"Deep focus work","type":"deep_work"},
        {"time":"10:30","duration":15,"task":"Break","type":"break"},
        {"time":"10:45","duration":60,"task":"Collaborative tasks","type":"collaboration"},
        {"time":"14:00","duration":90,"task":"Creative work","type":"creative"},
        {"time":"15:30","duration":60,"task":"Admin & emails","type":"admin"}],
        "tip":"Your peak performance window is 9-11 AM. Protect it for deep work!"}

@app.post("/ai/chat")
async def ai_chat(request: AIRequest):
    system = "You are NexusAI, a brilliant productivity assistant. Be concise, actionable, and motivating."
    response = await call_grok([{"role":"user","content":request.prompt}], system, max_tokens=512)
    return {"response": response}

# ─── Notes Endpoints ──────────────────────────────────────────────────
@app.get("/notes")
async def get_notes(user_id: str):
    return {"notes": [n for n in notes_db.values() if n.get("user_id")==user_id]}

@app.post("/notes")
async def create_note(note: NoteCreate, user_id: str):
    _ensure_user(user_id)
    nid = str(uuid.uuid4())
    n = {"id":nid,"user_id":user_id,"title":note.title,"content":note.content,
         "blocks":note.blocks or [{"type":"text","content":note.content}],
         "tags":note.tags,"created_at":datetime.now().isoformat(),"updated_at":datetime.now().isoformat()}
    notes_db[nid] = n
    return n

@app.put("/notes/{note_id}")
async def update_note(note_id: str, update: dict, user_id: str):
    if note_id not in notes_db: raise HTTPException(404,"Note not found")
    if notes_db[note_id].get("user_id") != user_id: raise HTTPException(403,"Not your note")
    notes_db[note_id].update(update)
    notes_db[note_id]["updated_at"] = datetime.now().isoformat()
    return notes_db[note_id]

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str, user_id: str):
    if note_id not in notes_db: raise HTTPException(404,"Note not found")
    if notes_db[note_id].get("user_id") != user_id: raise HTTPException(403,"Not your note")
    notes_db.pop(note_id)
    return {"deleted":True}

# ─── Mount Static Files (after all API routes) ──────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
