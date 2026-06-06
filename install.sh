#!/bin/bash
# ══════════════════════════════════════════════════════════
#  CiBird 词鸟 安装脚本
#  一键部署你的私人英语单词本
#  项目地址：https://github.com/zhangyang-games/cibird
# ══════════════════════════════════════════════════════════

set -e

# ── 颜色 ──────────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

REPO_RAW="https://raw.githubusercontent.com/zhangyang-games/cibird/main"
INSTALL_DIR="$HOME/cibird"

# ── Banner ────────────────────────────────────────────────
print_banner() {
    clear
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "    ██████╗██╗██████╗ ██╗██████╗ ██████╗"
    echo "   ██╔════╝██║██╔══██╗██║██╔══██╗██╔══██╗"
    echo "   ██║     ██║██████╔╝██║██████╔╝██║  ██║"
    echo "   ██║     ██║██╔══██╗██║██╔══██╗██║  ██║"
    echo "   ╚██████╗██║██████╔╝██║██║  ██║██████╔╝"
    echo "    ╚═════╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═════╝"
    echo -e "${NC}"
    echo -e "${BOLD}  ┌─────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}  │  🦜  CiBird 词鸟 · 你的私人英语单词本      │${NC}"
    echo -e "${DIM}  │      AI造句 · 发音 · 推特/游戏英语场景     │${NC}"
    echo -e "${BOLD}  └─────────────────────────────────────────────┘${NC}"
    echo ""
}

# ── 步骤提示 ──────────────────────────────────────────────
step() { echo -e "\n${BOLD}${CYAN}[$1]${NC} $2"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
err()  { echo -e "  ${RED}✗ 错误：${NC}$1"; exit 1; }
info() { echo -e "  ${DIM}$1${NC}"; }
ask()  { echo -e "  ${YELLOW}→${NC} $1"; }

# ── 0. 检查基础依赖 ────────────────────────────────────────
check_deps() {
    step "0/6" "检查系统环境"

    for cmd in curl python3; do
        if ! command -v $cmd &>/dev/null; then
            info "正在安装 $cmd ..."
            if command -v apt-get &>/dev/null; then
                apt-get update -qq && apt-get install -y $cmd -qq
            elif command -v apk &>/dev/null; then
                apk add --no-cache $cmd
            elif command -v yum &>/dev/null; then
                yum install -y $cmd
            else
                err "请手动安装 $cmd 后重试"
            fi
        fi
        ok "$cmd 已就绪"
    done
}

# ── 1. 安装 Python 依赖 ────────────────────────────────────
install_python_deps() {
    step "1/6" "安装 Python 依赖包"
    info "需要安装：fastapi uvicorn httpx"

    # 判断是否需要 --break-system-packages（Ubuntu 22+）
    BREAK_SYS=""
    if python3 -c "import sys; exit(0 if sys.version_info>=(3,11) else 1)" 2>/dev/null; then
        BREAK_SYS="--break-system-packages"
    fi
    # 另一种判断：pip 报 externally-managed
    if pip3 install --help 2>&1 | grep -q 'break-system'; then
        BREAK_SYS="--break-system-packages"
    fi

    python3 -m pip install --quiet fastapi uvicorn[standard] httpx $BREAK_SYS 2>/dev/null \
        || pip3 install --quiet fastapi uvicorn[standard] httpx $BREAK_SYS 2>/dev/null \
        || err "pip 安装失败，请手动执行：pip3 install fastapi uvicorn httpx"

    ok "Python 依赖安装完成"
}

# ── 2. 下载项目文件 ────────────────────────────────────────
download_files() {
    step "2/6" "下载 CiBird 项目文件"
    mkdir -p "$INSTALL_DIR"

    for f in server.py index.html Cibird.png; do
        info "下载 $f ..."
        curl -fsSL "$REPO_RAW/$f" -o "$INSTALL_DIR/$f" \
            || err "下载 $f 失败，请检查网络或 GitHub 地址"
        ok "$f 已下载"
    done
}

# ── 3. 选择 AI 服务商 ──────────────────────────────────────
choose_provider() {
    step "3/6" "选择 AI 服务商"
    echo ""
    echo -e "  ${BOLD}请选择你要使用的 AI 服务商：${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Google Gemini   ${DIM}← 免费额度大，推荐新手${NC}"
    echo -e "  ${GREEN}2)${NC} DeepSeek        ${DIM}← 国产之光，便宜效果好${NC}"
    echo -e "  ${GREEN}3)${NC} Groq            ${DIM}← 速度极快，免费${NC}"
    echo -e "  ${GREEN}4)${NC} OpenRouter      ${DIM}← 一个Key用几十种模型${NC}"
    echo -e "  ${GREEN}5)${NC} Claude          ${DIM}← Anthropic，你有付费Key${NC}"
    echo -e "  ${GREEN}6)${NC} OpenAI          ${DIM}← ChatGPT 同款${NC}"
    echo ""
    read -p "  👉 输入编号 [1-6]：" PROVIDER_CHOICE

    case "$PROVIDER_CHOICE" in
        1)
            PROVIDER="gemini"
            MODEL="gemini-2.0-flash"
            info "获取 Key：https://aistudio.google.com/apikey"
            ;;
        2)
            PROVIDER="deepseek"
            MODEL="deepseek-chat"
            info "获取 Key：https://platform.deepseek.com"
            ;;
        3)
            PROVIDER="groq"
            MODEL="llama-3.1-8b-instant"
            info "获取 Key：https://console.groq.com"
            ;;
        4)
            PROVIDER="openrouter"
            MODEL="google/gemini-flash-1.5"
            info "获取 Key：https://openrouter.ai"
            ;;
        5)
            PROVIDER="claude"
            MODEL="claude-haiku-4-5-20251001"
            info "获取 Key：https://console.anthropic.com"
            ;;
        6)
            PROVIDER="openai"
            MODEL="gpt-4o-mini"
            info "获取 Key：https://platform.openai.com"
            ;;
        *)
            err "无效选择，请输入 1-6"
            ;;
    esac

    ok "已选择：$PROVIDER（模型：$MODEL）"

    echo ""
    read -p "  👉 请粘贴你的 API Key：" API_KEY
    [ -z "$API_KEY" ] && err "API Key 不能为空"
    ok "API Key 已录入"

    echo ""
    echo -e "  ${DIM}💡 如果你想用其他模型，可以直接改默认值，也可以回车使用默认${NC}"
    read -p "  👉 模型名称（默认 $MODEL，直接回车跳过）：" MODEL_INPUT
    [ -n "$MODEL_INPUT" ] && MODEL="$MODEL_INPUT"
    ok "模型：$MODEL"
}

