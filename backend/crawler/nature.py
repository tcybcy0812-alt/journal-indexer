import re
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler
from models import Paper


class NatureCrawler(BaseCrawler):
    """Nature 系列期刊爬虫 (nature.com)"""

    BASE = "https://www.nature.com"

    def crawl(self, url: str) -> list[Paper]:
        soup = self.fetch_soup(url)
        papers = []

        # Nature 文章通常在 <article> 标签或 <li> 列表中
        articles = soup.find_all("article", class_=re.compile(r"article|toc-item", re.I))
        if not articles:
            articles = soup.find_all("li", class_=re.compile(r"article|toc-item|mb", re.I))
        if not articles:
            articles = soup.select('[class*="toc"] article, [class*="toc"] li, div[class*="article-item"]')

        if not articles:
            articles = self._fallback_parse(soup)

        for art in articles:
            # 标题
            title_el = art.find(["h2", "h3", "a"], class_=re.compile(r"title|link", re.I))
            if not title_el:
                title_el = art.find("a", href=re.compile(r"/articles/"))
            if not title_el:
                continue

            title = self.clean_text(title_el.get_text())
            if not title or len(title) < 5:
                continue

            paper_url = title_el.get("href", "") if title_el.name == "a" else ""
            if not paper_url:
                link = art.find("a", href=re.compile(r"/articles/"))
                if link:
                    paper_url = link.get("href", "")
            if paper_url and paper_url.startswith("/"):
                paper_url = self.BASE + paper_url

            # 作者
            authors = []
            author_els = art.select('[class*="author"], [itemprop="author"], [data-test="author"]')
            for a in author_els:
                name = self.clean_text(a.get_text())
                if name and len(name) > 1:
                    authors.append(name)

            # 摘要/摘要片段
            abstract = ""
            abstract_el = art.find(["p", "div"], class_=re.compile(r"abstract|summary|excerpt|description", re.I))
            if abstract_el:
                abstract = self.clean_text(abstract_el.get_text())

            # DOI
            doi = ""
            doi_match = re.search(r'10\.1038/[^\s"\']+', str(art))
            if doi_match:
                doi = doi_match.group(0).rstrip('.",')

            # 日期
            date = ""
            time_el = art.find("time")
            if time_el and time_el.get("datetime"):
                date = time_el["datetime"]
            elif time_el:
                date = self.clean_text(time_el.get_text())

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
        items = []
        for a in soup.find_all("a", href=re.compile(r"/articles/s\d{5}")):
            parent = a.parent
            for _ in range(4):
                if parent and parent.name in ("article", "li", "div"):
                    items.append(parent)
                    break
                parent = parent.parent if parent else None
        return items
