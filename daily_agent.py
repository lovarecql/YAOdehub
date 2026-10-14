import arxiv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import os

# ========= 配置 =========
today = datetime.now().strftime("%Y-%m-%d")
OUTPUT_PATH = f"reports/{today}_ai_daily.md"

# 【DeepSeek 配置】
llm_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
MODEL_NAME = "deepseek-flash" # 换成 deepseek-v4-pro 就是更强版本

# 1. Agent工具1：抓取arXiv今日AI论文
def fetch_arxiv_papers():
    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.LG OR cat:cs.CV",
        max_results=8,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    papers = []
    for res in search.results():
        papers.append({
            "title": res.title,
            "authors": [a.name for a in res.authors],
            "abstract": res.summary[:1200],
            "url": res.entry_id
        })
    return papers

# 2. Agent汇总+DeepSeek生成报告
def generate_report(papers):
    system_prompt = """
你是AI前沿研究助手，专业计算机/AI科研资讯整理专家。
任务：根据提供的arXiv最新论文，生成【每日AI前沿简报】
输出格式严格为Markdown：
1. 📄 论文亮点板块：每篇论文精简总结，提炼**核心创新点、技术突破**，不要直接复制摘要原文；附上论文链接
2. 💡 简短点评：该工作的价值、局限、潜在应用方向
不要冗余废话，文字精炼，适合科研人员快速浏览。
"""
    user_content = f"今日新论文列表：\n{papers}"
    resp = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.3
    )
    return resp.choices[0].message.content

if __name__ == "__main__":
    papers = fetch_arxiv_papers()
    md_report = generate_report(papers)
    # 写入md文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 🤖 AI前沿日报 | {today}\n\n")
        f.write(md_report)
    print(f"✅ 报告生成完成，保存到 {OUTPUT_PATH}")
