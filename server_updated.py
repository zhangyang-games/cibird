#!/usr/bin/env python3
"""
CiBird 词鸟 - 后端服务 v2.1
FastAPI + SQLite，支持多 AI 服务商
新增：国家练习模块
"""

import os, json, sqlite3, secrets, hashlib, time, random
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx

BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DB_FILE     = BASE_DIR / "cibird.db"
HTML_FILE   = BASE_DIR / "index.html"

def load_config():
    if not CONFIG_FILE.exists():
        raise RuntimeError("config.json 不存在")
    with open(CONFIG_FILE) as f:
        return json.load(f)

# ── DB ────────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL, meaning TEXT, phonetic TEXT, pos TEXT,
            examples TEXT DEFAULT '[]', note TEXT DEFAULT '',
            created INTEGER DEFAULT (strftime('%s','now')))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            created INTEGER DEFAULT (strftime('%s','now')))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS punch_cards (
            date_str TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0)""")

# ── AI ────────────────────────────────────────────────────────
CATEGORIES = {
    "基础": "Most common 100 English words for beginners.",
    "推特": "Common slang and abbreviations used on Twitter/X.",
    "游戏": "Essential vocabulary for gamers (UI, chat, mechanics).",
    "生存": "Crucial phrases for living abroad (ordering, directions).",
    "国家": "List of 195 countries in the world. Each item must follow format: {'en': 'Country Name', 'zh': '中文国名', 'note': 'Capital/Continent'}. Keep it accurate."
}

app = FastAPI()
auth_scheme = HTTPBearer()

def verify_token(cred: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = cred.credentials
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("SELECT token FROM sessions WHERE token=?", (token,)).fetchone()
        if not row: raise HTTPException(status_code=401, detail="未登录")
    return token

async def ask_ai(system: str, user: str):
    cfg = load_config()
    provider = cfg.get("provider", "gemini")
    api_key  = cfg.get("api_key", "")
    model    = cfg.get("model", "")
    timeout  = 30.0

    headers = {"Content-Type": "application/json"}
    
    if provider in ["gemini", "deepseek", "groq", "openrouter", "openai"]:
        endpoints = {
            "gemini":     f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "deepseek":   "https://api.deepseek.com/chat/completions",
            "groq":       "https://api.groq.com/openai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "openai":     "https://api.openai.com/v1/chat/completions",
        }
        url = endpoints[provider]
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {"model": model, "messages": [{"role":"system","content":system},{"role":"user","content":user}], "max_tokens": 2000}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    return "不支持的服务商"

# ── API ───────────────────────────────────────────────────────
@app.get("/")
async def read_index():
    return HTMLResponse(content=open(HTML_FILE, encoding='utf-8').read())

@app.post("/api/login")
async def login(data: dict):
    cfg = load_config()
    pw_hash = hashlib.sha256(data.get("password", "").encode()).hexdigest()
    if pw_hash != cfg.get("password_hash"):
        raise HTTPException(status_code=401, detail="密码错误")
    token = secrets.token_hex(16)
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO sessions (token) VALUES (?)", (token,))
    return {"token": token}

@app.get("/api/words")
async def list_words(q: str = "", token: str = Depends(verify_token)):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM words"
        params = []
        if q:
            sql += " WHERE word LIKE ? OR meaning LIKE ? OR note LIKE ?"
            params = [f"%{q}%", f"%{q}%", f"%{q}%"]
        sql += " ORDER BY created DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

@app.post("/api/words")
async def add_word(data: dict, token: str = Depends(verify_token)):
    word = data.get("word", "").strip()
    if not word: return {"error": "Word is empty"}
    
    system = "You are a helpful English teacher. Return ONLY JSON."
    prompt = f"""Define '{word}'. Output JSON: 
    {{'word': '{word}', 'phonetic': '...', 'pos': '...', 'meaning': '...', 'examples': ['English example 1 (context: Twitter/Game)', 'English example 2 (context: Daily/Living)']}}
    """
    try:
        res = await ask_ai(system, prompt)
        res_json = json.loads(res.strip('`').replace('json\n',''))
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO words (word, meaning, phonetic, pos, examples) VALUES (?,?,?,?,?)",
                         (res_json['word'], res_json['meaning'], res_json['phonetic'], res_json['pos'], json.dumps(res_json['examples'])))
            # 打卡
            today = datetime.now().strftime('%Y-%m-%d')
            conn.execute("INSERT INTO punch_cards(date_str, count) VALUES(?,1) ON CONFLICT(date_str) DO UPDATE SET count=count+1", (today,))
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/essentials/{cat}")
async def get_essentials(cat: str, token: str = Depends(verify_token)):
    if cat not in CATEGORIES: raise HTTPException(status_code=404)
    system = "You are a world geography and language expert. Return ONLY JSON array of objects."
    prompt = f"{CATEGORIES[cat]} Output format: {{'items': [{{'en': '...', 'zh': '...', 'note': '...'}}, ...]}}"
    try:
        res = await ask_ai(system, prompt)
        return json.loads(res.strip('`').replace('json\n',''))
    except:
        return {"items": []}

@app.get("/api/stats")
async def get_stats(token: str = Depends(verify_token)):
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT date_str, count FROM punch_cards ORDER BY date_str DESC LIMIT 100").fetchall()
        return {r[0]: r[1] for r in rows}

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8848)
