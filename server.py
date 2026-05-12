#!/usr/bin/env python3
"""
CiBird 词鸟 - 后端服务 v2.2
FastAPI + SQLite，支持多 AI 服务商
新增：月/周/动物/食物/职业 静态词库接口
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

# ── 静态词库 ───────────────────────────────────────────────────
STATIC_DATA = {
    "月": [
        {"en":"January","zh":"一月","note":"1月 / Jan"},
        {"en":"February","zh":"二月","note":"2月 / Feb"},
        {"en":"March","zh":"三月","note":"3月 / Mar"},
        {"en":"April","zh":"四月","note":"4月 / Apr"},
        {"en":"May","zh":"五月","note":"5月 / May"},
        {"en":"June","zh":"六月","note":"6月 / Jun"},
        {"en":"July","zh":"七月","note":"7月 / Jul"},
        {"en":"August","zh":"八月","note":"8月 / Aug"},
        {"en":"September","zh":"九月","note":"9月 / Sep"},
        {"en":"October","zh":"十月","note":"10月 / Oct"},
        {"en":"November","zh":"十一月","note":"11月 / Nov"},
        {"en":"December","zh":"十二月","note":"12月 / Dec"},
    ],
    "周": [
        {"en":"Monday","zh":"星期一","note":"Mon"},
        {"en":"Tuesday","zh":"星期二","note":"Tue"},
        {"en":"Wednesday","zh":"星期三","note":"Wed"},
        {"en":"Thursday","zh":"星期四","note":"Thu"},
        {"en":"Friday","zh":"星期五","note":"Fri"},
        {"en":"Saturday","zh":"星期六","note":"Sat"},
        {"en":"Sunday","zh":"星期日","note":"Sun"},
    ],
    "动物": [
        {"en":"dog","zh":"狗","note":"🐶"},
        {"en":"cat","zh":"猫","note":"🐱"},
        {"en":"lion","zh":"狮子","note":"🦁"},
        {"en":"tiger","zh":"老虎","note":"🐯"},
        {"en":"elephant","zh":"大象","note":"🐘"},
        {"en":"bear","zh":"熊","note":"🐻"},
        {"en":"monkey","zh":"猴子","note":"🐵"},
        {"en":"giraffe","zh":"长颈鹿","note":"🦒"},
        {"en":"zebra","zh":"斑马","note":"🦓"},
        {"en":"wolf","zh":"狼","note":"🐺"},
        {"en":"fox","zh":"狐狸","note":"🦊"},
        {"en":"rabbit","zh":"兔子","note":"🐰"},
        {"en":"horse","zh":"马","note":"🐴"},
        {"en":"cow","zh":"奶牛","note":"🐮"},
        {"en":"pig","zh":"猪","note":"🐷"},
        {"en":"sheep","zh":"羊","note":"🐑"},
        {"en":"chicken","zh":"鸡","note":"🐔"},
        {"en":"duck","zh":"鸭子","note":"🦆"},
        {"en":"penguin","zh":"企鹅","note":"🐧"},
        {"en":"eagle","zh":"老鹰","note":"🦅"},
        {"en":"parrot","zh":"鹦鹉","note":"🦜"},
        {"en":"snake","zh":"蛇","note":"🐍"},
        {"en":"crocodile","zh":"鳄鱼","note":"🐊"},
        {"en":"shark","zh":"鲨鱼","note":"🦈"},
        {"en":"whale","zh":"鲸鱼","note":"🐋"},
        {"en":"dolphin","zh":"海豚","note":"🐬"},
        {"en":"frog","zh":"青蛙","note":"🐸"},
        {"en":"butterfly","zh":"蝴蝶","note":"🦋"},
        {"en":"bee","zh":"蜜蜂","note":"🐝"},
        {"en":"spider","zh":"蜘蛛","note":"🕷️"},
    ],
    "食物": [
        {"en":"rice","zh":"米饭","note":"🍚"},
        {"en":"noodles","zh":"面条","note":"🍜"},
        {"en":"bread","zh":"面包","note":"🍞"},
        {"en":"pizza","zh":"披萨","note":"🍕"},
        {"en":"burger","zh":"汉堡","note":"🍔"},
        {"en":"hot dog","zh":"热狗","note":"🌭"},
        {"en":"sandwich","zh":"三明治","note":"🥪"},
        {"en":"sushi","zh":"寿司","note":"🍣"},
        {"en":"steak","zh":"牛排","note":"🥩"},
        {"en":"chicken","zh":"鸡肉","note":"🍗"},
        {"en":"fish","zh":"鱼","note":"🐟"},
        {"en":"egg","zh":"鸡蛋","note":"🥚"},
        {"en":"salad","zh":"沙拉","note":"🥗"},
        {"en":"soup","zh":"汤","note":"🍲"},
        {"en":"dumpling","zh":"饺子","note":"🥟"},
        {"en":"apple","zh":"苹果","note":"🍎"},
        {"en":"banana","zh":"香蕉","note":"🍌"},
        {"en":"orange","zh":"橙子","note":"🍊"},
        {"en":"strawberry","zh":"草莓","note":"🍓"},
        {"en":"watermelon","zh":"西瓜","note":"🍉"},
        {"en":"grape","zh":"葡萄","note":"🍇"},
        {"en":"mango","zh":"芒果","note":"🥭"},
        {"en":"potato","zh":"土豆","note":"🥔"},
        {"en":"tomato","zh":"西红柿","note":"🍅"},
        {"en":"carrot","zh":"胡萝卜","note":"🥕"},
        {"en":"cake","zh":"蛋糕","note":"🎂"},
        {"en":"ice cream","zh":"冰淇淋","note":"🍦"},
        {"en":"chocolate","zh":"巧克力","note":"🍫"},
        {"en":"coffee","zh":"咖啡","note":"☕"},
        {"en":"tea","zh":"茶","note":"🍵"},
    ],
    "职业": [
        {"en":"doctor","zh":"医生","note":"🏥"},
        {"en":"nurse","zh":"护士","note":"👩‍⚕️"},
        {"en":"teacher","zh":"老师","note":"👩‍🏫"},
        {"en":"engineer","zh":"工程师","note":"👨‍💻"},
        {"en":"programmer","zh":"程序员","note":"💻"},
        {"en":"designer","zh":"设计师","note":"🎨"},
        {"en":"lawyer","zh":"律师","note":"⚖️"},
        {"en":"judge","zh":"法官","note":"👨‍⚖️"},
        {"en":"police","zh":"警察","note":"👮"},
        {"en":"firefighter","zh":"消防员","note":"🚒"},
        {"en":"soldier","zh":"士兵","note":"💂"},
        {"en":"chef","zh":"厨师","note":"👨‍🍳"},
        {"en":"waiter","zh":"服务员","note":"🍽️"},
        {"en":"driver","zh":"司机","note":"🚗"},
        {"en":"pilot","zh":"飞行员","note":"✈️"},
        {"en":"sailor","zh":"水手","note":"⚓"},
        {"en":"farmer","zh":"农民","note":"👨‍🌾"},
        {"en":"scientist","zh":"科学家","note":"🔬"},
        {"en":"artist","zh":"艺术家","note":"🎭"},
        {"en":"singer","zh":"歌手","note":"🎤"},
        {"en":"actor","zh":"演员","note":"🎬"},
        {"en":"athlete","zh":"运动员","note":"🏅"},
        {"en":"journalist","zh":"记者","note":"📰"},
        {"en":"photographer","zh":"摄影师","note":"📷"},
        {"en":"accountant","zh":"会计","note":"💰"},
        {"en":"manager","zh":"经理","note":"👔"},
        {"en":"secretary","zh":"秘书","note":"📋"},
        {"en":"salesperson","zh":"销售员","note":"🛍️"},
        {"en":"mechanic","zh":"机械师","note":"🔧"},
        {"en":"electrician","zh":"电工","note":"⚡"},
    ],
}

# ── AI 分类（需要 AI 生成的） ──────────────────────────────────
AI_CATEGORIES = {
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
            "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
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
            today = datetime.now().strftime('%Y-%m-%d')
            conn.execute("INSERT INTO punch_cards(date_str, count) VALUES(?,1) ON CONFLICT(date_str) DO UPDATE SET count=count+1", (today,))
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 静态词库接口（月/周/动物/食物/职业）
@app.get("/api/static/{cat}")
async def get_static(cat: str, token: str = Depends(verify_token)):
    if cat not in STATIC_DATA:
        raise HTTPException(status_code=404, detail="分类不存在")
    return {"items": STATIC_DATA[cat]}

# AI 词库接口（国家等需要 AI 的）
@app.get("/api/essentials/{cat}")
async def get_essentials(cat: str, token: str = Depends(verify_token)):
    if cat not in AI_CATEGORIES: raise HTTPException(status_code=404)
    system = "You are a world geography and language expert. Return ONLY JSON array of objects."
    prompt = f"{AI_CATEGORIES[cat]} Output format: {{'items': [{{'en': '...', 'zh': '...', 'note': '...'}}, ...]}}"
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