# ── 4. 设置访问密码 ────────────────────────────────────────
setup_auth() {
    step "4/6" "设置登录账号"

    echo ""
    read -p "  👉 用户名（默认 admin，回车跳过）：" USERNAME
    [ -z "$USERNAME" ] && USERNAME="admin"
    ok "用户名：$USERNAME"

    echo ""
    while true; do
        read -s -p "  👉 设置登录密码（至少6位）：" PASSWORD
        echo ""
        [ ${#PASSWORD} -ge 6 ] && break
        echo -e "  ${RED}密码太短，请至少6位！${NC}"
    done
    read -s -p "  👉 再次确认密码：" PASSWORD2
    echo ""
    [ "$PASSWORD" != "$PASSWORD2" ] && err "两次密码不一致"
    ok "密码已设置"

    echo ""
    read -p "  👉 访问端口（默认 8848，回车跳过）：" PORT
    [ -z "$PORT" ] && PORT="8848"
    ok "端口：$PORT"

    # 生成密码 hash
    PASSWORD_HASH=$(python3 -c "import hashlib; print(hashlib.sha256('$PASSWORD'.encode()).hexdigest())")
}

# ── 5. 写入配置 ────────────────────────────────────────────
write_config() {
    step "5/6" "写入配置文件"

    cat > "$INSTALL_DIR/config.json" <<EOF
{
  "username": "$USERNAME",
  "password_hash": "$PASSWORD_HASH",
  "port": $PORT,
  "provider": "$PROVIDER",
  "api_key": "$API_KEY",
  "model": "$MODEL"
}
EOF
    chmod 600 "$INSTALL_DIR/config.json"
    ok "config.json 已写入（权限已设为仅自己可读）"
}

# ── 6. 启动服务 ────────────────────────────────────────────
start_service() {
    step "6/6" "启动 CiBird 服务"

    # 停掉旧进程
    if [ -f "$INSTALL_DIR/cibird.pid" ]; then
        OLD_PID=$(cat "$INSTALL_DIR/cibird.pid")
        kill "$OLD_PID" 2>/dev/null && info "已停止旧进程 (PID $OLD_PID)" || true
        rm -f "$INSTALL_DIR/cibird.pid"
    fi
    # 也搜一下
    pkill -f "server.py" 2>/dev/null || true
    sleep 1

    # 初始化数据库
    cd "$INSTALL_DIR"
    python3 -c "
import sys; sys.path.insert(0,'.')
from server import init_db
init_db()
print('  DB 初始化完成')
"
    # 后台启动
    nohup python3 "$INSTALL_DIR/server.py" >> "$INSTALL_DIR/cibird.log" 2>&1 &
    echo $! > "$INSTALL_DIR/cibird.pid"
    sleep 2

    # 验证是否启动成功
    if kill -0 $(cat "$INSTALL_DIR/cibird.pid") 2>/dev/null; then
        ok "服务启动成功！(PID $(cat $INSTALL_DIR/cibird.pid))"
    else
        err "服务启动失败，查看日志：cat $INSTALL_DIR/cibird.log"
    fi
}

# ── 写入快捷命令 ───────────────────────────────────────────
write_shortcut() {
    SHORTCUT="/usr/local/bin/cibird"
    cat > "$SHORTCUT" <<'SCRIPT'
#!/bin/bash
INSTALL_DIR="$HOME/cibird"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

get_pid() { [ -f "$INSTALL_DIR/cibird.pid" ] && cat "$INSTALL_DIR/cibird.pid" || echo ""; }
is_running() { PID=$(get_pid); [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; }
get_port() { python3 -c "import json; print(json.load(open('$INSTALL_DIR/config.json'))['port'])" 2>/dev/null || echo "8848"; }

case "$1" in
    start)
        if is_running; then
            echo -e "  ${YELLOW}词鸟已经在运行中${NC}"
        else
            cd "$INSTALL_DIR"
            nohup python3 server.py >> cibird.log 2>&1 &
            echo $! > cibird.pid
            sleep 1
            echo -e "  ${GREEN}✓ 词鸟已启动${NC}  访问 http://$(curl -s ifconfig.me 2>/dev/null || echo '你的IP'):$(get_port)"
        fi
        ;;
    stop)
        PID=$(get_pid)
        [ -n "$PID" ] && kill "$PID" 2>/dev/null && echo -e "  ${GREEN}✓ 词鸟已停止${NC}" || echo -e "  ${DIM}没有运行中的词鸟${NC}"
        rm -f "$INSTALL_DIR/cibird.pid"
        ;;
    restart)
        $0 stop; sleep 1; $0 start
        ;;
    log)
        tail -f "$INSTALL_DIR/cibird.log"
        ;;
    status)
        PORT=$(get_port)
        if is_running; then
            echo -e "  ${GREEN}● 词鸟运行中${NC}  PID $(get_pid)"
            echo -e "  ${DIM}访问地址：http://$(curl -s ifconfig.me 2>/dev/null || echo '你的IP'):$PORT${NC}"
        else
            echo -e "  ${RED}○ 词鸟未运行${NC}"
        fi
        ;;
    *)
        echo ""
        echo -e "  ${BOLD}🦜 CiBird 词鸟 管理命令${NC}"
        echo ""
        PORT=$(get_port)
        if is_running; then
            echo -e "  ${GREEN}● 状态：运行中${NC}  PID $(get_pid)"
        else
            echo -e "  ${RED}○ 状态：未运行${NC}"
        fi
        echo -e "  ${DIM}访问地址：http://你的IP:$PORT${NC}"
        echo ""
        echo -e "  ${CYAN}cibird start${NC}    启动"
        echo -e "  ${CYAN}cibird stop${NC}     停止"
        echo -e "  ${CYAN}cibird restart${NC}  重启"
        echo -e "  ${CYAN}cibird status${NC}   查看状态"
        echo -e "  ${CYAN}cibird log${NC}      查看日志"
        echo ""
        ;;
