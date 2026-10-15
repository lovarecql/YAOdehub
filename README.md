# 🤖 AI 前沿日报

每天由 GitHub Actions 自动抓取 arXiv 最新 AI 论文，交给 DeepSeek 汇总成 Markdown 日报，并提交回本仓库。

## 目录

- `daily_agent.py`：抓取论文 + 调用 LLM 生成日报 + 重建 `reports/index.json`
- `.github/workflows/daily_ai_report.yml`：定时（UTC 06:00）或手动触发的自动化任务
- `index.html`：日报浏览网页（GitHub Pages 托管）
- `reports/`：生成的日报与索引

## 网页如何工作

网页是纯静态页面，启动时读取 `reports/index.json` 获得日报列表，再按需加载对应 Markdown 并渲染。无需任何后端服务器。

### 开启 GitHub Pages（一次性）

1. 打开仓库 **Settings → Pages**
2. **Source** 选择 `Deploy from a branch`
3. 分支选 `main`，目录选 `/ (root)`
4. 保存后稍等 1 分钟，访问 `https://<用户名>.github.io/Yaodehub/` 即可

仓库根目录的 `.nojekyll` 会禁用 Jekyll 处理，保证 `reports/*.md` 以原始文本返回给网页。

### 本地预览

```powershell
python -m http.server 8000
```

然后浏览器打开 `http://localhost:8000/`。注意不要直接双击打开 `index.html`，浏览器会因跨域限制无法读取 `index.json`。

## 手动触发一次日报

在仓库 **Actions** 页选择 `Daily AI Frontier Report`，点 **Run workflow**。
