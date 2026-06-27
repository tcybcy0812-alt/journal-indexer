"""
期刊论文索引器 - 后端 API 服务
启动方式: python main.py 或 uvicorn main:app --host 0.0.0.0 --port 8000
"""
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import openpyxl

from models import CrawlRequest, CrawlResponse
from database import init_db, save_papers, get_papers, get_paper, get_journals, get_paper_count, search_papers
from crawler import get_crawler

app = FastAPI(title="期刊论文索引器", version="1.0.0")

# 允许所有来源的跨域请求（方便手机测试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    print("✅ 数据库已初始化")


# ── API 端点 ─────────────────────────────────────────────


@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest):
    """
    爬取期刊链接，提取所有论文信息。
    支持 Science、Nature 及通用期刊网站。
    """
    url = request.url.strip()
    if not url:
        raise HTTPException(400, "请输入有效的期刊链接")

    try:
        crawler = get_crawler(url)
        papers = crawler.crawl(url)

        if papers:
            saved = save_papers(url, papers)
            return CrawlResponse(
                success=True,
                journal_url=url,
                papers=papers,
                total=len(papers),
            )
        else:
            return CrawlResponse(
                success=False,
                journal_url=url,
                error="未能从页面中提取到论文，请确认链接是期刊目录页（TOC）",
            )
    except Exception as e:
        return CrawlResponse(
            success=False,
            journal_url=url,
            error=f"爬取失败: {str(e)}",
        )


@app.get("/api/papers")
async def list_papers(
    journal_url: str = Query(None, description="按期刊 URL 过滤"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """获取已爬取的论文列表"""
    papers = get_papers(journal_url=journal_url, limit=limit, offset=offset)
    total = get_paper_count()
    return {
        "papers": [p.model_dump() for p in papers],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/papers/search")
async def search(query: str = Query(..., min_length=2)):
    """搜索论文（标题或摘要）"""
    papers = search_papers(query)
    return {"papers": [p.model_dump() for p in papers], "query": query}


@app.get("/api/papers/{paper_id}")
async def paper_detail(paper_id: int):
    """获取单篇论文详情"""
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(404, "论文不存在")
    return paper.model_dump()


@app.get("/api/journals")
async def list_journals():
    """获取已爬取的期刊列表"""
    journals = get_journals()
    return {"journals": journals}


@app.get("/api/papers/export")
async def export_excel(journal_url: str = Query(None)):
    """导出论文为 Excel"""
    papers = get_papers(journal_url=journal_url, limit=1000)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "论文列表"

    # 表头
    headers = ["ID", "标题", "作者", "摘要", "原文链接", "DOI", "发表日期", "爬取时间", "来源期刊"]
    ws.append(headers)

    for p in papers:
        ws.append([
            p.id, p.title, ", ".join(p.authors), p.abstract,
            p.paper_url, p.doi, p.published_date, p.crawled_at, p.journal_url
        ])

    # 调整列宽
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 60
    ws.column_dimensions["E"].width = 40
    ws.column_dimensions["F"].width = 30
    ws.column_dimensions["G"].width = 15
    ws.column_dimensions["H"].width = 20
    ws.column_dimensions["I"].width = 40

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=papers.xlsx"},
    )


# ── 健康检查 ─────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "papers_total": get_paper_count()}


# ── 启动入口 ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("🚀 期刊论文索引器 启动中...")
    print("📱 API 地址: http://0.0.0.0:8000")
    print("📖 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
