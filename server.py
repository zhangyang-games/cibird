#!/usr/bin/env python3
"""
CiBird 词鸟 - 后端服务 v2
FastAPI + SQLite，支持多 AI 服务商
新增：今日金句 / 打卡记录 / 必学模块
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
        # 打卡记录表：date_str = YYYY-MM-DD，count = 当天操作数
        conn.execute("""CREATE TABLE IF NOT EXISTS checkins (
            date_str TEXT PRIMARY KEY,
            count    INTEGER DEFAULT 0)""")
        # 今日金句缓存：date_str + word_id
        conn.execute("""CREATE TABLE IF NOT EXISTS daily_quote (
            date_str TEXT PRIMARY KEY,
            word_id  INTEGER,
            sentence_en TEXT DEFAULT '',
            sentence_zh TEXT DEFAULT '')""")
        # 必学模块内容缓存
        conn.execute("""CREATE TABLE IF NOT EXISTS essentials (
            category TEXT PRIMARY KEY,
            content  TEXT DEFAULT '[]',
            updated  INTEGER DEFAULT 0)""")
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def bump_checkin():
    """每次用户有实质操作就调用，给今天打卡+1"""
    ds = today_str()
    with get_db() as db:
        db.execute("""INSERT INTO checkins(date_str,count) VALUES(?,1)
            ON CONFLICT(date_str) DO UPDATE SET count=count+1""", (ds,))

# ── APP ───────────────────────────────────────────────────────
app = FastAPI(title="CiBird", docs_url=None, redoc_url=None)
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    tok = credentials.credentials
    with get_db() as db:
        row = db.execute("SELECT token FROM sessions WHERE token=?", (tok,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return tok

# ── Models ────────────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str; password: str

class WordReq(BaseModel):
    word: str; meaning: str=""; phonetic: str=""; pos: str=""; examples: list=[]; note: str=""

class GenerateReq(BaseModel):
    word: str

class EssentialReq(BaseModel):
    category: str

class NoteReq(BaseModel):
    note: str

class ExamplesReq(BaseModel):
    examples: list

# ── 前端 ──────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if HTML_FILE.exists():
        return HTML_FILE.read_text(encoding="utf-8")
    return HTMLResponse("<h1>index.html 未找到</h1>", status_code=404)

# ── 登录 ──────────────────────────────────────────────────────
@app.post("/api/login")
async def login(req: LoginReq):
    cfg = load_config()
    if req.username != cfg["username"]:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if hashlib.sha256(req.password.encode()).hexdigest() != cfg["password_hash"]:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    tok = secrets.token_urlsafe(32)
    with get_db() as db:
        db.execute("DELETE FROM sessions WHERE created<?", (int(time.time())-7*86400,))
        db.execute("INSERT INTO sessions(token) VALUES(?)", (tok,))
    return {"token": tok}

# ── 词库 ──────────────────────────────────────────────────────
@app.get("/api/words")
async def list_words(tok=Depends(verify_token)):
    with get_db() as db:
        rows = db.execute("SELECT id,word,meaning,phonetic,pos,examples,note,created FROM words ORDER BY created DESC").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try: d["examples"] = json.loads(d["examples"] or "[]")
        except: d["examples"] = []
        result.append(d)
    return result

@app.post("/api/words")
async def add_word(req: WordReq, tok=Depends(verify_token)):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO words(word,meaning,phonetic,pos,examples,note) VALUES(?,?,?,?,?,?)",
            (req.word.strip(), req.meaning, req.phonetic, req.pos,
             json.dumps(req.examples, ensure_ascii=False), req.note))
    bump_checkin()
    return {"id": cur.lastrowid, "word": req.word}

@app.delete("/api/words/{wid}")
async def del_word(wid: int, tok=Depends(verify_token)):
    with get_db() as db:
        db.execute("DELETE FROM words WHERE id=?", (wid,))
    return {"ok": True}

@app.patch("/api/words/{wid}/note")
async def update_note(wid: int, req: NoteReq, tok=Depends(verify_token)):
    with get_db() as db:
        db.execute("UPDATE words SET note=? WHERE id=?", (req.note, wid))
    bump_checkin()
    return {"ok": True}

@app.patch("/api/words/{wid}/examples")
async def update_examples(wid: int, req: ExamplesReq, tok=Depends(verify_token)):
    with get_db() as db:
        db.execute("UPDATE words SET examples=? WHERE id=?",
                   (json.dumps(req.examples, ensure_ascii=False), wid))
    bump_checkin()
    return {"ok": True}

# ── 打卡记录 ──────────────────────────────────────────────────
@app.get("/api/checkins")
async def get_checkins(tok=Depends(verify_token)):
    """返回最近 90 天的打卡记录"""
    with get_db() as db:
        rows = db.execute(
            "SELECT date_str, count FROM checkins ORDER BY date_str DESC LIMIT 90"
        ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    return {
        "records": [{"date": r["date_str"], "count": r["count"]} for r in rows],
        "total_words": total,
        "today": today_str()
    }

# ── 今日金句 ──────────────────────────────────────────────────
@app.get("/api/daily-quote")
async def get_daily_quote(tok=Depends(verify_token)):
    ds = today_str()
    with get_db() as db:
        # 先查缓存
        row = db.execute("SELECT * FROM daily_quote WHERE date_str=?", (ds,)).fetchone()
        if row and row["sentence_en"]:
            word_row = db.execute("SELECT word,meaning FROM words WHERE id=?", (row["word_id"],)).fetchone()
            return {
                "word": word_row["word"] if word_row else "",
                "meaning": word_row["meaning"] if word_row else "",
                "sentence_en": row["sentence_en"],
                "sentence_zh": row["sentence_zh"],
                "date": ds
            }
        # 没有缓存，随机选一个有例句的词
        words_with_ex = db.execute(
            "SELECT id,word,meaning,examples FROM words WHERE examples!='[]' AND examples!='' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if not words_with_ex:
            # 没有例句就随机选任意词
            words_with_ex = db.execute("SELECT id,word,meaning,examples FROM words ORDER BY RANDOM() LIMIT 1").fetchone()
        if not words_with_ex:
            return {"word": "", "meaning": "", "sentence_en": "Keep learning!", "sentence_zh": "坚持学习！", "date": ds}

    # 从例句里取第一条
    try:
        exs = json.loads(words_with_ex["examples"] or "[]")
        en = exs[0]["en"] if exs else ""
        zh = exs[0]["zh"] if exs else ""
    except:
        en = zh = ""

    with get_db() as db:
        db.execute("""INSERT INTO daily_quote(date_str,word_id,sentence_en,sentence_zh) VALUES(?,?,?,?)
            ON CONFLICT(date_str) DO UPDATE SET word_id=?,sentence_en=?,sentence_zh=?""",
            (ds, words_with_ex["id"], en, zh, words_with_ex["id"], en, zh))

    return {
        "word": words_with_ex["word"],
        "meaning": words_with_ex["meaning"],
        "sentence_en": en,
        "sentence_zh": zh,
        "date": ds
    }

# ── 必学模块 ──────────────────────────────────────────────────
ESSENTIAL_SYSTEM = """You are an English learning assistant for a Chinese user.
Generate a structured vocabulary list for the given category. Return ONLY raw JSON array, no markdown, no explanation.
Each item must have: {"en": "English word or phrase", "zh": "中文", "note": "optional short tip in Chinese, max 10 chars, or empty string"}
Make it practical, conversational, suitable for daily life / Twitter / gaming context.
Generate 8-12 items."""

CATEGORIES = {
    "时间": "Common time expressions in English (morning, noon, afternoon, evening, midnight, rush hour, etc.)",
    "数字": "Numbers and counting in English context (dozen, score, hundred, thousand, million, billion, etc.) with practical usage",
    "日期": "Days of the week in English with common abbreviations",
    "十二个月": "12 months of the year in English with abbreviations",
    "问候": "Common English greetings and farewells for daily life and social media",
    "情绪": "English words for emotions and feelings, including internet slang",
    "游戏": "Common English gaming terms and phrases (gg, afk, buff, nerf, etc.)",
    "推特": "Common English Twitter/social media slang and expressions (lol, smh, tbh, ngl, etc.)",
}

@app.get("/api/essentials/categories")
async def get_categories(tok=Depends(verify_token)):
    return {"categories": list(CATEGORIES.keys())}

@app.get("/api/essentials/{category}")
async def get_essential(category: str, tok=Depends(verify_token)):
    if category not in CATEGORIES:
        raise HTTPException(status_code=404, detail="分类不存在")
    # 查缓存（24小时有效）
    with get_db() as db:
        row = db.execute("SELECT content, updated FROM essentials WHERE category=?", (category,)).fetchone()
        if row and (int(time.time()) - row["updated"]) < 86400:
            try:
                return {"category": category, "items": json.loads(row["content"])}
            except: pass

    # 调 AI 生成
    cfg = load_config()
    prompt = CATEGORIES[category]
    try:
        result = await call_ai(
            cfg.get("provider",""), cfg.get("api_key",""), cfg.get("model",""),
            ESSENTIAL_SYSTEM,
            f"Generate vocabulary list for category: {prompt}"
        )
        import re
        m = re.search(r'\[[\s\S]*\]', result)
        items = json.loads(m.group()) if m else []
    except:
        items = []

    with get_db() as db:
        db.execute("""INSERT INTO essentials(category,content,updated) VALUES(?,?,?)
            ON CONFLICT(category) DO UPDATE SET content=?,updated=?""",
            (category, json.dumps(items, ensure_ascii=False), int(time.time()),
             json.dumps(items, ensure_ascii=False), int(time.time())))

    return {"category": category, "items": items}

# ── AI 核心 ───────────────────────────────────────────────────
WORD_SYSTEM = """You are an English vocabulary assistant helping a Chinese user learn English for Twitter, gaming, and daily survival abroad.

