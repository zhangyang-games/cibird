#!/usr/bin/env python3
"""
CiBird 词鸟 - 后端服务
FastAPI + SQLite，支持多 AI 服务商
"""

import os, json, sqlite3, secrets, hashlib, time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

# ── 配置 ──────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DB_FILE     = BASE_DIR / "cibird.db"
HTML_FILE   = BASE_DIR / "index.html"

def load_config():
    if not CONFIG_FILE.exists():
        raise RuntimeError("config.json 不存在，请重新运行 install.sh")
    with open(CONFIG_FILE) as f:
        return json.load(f)

# ── 数据库 ─────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                word     TEXT NOT NULL,
                meaning  TEXT,
                phonetic TEXT,
                pos      TEXT,
                examples TEXT DEFAULT '[]',
                note     TEXT DEFAULT '',
                created  INTEGER DEFAULT (strftime('%s','now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token   TEXT PRIMARY KEY,
                created INTEGER DEFAULT (strftime('%s','now'))
            )
        """)
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

# ── APP ────────────────────────────────────────────────────────
app = FastAPI(title="CiBird", docs_url=None, redoc_url=None)
security = HTTPBearer()

# ── 认证 ───────────────────────────────────────────────────────
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    tok = credentials.credentials
    with get_db() as db:
        row = db.execute("SELECT token FROM sessions WHERE token=?", (tok,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return tok

# ── Models ─────────────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str
    password: str

class WordReq(BaseModel):
    word: str
    meaning: str = ""
    phonetic: str = ""
    pos: str = ""
    examples: list = []
    note: str = ""

class GenerateReq(BaseModel):
    word: str

class NoteReq(BaseModel):
    note: str

class ExamplesReq(BaseModel):
    examples: list

# ── 路由：前端 ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if HTML_FILE.exists():
        return HTML_FILE.read_text(encoding="utf-8")
    return HTMLResponse("<h1>index.html 未找到</h1>", status_code=404)

# ── 路由：登录 ─────────────────────────────────────────────────
@app.post("/api/login")
async def login(req: LoginReq):
    cfg = load_config()
    if req.username != cfg["username"]:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    pw_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if pw_hash != cfg["password_hash"]:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    tok = secrets.token_urlsafe(32)
    with get_db() as db:
        # 清理 7 天前的 session
        db.execute("DELETE FROM sessions WHERE created < ?", (int(time.time()) - 7*86400,))
        db.execute("INSERT INTO sessions(token) VALUES(?)", (tok,))
    return {"token": tok}

# ── 路由：词库 ─────────────────────────────────────────────────
@app.get("/api/words")
async def list_words(tok=Depends(verify_token)):
    with get_db() as db:
        rows = db.execute(
            "SELECT id,word,meaning,phonetic,pos,examples,note,created FROM words ORDER BY created DESC"
        ).fetchall()
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
             json.dumps(req.examples, ensure_ascii=False), req.note)
        )
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
    return {"ok": True}

@app.patch("/api/words/{wid}/examples")
async def update_examples(wid: int, req: ExamplesReq, tok=Depends(verify_token)):
    with get_db() as db:
        db.execute("UPDATE words SET examples=? WHERE id=?",
                   (json.dumps(req.examples, ensure_ascii=False), wid))
    return {"ok": True}

# ── AI 造句 ────────────────────────────────────────────────────
SYSTEM_PROMPT = """你是一个英语单词助手，专门帮助想看懂推特、在游戏里聊天、未来能出国生活的中国人学英语。

用户给你一个英文单词，你返回 JSON（不要 markdown 代码块，直接裸 JSON），格式：
{
  "meaning": "通俗中文释义，1-2句，不要词典味，要像朋友解释",
  "phonetic": "美式音标，例如 /rɪˈzɪliənt/",
  "pos": "词性缩写，例如 adj / n / v",
  "examples": [
    {
      "en": "推特或游戏场景的例句，自然口语，不要教科书腔",
      "zh": "对应的中文翻译"
    },
    {
      "en": "第二个例句，换一个不同的使用场景",
      "zh": "对应的中文翻译"
    }
  ]
}"""

@app.post("/api/generate")
async def generate(req: GenerateReq, tok=Depends(verify_token)):
    cfg = load_config()
    provider = cfg.get("provider", "").lower()
    api_key   = cfg.get("api_key", "")
    model     = cfg.get("model", "")

    if not api_key:
        raise HTTPException(status_code=500, detail="API Key 未配置，请检查 config.json")

    word = req.word.strip()
    user_msg = f"请为这个单词生成学习卡片：{word}"

    try:
        result = await call_ai(provider, api_key, model, SYSTEM_PROMPT, user_msg)
        # 解析 JSON
        try:
            data = json.loads(result)
        except:
            # 尝试提取 JSON 块
            import re
            m = re.search(r'\{[\s\S]*\}', result)
            if m:
                data = json.loads(m.group())
            else:
                raise HTTPException(status_code=500, detail="AI 返回格式异常，请重试")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败：{str(e)}")


async def call_ai(provider: str, api_key: str, model: str, system: str, user: str) -> str:
    """统一调用各家 AI，返回文本"""
    headers = {"Content-Type": "application/json"}
    timeout = httpx.Timeout(30.0)

    # ── OpenAI 兼容格式（Gemini/DeepSeek/Groq/OpenRouter 全部走这条）
    if provider in ("gemini", "deepseek", "groq", "openrouter", "openai"):
        endpoints = {
            "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "deepseek":   "https://api.deepseek.com/chat/completions",
            "groq":       "https://api.groq.com/openai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "openai":     "https://api.openai.com/v1/chat/completions",
        }
        url = endpoints[provider]
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ],
            "max_tokens": 600
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    # ── Claude (Anthropic 原生)
    elif provider == "claude":
        url = "https://api.anthropic.com/v1/messages"
        headers["x-api-key"]         = api_key
        headers["anthropic-version"] = "2023-06-01"
        payload = {
            "model": model,
            "max_tokens": 600,
            "system": system,
            "messages": [{"role": "user", "content": user}]
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["content"][0]["text"]

    else:
        raise ValueError(f"不支持的服务商：{provider}")


# ── 启动 ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    port = int(cfg.get("port", 8848))
    init_db()
    print(f"\n🦜 CiBird 词鸟已启动！访问 http://0.0.0.0:{port}\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="warning")
