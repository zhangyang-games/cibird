# 🦜 CiBird 词鸟

> 你的私人英语单词本，住在你自己的 VPS 上，AI 自动造句，专攻推特/游戏英语场景

## 一行命令安装

```bash
curl -sSL https://raw.githubusercontent.com/zhangyang-games/cibird/main/install.sh | bash
```

安装过程会问你：
1. 选 AI 服务商（推荐 Gemini 免费额度 / DeepSeek 便宜好用）
2. 粘贴 API Key
3. 设置登录密码
4. 选端口（默认 8848）

完成后脚本会告诉你访问地址，打开浏览器就能用。

---

## 功能

- ➕ **添加单词** → AI 自动生成释义、音标、2 个例句（口语/推特/游戏场景）
- 🔊 **发音** → 点击发音按钮，浏览器直接朗读
- 📝 **笔记** → 每个单词可以写自己的理解或记忆方法
- ✦ **重新造句** → 一键让 AI 换新例句
- 🔍 **搜索** → 支持按单词、释义、笔记搜索
- 📱 **全平台** → 手机/电脑浏览器均可访问，SPA 单页应用

---

## 支持的 AI 服务商

| 服务商 | 推荐模型 | 备注 |
|--------|----------|------|
| Google Gemini | gemini-2.0-flash | 免费额度大，首选 |
| DeepSeek | deepseek-chat | 国产良心价 |
| Groq | llama-3.1-8b-instant | 速度极快，免费 |
| OpenRouter | 任意 | 一个 Key 用几十种模型 |
| Claude | claude-haiku-4-5 | Anthropic 原生 |
| OpenAI | gpt-4o-mini | ChatGPT 同款 |

---

## 管理命令

```bash
cibird           # 查看状态
cibird start     # 启动
cibird stop      # 停止
cibird restart   # 重启
cibird log       # 查看日志（排查问题）
```

---

## 常见问题

**Q: 装完打不开网页？**  
A: Oracle Cloud 需要在"安全列表"里添加端口规则，腾讯云/阿里云要在安全组开放端口。

**Q: AI 造句失败？**  
A: 运行 `cibird log` 看报错，通常是 API Key 填错了。

**Q: 怎么换 AI 服务商？**  
A: 编辑 `~/cibird/config.json`，修改 provider / api_key / model，然后 `cibird restart`。

---

## 文件结构

```
~/cibird/
├── server.py       后端服务
├── index.html      前端单页应用
├── config.json     配置（API Key 等，权限 600）
├── cibird.db       单词数据库（SQLite）
├── cibird.pid      进程 ID
└── cibird.log      运行日志
```

---

*展翅高飞 🦜*
