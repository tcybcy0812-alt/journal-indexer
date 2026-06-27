import re
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler
from models import Paper


class ScienceCrawler(BaseCrawler):
    """Science 系列期刊爬虫 (science.org)"""

    BASE = "https://www.science.org"

    def crawl(self, url: str) -> list[Paper]:
        soup = self.fetch_soup(url)
        papers = []

        # Science.org 的论文列表在 article 标签或特定 div 中
        # 方法1：找 meta citation 标签（最可靠）
        articles = soup.find_all(["article", "div"], class_=re.compile(r"issue-item|card|toc-item", re.I))

        if not articles:
            # 方法2：找所有带标题链接的区块
            articles = soup.select("div.toc__section, div.article-item, li.issue-item, div.card-body")

        if not articles:
            # 方法3：范围搜索 — 找有 heading 链接的区域
            articles = self._fallback_parse(soup)

        for art in articles:
            title_el = art.find(["h2", "h3", "h4"], class_=re.compile(r"title|headline", re.I))
            if not title_el:
                title_el = art.find(["h2", "h3", "h4"])
            title_link = title_el.find("a") if title_el else art.find("a", href=re.compile(r"/doi/"))
            if not title_link:
                continue

            title = self.clean_text(title_link.get_text())
            if not title or len(title) < 5:
                continue

            paper_url = title_link.get("href", "")
            if paper_url and paper_url.startswith("/"):
                paper_url = self.BASE + paper_url

            # 作者
            authors = []
            author_els = art.find_all(["span", "a"], class_=re.compile(r"author|contrib", re.I))
            if not author_els:
                author_els = art.select('[class*="author"]')
            if not author_els:
                # 尝试从 text 中提取 "by ..." 模式
                text = art.get_text()
                by_match = re.search(r"By\s+(.+?)(?:\n|$)", text)
                if by_match:
                    authors = [a.strip() for a in by_match.group(1).split(",")]
            authors = [self.clean_text(a.get_text() if hasattr(a, 'get_text') else str(a)) for a in author_els]
            authors = list({a for a in authors if a and len(a) > 1})

            # 摘要 — 通常 TOC 页面没有完整摘要
            abstract = ""
            abstract_el = art.find(["p", "div"], class_=re.compile(r"abstract|summary|excerpt", re.I))
            if abstract_el:
                abstract = self.clean_text(abstract_el.get_text())

            # DOI
            doi = ""
            doi_match = re.search(r'10\.\d{4,}/[^\s"\']+', str(art))
            if doi_match:
                doi = doi_match.group(0).rstrip('.",')

            # 日期
            date = ""
            date_el = art.find(["time", "span"], class_=re.compile(r"date|published", re.I))
            if date_el:
                date = self.clean_text(date_el.get_text())

            papers.append(Paper(
                journal_url=url,
                title=title,
                authors=authors,
                abstract=abstract,
                paper_url=paper_url,
                doi=doi,
                published_date=date,
            ))

        return papers

    def _fallback_parse(self, soup: BeautifulSoup) -> list:
        """降级解析：找所有包含链接的标题区域"""
        items = []
        for h in soup.find_all(["h2", "h3", "h4"]):
            link = h.find("a", href=re.compile(r"/doi/|/doi/full/"))
            if link:
                # 把 h 的父级 element 作为 item
                parent = h.parent
                while parent and parent.name not in ("article", "section", "li", "div"):
                    parent = parent.parent
                if parent:
                    items.append(parent)
        return items