esac
SCRIPT
    chmod +x "$SHORTCUT" 2>/dev/null || true
    ok "快捷命令 cibird 已安装（可用 cibird start/stop/status）"
}

# ── 获取公网 IP ────────────────────────────────────────────
get_public_ip() {
    PUBLIC_IP=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null \
             || curl -s --connect-timeout 5 api.ipify.org 2>/dev/null \
             || echo "你的VPS公网IP")
}


# ── 导入单词 ───────────────────────────────────────────────
import_words() {
    echo ""
    echo -e "  ${BOLD}📖 导入多邻国单词本${NC}"
    echo -e "  ${DIM}从 GitHub 拉取 words.txt 导入到词库${NC}"
    echo ""
    WORDS_URL="https://raw.githubusercontent.com/zhangyang-games/cibird/main/words.txt"
    curl -sL "$WORDS_URL" | python3 -c "
import sys,sqlite3,pathlib
DB=pathlib.Path.home()/'cibird/cibird.db'
if not DB.exists(): print('  找不到数据库'); exit(1)
words=[l.strip().split('|',1) for l in sys.stdin if '|' in l]
conn=sqlite3.connect(DB)
existing=set(r[0].lower() for r in conn.execute('SELECT word FROM words'))
added=skipped=0
for w in words:
    if len(w)!=2: continue
    word,meaning=w
    if word.lower() in existing: skipped+=1; continue
    conn.execute('INSERT INTO words(word,meaning,phonetic,pos,examples,note) VALUES(?,?,?,?,?,?)',(word,meaning,'','','[]',''))
    existing.add(word.lower()); added+=1
conn.commit(); conn.close()
print(f'  ✓ 导入完成！新增 {added} 个，跳过 {skipped} 个')
" || echo -e "  ${RED}✗ 导入失败，请检查网络${NC}"
}
# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
print_banner

