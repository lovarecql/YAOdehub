import arxiv
import requests
from openai import OpenAI
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import glob
import json
import time
import traceback

# ========= 配置 =========
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
OUTPUT_PATH = f"reports/{today}_ai_daily.md"

# 【DeepSeek 配置】
llm_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
MODEL_NAME = "deepseek-flash"


def fetch_arxiv_papers():
    """抓取 arXiv 最新 AI 论文（加重试应对限流）"""
    client = arxiv.Client(num_retries=5, delay_seconds=5)
    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.LG OR cat:cs.CV",
        max_results=8,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    papers = []
    for res in client.results(search):
        papers.append({
            "title": res.title,
            "authors": [a.name for a in res.authors],
            "abstract": res.summary[:1200],
            "url": res.entry_id
        })
    return papers


def fetch_arxiv_papers_with_retry(max_attempts=3):
    """外层重试：捕获所有可能的 arxiv/网络异常"""
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"📥 [arXiv] 第 {attempt}/{max_attempts} 次抓取...")
            papers = fetch_arxiv_papers()
            print(f"✅ [arXiv] 成功获取 {len(papers)} 篇论文")
            return papers
        except arxiv.ArxivError as e:
            # arxiv 所有异常的基类：HTTPError, UnexpectedEmptyPageError 等
            last_err = e
            print(f"⚠️ [arXiv] ArxivError: {e}")
        except requests.exceptions.RequestException as e:
            # 网络层异常：ConnectionError, Timeout 等
            last_err = e
            print(f"⚠️ [arXiv] NetworkError: {e}")
        except Exception as e:
            # 兜底
            last_err = e
            print(f"⚠️ [arXiv] UnexpectedError: {e}")

        if attempt < max_attempts:
            wait = 20 * attempt
            print(f"⏳ 等待 {wait} 秒后重试...")
            time.sleep(wait)

    print(f"❌ [arXiv] 全部 {max_attempts} 次重试耗尽，放弃抓取")
    raise last_err


def generate_report(papers):
    """用 DeepSeek 汇总生成日报"""
    system_prompt = """
你是AI前沿研究助手，专业计算机/AI科研资讯整理专家。
任务：根据提供的arXiv最新论文，生成【每日AI前沿简报】
输出格式严格为Markdown：
1. 📄 论文亮点板块：每篇论文精简总结，提炼**核心创新点、技术突破**，不要直接复制摘要原文；附上论文链接
2. 💡 简短点评：该工作的价值、局限、潜在应用方向
不要冗余废话，文字精炼，适合科研人员快速浏览。
"""
    user_content = f"今日新论文列表：\n{json.dumps(papers, ensure_ascii=False, indent=2)}"

    print(f"🤖 [LLM] 调用 {MODEL_NAME}，输入 {len(user_content)} 字符...")
    resp = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.3
    )
    print(f"✅ [LLM] 调用成功，输出 {len(resp.choices[0].message.content)} 字符")
    return resp.choices[0].message.content


def rebuild_index():
    """重建日报索引 JSON"""
    report_files = sorted(glob.glob("reports/*_ai_daily.md"), reverse=True)
    reports = []
    for path in report_files:
        filename = os.path.basename(path)
        date = filename.split("_")[0]
        reports.append({
            "date": date,
            "file": filename,
            "title": f"AI前沿日报 {date}"
        })
    with open("reports/index.json", "w", encoding="utf-8") as f:
        json.dump(
            {"updated": reports[0]["date"] if reports else "", "reports": reports},
            f,
            ensure_ascii=False,
            indent=2
        )
    print(f"📚 索引已更新，共 {len(reports)} 篇报告")


if __name__ == "__main__":
    print("=" * 50)
    print(f"🤖 AI 前沿日报生成器 | 北京时间 {today}")
    print("=" * 50)

    try:
        # Step 1: 抓论文
        papers = fetch_arxiv_papers_with_retry()
        if not papers:
            print("❌ 抓到的论文列表为空，终止生成")
            exit(1)

        # Step 2: 调 LLM 生成
        try:
            md_report = generate_report(papers)
        except Exception as e:
            print(f"❌ [LLM] 调用失败: {e}")
            traceback.print_exc()
            exit(1)

        # Step 3: 写文件
        os.makedirs("reports", exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(f"# 🤖 AI前沿日报 | {today}\n\n")
            f.write(md_report)
        print(f"✅ 报告已保存: {OUTPUT_PATH}")

        # Step 4: 更新索引
        rebuild_index()

        print("=" * 50)
        print("🎉 全部完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n💥 致命错误: {e}")
        print("\n完整堆栈:")
        traceback.print_exc()
        exit(1)
