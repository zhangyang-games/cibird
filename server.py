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
    "国家": [
        {"en":"Afghanistan","zh":"阿富汗","note":"亚洲"},
        {"en":"Albania","zh":"阿尔巴尼亚","note":"欧洲"},
        {"en":"Algeria","zh":"阿尔及利亚","note":"非洲"},
        {"en":"Andorra","zh":"安道尔","note":"欧洲"},
        {"en":"Angola","zh":"安哥拉","note":"非洲"},
        {"en":"Antigua and Barbuda","zh":"安提瓜和巴布达","note":"北美洲"},
        {"en":"Argentina","zh":"阿根廷","note":"南美洲"},
        {"en":"Armenia","zh":"亚美尼亚","note":"亚洲"},
        {"en":"Australia","zh":"澳大利亚","note":"大洋洲"},
        {"en":"Austria","zh":"奥地利","note":"欧洲"},
        {"en":"Azerbaijan","zh":"阿塞拜疆","note":"亚洲"},
        {"en":"Bahamas","zh":"巴哈马","note":"北美洲"},
        {"en":"Bahrain","zh":"巴林","note":"亚洲"},
        {"en":"Bangladesh","zh":"孟加拉国","note":"亚洲"},
        {"en":"Barbados","zh":"巴巴多斯","note":"北美洲"},
        {"en":"Belarus","zh":"白俄罗斯","note":"欧洲"},
        {"en":"Belgium","zh":"比利时","note":"欧洲"},
        {"en":"Belize","zh":"伯利兹","note":"北美洲"},
        {"en":"Benin","zh":"贝宁","note":"非洲"},
        {"en":"Bhutan","zh":"不丹","note":"亚洲"},
        {"en":"Bolivia","zh":"玻利维亚","note":"南美洲"},
        {"en":"Bosnia and Herzegovina","zh":"波斯尼亚和黑塞哥维那","note":"欧洲"},
        {"en":"Botswana","zh":"博茨瓦纳","note":"非洲"},
        {"en":"Brazil","zh":"巴西","note":"南美洲"},
        {"en":"Brunei","zh":"文莱","note":"亚洲"},
        {"en":"Bulgaria","zh":"保加利亚","note":"欧洲"},
        {"en":"Burkina Faso","zh":"布基纳法索","note":"非洲"},
        {"en":"Burundi","zh":"布隆迪","note":"非洲"},
        {"en":"Cabo Verde","zh":"佛得角","note":"非洲"},
        {"en":"Cambodia","zh":"柬埔寨","note":"亚洲"},
        {"en":"Cameroon","zh":"喀麦隆","note":"非洲"},
        {"en":"Canada","zh":"加拿大","note":"北美洲"},
        {"en":"Central African Republic","zh":"中非共和国","note":"非洲"},
        {"en":"Chad","zh":"乍得","note":"非洲"},
        {"en":"Chile","zh":"智利","note":"南美洲"},
        {"en":"China","zh":"中国","note":"亚洲"},
        {"en":"Colombia","zh":"哥伦比亚","note":"南美洲"},
        {"en":"Comoros","zh":"科摩罗","note":"非洲"},
        {"en":"Congo","zh":"刚果共和国","note":"非洲"},
        {"en":"Costa Rica","zh":"哥斯达黎加","note":"北美洲"},
        {"en":"Croatia","zh":"克罗地亚","note":"欧洲"},
        {"en":"Cuba","zh":"古巴","note":"北美洲"},
        {"en":"Cyprus","zh":"塞浦路斯","note":"欧洲"},
        {"en":"Czech Republic","zh":"捷克","note":"欧洲"},
        {"en":"Denmark","zh":"丹麦","note":"欧洲"},
        {"en":"Djibouti","zh":"吉布提","note":"非洲"},
        {"en":"Dominica","zh":"多米尼克","note":"北美洲"},
        {"en":"Dominican Republic","zh":"多米尼加共和国","note":"北美洲"},
        {"en":"DR Congo","zh":"刚果民主共和国","note":"非洲"},
        {"en":"Ecuador","zh":"厄瓜多尔","note":"南美洲"},
        {"en":"Egypt","zh":"埃及","note":"非洲"},
        {"en":"El Salvador","zh":"萨尔瓦多","note":"北美洲"},
        {"en":"Equatorial Guinea","zh":"赤道几内亚","note":"非洲"},
        {"en":"Eritrea","zh":"厄立特里亚","note":"非洲"},
        {"en":"Estonia","zh":"爱沙尼亚","note":"欧洲"},
        {"en":"Eswatini","zh":"斯威士兰","note":"非洲"},
        {"en":"Ethiopia","zh":"埃塞俄比亚","note":"非洲"},
        {"en":"Fiji","zh":"斐济","note":"大洋洲"},
        {"en":"Finland","zh":"芬兰","note":"欧洲"},
        {"en":"France","zh":"法国","note":"欧洲"},
        {"en":"Gabon","zh":"加蓬","note":"非洲"},
        {"en":"Gambia","zh":"冈比亚","note":"非洲"},
        {"en":"Georgia","zh":"格鲁吉亚","note":"亚洲"},
        {"en":"Germany","zh":"德国","note":"欧洲"},
        {"en":"Ghana","zh":"加纳","note":"非洲"},
        {"en":"Greece","zh":"希腊","note":"欧洲"},
        {"en":"Grenada","zh":"格林纳达","note":"北美洲"},
        {"en":"Guatemala","zh":"危地马拉","note":"北美洲"},
        {"en":"Guinea","zh":"几内亚","note":"非洲"},
        {"en":"Guinea-Bissau","zh":"几内亚比绍","note":"非洲"},
        {"en":"Guyana","zh":"圭亚那","note":"南美洲"},
        {"en":"Haiti","zh":"海地","note":"北美洲"},
        {"en":"Honduras","zh":"洪都拉斯","note":"北美洲"},
        {"en":"Hungary","zh":"匈牙利","note":"欧洲"},
        {"en":"Iceland","zh":"冰岛","note":"欧洲"},
        {"en":"India","zh":"印度","note":"亚洲"},
        {"en":"Indonesia","zh":"印度尼西亚","note":"亚洲"},
        {"en":"Iran","zh":"伊朗","note":"亚洲"},
        {"en":"Iraq","zh":"伊拉克","note":"亚洲"},
        {"en":"Ireland","zh":"爱尔兰","note":"欧洲"},
        {"en":"Israel","zh":"以色列","note":"亚洲"},
        {"en":"Italy","zh":"意大利","note":"欧洲"},
        {"en":"Ivory Coast","zh":"科特迪瓦","note":"非洲"},
        {"en":"Jamaica","zh":"牙买加","note":"北美洲"},
        {"en":"Japan","zh":"日本","note":"亚洲"},
        {"en":"Jordan","zh":"约旦","note":"亚洲"},
        {"en":"Kazakhstan","zh":"哈萨克斯坦","note":"亚洲"},
        {"en":"Kenya","zh":"肯尼亚","note":"非洲"},
        {"en":"Kiribati","zh":"基里巴斯","note":"大洋洲"},
        {"en":"Kuwait","zh":"科威特","note":"亚洲"},
        {"en":"Kyrgyzstan","zh":"吉尔吉斯斯坦","note":"亚洲"},
        {"en":"Laos","zh":"老挝","note":"亚洲"},
        {"en":"Latvia","zh":"拉脱维亚","note":"欧洲"},
        {"en":"Lebanon","zh":"黎巴嫩","note":"亚洲"},
        {"en":"Lesotho","zh":"莱索托","note":"非洲"},
        {"en":"Liberia","zh":"利比里亚","note":"非洲"},
        {"en":"Libya","zh":"利比亚","note":"非洲"},
        {"en":"Liechtenstein","zh":"列支敦士登","note":"欧洲"},
        {"en":"Lithuania","zh":"立陶宛","note":"欧洲"},
        {"en":"Luxembourg","zh":"卢森堡","note":"欧洲"},
        {"en":"Madagascar","zh":"马达加斯加","note":"非洲"},
        {"en":"Malawi","zh":"马拉维","note":"非洲"},
        {"en":"Malaysia","zh":"马来西亚","note":"亚洲"},
        {"en":"Maldives","zh":"马尔代夫","note":"亚洲"},
        {"en":"Mali","zh":"马里","note":"非洲"},
        {"en":"Malta","zh":"马耳他","note":"欧洲"},
        {"en":"Marshall Islands","zh":"马绍尔群岛","note":"大洋洲"},
        {"en":"Mauritania","zh":"毛里塔尼亚","note":"非洲"},
        {"en":"Mauritius","zh":"毛里求斯","note":"非洲"},
        {"en":"Mexico","zh":"墨西哥","note":"北美洲"},
        {"en":"Micronesia","zh":"密克罗尼西亚","note":"大洋洲"},
        {"en":"Moldova","zh":"摩尔多瓦","note":"欧洲"},
        {"en":"Monaco","zh":"摩纳哥","note":"欧洲"},
        {"en":"Mongolia","zh":"蒙古","note":"亚洲"},
        {"en":"Montenegro","zh":"黑山","note":"欧洲"},
        {"en":"Morocco","zh":"摩洛哥","note":"非洲"},
        {"en":"Mozambique","zh":"莫桑比克","note":"非洲"},
        {"en":"Myanmar","zh":"缅甸","note":"亚洲"},
        {"en":"Namibia","zh":"纳米比亚","note":"非洲"},
        {"en":"Nauru","zh":"瑙鲁","note":"大洋洲"},
        {"en":"Nepal","zh":"尼泊尔","note":"亚洲"},
        {"en":"Netherlands","zh":"荷兰","note":"欧洲"},
        {"en":"New Zealand","zh":"新西兰","note":"大洋洲"},
        {"en":"Nicaragua","zh":"尼加拉瓜","note":"北美洲"},
        {"en":"Niger","zh":"尼日尔","note":"非洲"},
        {"en":"Nigeria","zh":"尼日利亚","note":"非洲"},
        {"en":"North Korea","zh":"朝鲜","note":"亚洲"},
        {"en":"North Macedonia","zh":"北马其顿","note":"欧洲"},
        {"en":"Norway","zh":"挪威","note":"欧洲"},
        {"en":"Oman","zh":"阿曼","note":"亚洲"},
        {"en":"Pakistan","zh":"巴基斯坦","note":"亚洲"},
        {"en":"Palau","zh":"帕劳","note":"大洋洲"},
        {"en":"Palestine","zh":"巴勒斯坦","note":"亚洲"},
        {"en":"Panama","zh":"巴拿马","note":"北美洲"},
        {"en":"Papua New Guinea","zh":"巴布亚新几内亚","note":"大洋洲"},
        {"en":"Paraguay","zh":"巴拉圭","note":"南美洲"},
        {"en":"Peru","zh":"秘鲁","note":"南美洲"},
        {"en":"Philippines","zh":"菲律宾","note":"亚洲"},
        {"en":"Poland","zh":"波兰","note":"欧洲"},
        {"en":"Portugal","zh":"葡萄牙","note":"欧洲"},
        {"en":"Qatar","zh":"卡塔尔","note":"亚洲"},
        {"en":"Romania","zh":"罗马尼亚","note":"欧洲"},
        {"en":"Russia","zh":"俄罗斯","note":"欧洲/亚洲"},
        {"en":"Rwanda","zh":"卢旺达","note":"非洲"},
        {"en":"Saint Kitts and Nevis","zh":"圣基茨和尼维斯","note":"北美洲"},
        {"en":"Saint Lucia","zh":"圣卢西亚","note":"北美洲"},
        {"en":"Saint Vincent and the Grenadines","zh":"圣文森特和格林纳丁斯","note":"北美洲"},
        {"en":"Samoa","zh":"萨摩亚","note":"大洋洲"},
        {"en":"San Marino","zh":"圣马力诺","note":"欧洲"},
        {"en":"Sao Tome and Principe","zh":"圣多美和普林西比","note":"非洲"},
        {"en":"Saudi Arabia","zh":"沙特阿拉伯","note":"亚洲"},
        {"en":"Senegal","zh":"塞内加尔","note":"非洲"},
        {"en":"Serbia","zh":"塞尔维亚","note":"欧洲"},
        {"en":"Seychelles","zh":"塞舌尔","note":"非洲"},
        {"en":"Sierra Leone","zh":"塞拉利昂","note":"非洲"},
        {"en":"Singapore","zh":"新加坡","note":"亚洲"},
        {"en":"Slovakia","zh":"斯洛伐克","note":"欧洲"},
        {"en":"Slovenia","zh":"斯洛文尼亚","note":"欧洲"},
        {"en":"Solomon Islands","zh":"所罗门群岛","note":"大洋洲"},
        {"en":"Somalia","zh":"索马里","note":"非洲"},
        {"en":"South Africa","zh":"南非","note":"非洲"},
        {"en":"South Korea","zh":"韩国","note":"亚洲"},
        {"en":"South Sudan","zh":"南苏丹","note":"非洲"},
        {"en":"Spain","zh":"西班牙","note":"欧洲"},
        {"en":"Sri Lanka","zh":"斯里兰卡","note":"亚洲"},
        {"en":"Sudan","zh":"苏丹","note":"非洲"},
        {"en":"Suriname","zh":"苏里南","note":"南美洲"},
        {"en":"Sweden","zh":"瑞典","note":"欧洲"},
        {"en":"Switzerland","zh":"瑞士","note":"欧洲"},
        {"en":"Syria","zh":"叙利亚","note":"亚洲"},
        {"en":"Taiwan","zh":"台湾","note":"亚洲"},
        {"en":"Tajikistan","zh":"塔吉克斯坦","note":"亚洲"},
        {"en":"Tanzania","zh":"坦桑尼亚","note":"非洲"},
        {"en":"Thailand","zh":"泰国","note":"亚洲"},
        {"en":"Timor-Leste","zh":"东帝汶","note":"亚洲"},
        {"en":"Togo","zh":"多哥","note":"非洲"},
        {"en":"Tonga","zh":"汤加","note":"大洋洲"},
        {"en":"Trinidad and Tobago","zh":"特立尼达和多巴哥","note":"北美洲"},
        {"en":"Tunisia","zh":"突尼斯","note":"非洲"},
        {"en":"Turkey","zh":"土耳其","note":"亚洲/欧洲"},
        {"en":"Turkmenistan","zh":"土库曼斯坦","note":"亚洲"},
        {"en":"Tuvalu","zh":"图瓦卢","note":"大洋洲"},
        {"en":"Uganda","zh":"乌干达","note":"非洲"},
        {"en":"Ukraine","zh":"乌克兰","note":"欧洲"},
        {"en":"United Arab Emirates","zh":"阿联酋","note":"亚洲"},
        {"en":"United Kingdom","zh":"英国","note":"欧洲"},
        {"en":"United States","zh":"美国","note":"北美洲"},
        {"en":"Uruguay","zh":"乌拉圭","note":"南美洲"},
        {"en":"Uzbekistan","zh":"乌兹别克斯坦","note":"亚洲"},
        {"en":"Vanuatu","zh":"瓦努阿图","note":"大洋洲"},
        {"en":"Vatican City","zh":"梵蒂冈","note":"欧洲"},
        {"en":"Venezuela","zh":"委内瑞拉","note":"南美洲"},
        {"en":"Vietnam","zh":"越南","note":"亚洲"},
        {"en":"Yemen","zh":"也门","note":"亚洲"},
        {"en":"Zambia","zh":"赞比亚","note":"非洲"},
        {"en":"Zimbabwe","zh":"津巴布韦","note":"非洲"},
    ],
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