echo -e "  欢迎！这个脚本会帮你在 VPS 上部署 CiBird 词鸟。"
echo -e "  ${DIM}整个过程大约需要 2-3 分钟，请跟着提示一步步来。${NC}"
echo ""
read -p "  按回车键开始安装，Ctrl+C 取消..." _

check_deps
install_python_deps
download_files
choose_provider
setup_auth
write_config
start_service
write_shortcut
get_public_ip

# ── 可选：导入单词 ─────────────────────────────────────────
echo ""
read -p "  👉 是否导入你的多邻国单词本？（输入 y 导入，回车跳过）：" IMPORT_CHOICE
if [ "$IMPORT_CHOICE" = "y" ] || [ "$IMPORT_CHOICE" = "Y" ]; then
    import_words
fi

# ── 完成提示 ──────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}"
echo "  ┌──────────────────────────────────────────────┐"
echo "  │         🎉  CiBird 词鸟安装完成！            │"
echo "  └──────────────────────────────────────────────┘"
echo -e "${NC}"
echo -e "  ${BOLD}🌐 访问地址：${CYAN}http://$PUBLIC_IP:$PORT${NC}"
echo -e "  ${BOLD}👤 用户名：${NC}$USERNAME"
echo -e "  ${BOLD}🔑 密码：${NC}你刚才设置的密码"
echo ""
echo -e "  ${DIM}💡 管理命令：${NC}"
echo -e "  ${DIM}   cibird         查看状态${NC}"
echo -e "  ${DIM}   cibird stop    停止服务${NC}"
echo -e "  ${DIM}   cibird start   启动服务${NC}"
echo -e "  ${DIM}   cibird log     查看日志（排查问题用）${NC}"
echo ""
echo -e "  ${DIM}⚠️  如果访问不了，请确认防火墙已开放 $PORT 端口${NC}"
echo -e "  ${DIM}   Oracle Cloud 需要在安全列表里手动添加规则${NC}"
echo ""
echo -e "  ${BOLD}展翅高飞！🦜${NC}"
echo ""