The user gives you one English word. Return ONLY a raw JSON object (no markdown, no code blocks, no explanation). Use this exact format:
{
  "meaning": "用中文通俗解释这个词，1-2句，像朋友说话，不要词典腔",
  "phonetic": "美式音标，例如 /rɪˈzɪliənt/",
  "pos": "词性缩写，例如 adj / n / v",
  "examples": [
    {"en": "MUST be in English. Natural Twitter or gaming sentence. NO Chinese.", "zh": "中文翻译"},
    {"en": "MUST be in English. Different scenario. NO Chinese.", "zh": "中文翻译"}
  ]
}
CRITICAL: "en" fields = English only. "meaning"/"zh" = Chinese only. Raw JSON only."""

@app.post("/api/generate")
async def generate(req: GenerateReq, tok=Depends(verify_token)):
    cfg = load_config()
    word = req.word.strip()
    try:
        result = await call_ai(cfg.get("provider",""), cfg.get("api_key",""), cfg.get("model",""),
                               WORD_SYSTEM, f"Generate a vocabulary card for the English word: {word}")
        try: data = json.loads(result)
        except:
            import re
            m = re.search(r'\{[\s\S]*\}', result)
            if m: data = json.loads(m.group())
            else: raise HTTPException(status_code=500, detail="AI 返回格式异常")
        bump_checkin()
        return data
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败：{str(e)}")

async def call_ai(provider: str, api_key: str, model: str, system: str, user: str) -> str:
    headers = {"Content-Type": "application/json"}
    timeout = httpx.Timeout(30.0)
    if provider in ("gemini","deepseek","groq","openrouter","openai"):
        endpoints = {
            "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "deepseek":   "https://api.deepseek.com/chat/completions",
            "groq":       "https://api.groq.com/openai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "openai":     "https://api.openai.com/v1/chat/completions",
        }
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {"model": model, "messages": [{"role":"system","content":system},{"role":"user","content":user}], "max_tokens": 800}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(endpoints[provider], headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    elif provider == "claude":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        payload = {"model": model, "max_tokens": 800, "system": system, "messages": [{"role":"user","content":user}]}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["content"][0]["text"]
    else:
        raise ValueError(f"不支持的服务商：{provider}")

if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    port = int(cfg.get("port", 8848))
    init_db()
    print(f"\n🦜 CiBird 词鸟 v2 已启动！访问 http://0.0.0.0:{port}\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="warning")
