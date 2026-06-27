import re
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler
from models import Paper


class ArxivCrawler(BaseCrawler):
    """arXiv 爬虫 (arxiv.org)"""

    BASE = "https://arxiv.org"

    def crawl(self, url: str) -> list[Paper]:
        soup = self.fetch_soup(url)
        papers = []

        # arXiv listing: dt 标签包含论文信息
        for dt in soup.find_all("dt"):
            link = dt.find("a", title=re.compile(r"^(Abstract|pdf)"))
            if not link:
                continue

            paper_url = link.get("href", "")
            if paper_url.startswith("/"):
                paper_url = self.BASE + paper_url

            arxiv_id = link.get("id", "") or paper_url.split("/")[-1]

            # dd 标签紧跟在 dt 后面
            dd = dt.find_next("dd")
            if not dd:
                continue

            # 标题
            title_el = dd.find("div", class_="list-title")
            title = ""
            if title_el:
                title = self.clean_text(title_el.get_text())
                title = re.sub(r'^Title:\s*', '', title)

            # 作者
            authors_el = dd.find("div", class_="list-authors")
            authors = []
            if authors_el:
                for a in authors_el.find_all("a"):
                    name = self.clean_text(a.get_text())
                    if name:
                        authors.append(name)

            # 摘要
            abstract = ""
            # arXiv 列表页通常没有摘要，需要从详情页获取
            # 但我们可以尝试获取 subject 信息
            subject_el = dd.find("span", class_="primary-subject")
            subject = self.clean_text(subject_el.get_text()) if subject_el else ""

            papers.append(Paper(
                journal_url=url,
                title=title,
                authors=authors,
                abstract=subject,
                paper_url=paper_url,
                doi=arxiv_id,
                published_date="",
            ))

        # 如果没找到（可能是新版 arXiv），尝试其他解析方式
        if not papers:
            papers = self._fallback_parse(soup, url)

        return papers[:50]

    def _fallback_parse(self, soup: BeautifulSoup, journal_url: str) -> list[Paper]:
        """新版 arXiv 解析"""
        papers = []
        for item in soup.find_all(["li", "div"], class_=re.compile(r"arxiv-result|paper")):
            title_el = item.find(["h2", "h3", "p"], class_=re.compile(r"title"))
            if not title_el:
                continue
            link = title_el.find("a") or item.find("a")
            if not link:
                continue

            title = self.clean_text(link.get_text())
            paper_url = link.get("href", "")

            authors = []
            authors_el = item.find(["p", "span"], class_=re.compile(r"authors"))
            if authors_el:
                authors = [self.clean_text(a) for a in authors_el.get_text().split(",")]

            abstract = ""
            abstract_el = item.find(["span", "p"], class_=re.compile(r"abstract"))
            if abstract_el:
                abstract = self.clean_text(abstract_el.get_text())

            papers.append(Paper(
                journal_url=journal_url,
                title=title,
                authors=authors,
                abstract=abstract,
                paper_url=paper_url,
            ))

        return papers
