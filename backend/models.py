from pydantic import BaseModel
from typing import Optional


class Paper(BaseModel):
    """单篇论文"""
    id: Optional[int] = None
    journal_url: str
    title: str
    authors: list[str] = []
    abstract: str = ""
    paper_url: str = ""
    doi: str = ""
    published_date: str = ""
    crawled_at: str = ""


class CrawlRequest(BaseModel):
    """爬取请求"""
    url: str


class CrawlResponse(BaseModel):
    """爬取结果"""
    success: bool
    journal_url: str
    papers: list[Paper] = []
    error: str = ""
    total: int = 0
