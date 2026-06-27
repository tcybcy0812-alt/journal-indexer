import re
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from crawler.base import BaseCrawler
from models import Paper


class GenericCrawler(BaseCrawler):
    """
    通用爬虫：尝试多种策略从任意期刊页面提取论文信息。
    优先级：meta 标签 → JSON-LD → RSS → 启发式解析
    """

    def crawl(self, url: str) -> list[Paper]:
        soup = self.fetch_soup(url)

        # 策略 1：Google Scholar / HighWire meta citation 标签
        papers = self._parse_meta_tags(soup, url)
        if papers:
            return papers

        # 策略 2：JSON-LD 结构化数据
        papers = self._parse_jsonld(soup, url)
        if papers:
            return papers

        # 策略 3：尝试 RSS feed
        papers = self._try_rss(url)
        if papers:
            return papers

        # 策略 4：启发式 HTML 解析
        papers = self._heuristic_parse(soup, url)
        return papers

    # ── 策略 1: meta citation 标签 ──────────────────────

    def _parse_meta_tags(self, soup: BeautifulSoup, journal_url: str) -> list[Paper]:
        """解析 Google Scholar 风格的 meta 标签"""
        # 先收集所有 citation_* meta 标签
        metas = soup.find_all("meta")
        citation_data: dict[str, list[str]] = {}  # key → values

        for m in metas:
            name = m.get("name", "")
            content = m.get("content", "")
            if name.startswith("citation_") and content:
                citation_data.setdefault(name, []).append(content)

        if not citation_data.get("citation_title"):
            return []

        # 按索引分组（citation_title[0], citation_author[0] 属于同一篇）
        # 多数期刊用重复 meta name 表示多篇，用索引匹配
        titles = citation_data.get("citation_title", [])
        papers = []

        for i, title in enumerate(titles):
            authors = []
            all_authors = citation_data.get("citation_author", [])
            # 简单处理：所有 author 分配给第一篇（大多数 TOC 每页只有一篇）
            if i == 0:
                authors = all_authors

            doi = ""
            dois = citation_data.get("citation_doi", [])
            if i < len(dois):
                doi = dois[i]

            paper_url = ""
            urls = citation_data.get("citation_fulltext_url", []) or citation_data.get("citation_abstract_html_url", [])
            if i < len(urls):
                paper_url = urls[i]

            date = ""
            dates = citation_data.get("citation_date", []) or citation_data.get("citation_publication_date", [])
            if i < len(dates):
                date = dates[i]

            abstract = ""
            abstracts = citation_data.get("citation_abstract", [])
            if i < len(abstracts):
                abstract = abstracts[i]

            papers.append(Paper(
                journal_url=journal_url,
                title=self.clean_text(title),
                authors=[self.clean_text(a) for a in authors],
                abstract=self.clean_text(abstract),
                paper_url=paper_url,
                doi=doi,
                published_date=date,
            ))

        return papers

    # ── 策略 2: JSON-LD ──────────────────────────────────

    def _parse_jsonld(self, soup: BeautifulSoup, journal_url: str) -> list[Paper]:
        papers = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            # 可能是 dict 或 list
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                at_type = item.get("@type", "")
                if isinstance(at_type, list):
                    at_type = " ".join(at_type)
                if "scholarly" not in str(at_type).lower() and "article" not in str(at_type).lower():
                    continue

                title = self.clean_text(item.get("name", "") or item.get("headline", ""))
                if not title:
                    continue

                authors = []
                for a in item.get("author", []) or []:
                    if isinstance(a, dict):
                        authors.append(a.get("name", ""))
                    elif isinstance(a, str):
                        authors.append(a)

                abstract = self.clean_text(item.get("description", ""))
                doi = item.get("doi", "") or item.get("@id", "")
                paper_url = item.get("url", "") or item.get("sameAs", "")
                if isinstance(paper_url, list):
                    paper_url = paper_url[0] if paper_url else ""
                date = item.get("datePublished", "")

                papers.append(Paper(
                    journal_url=journal_url,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    paper_url=paper_url,
                    doi=doi,
                    published_date=date,
                ))
        return papers

    # ── 策略 3: RSS ──────────────────────────────────────

    def _try_rss(self, url: str) -> list[Paper]:
        """尝试从常见 RSS 路径获取"""
        parsed = urlparse(url)
        rss_paths = [
            f"{parsed.scheme}://{parsed.netloc}/rss",
            f"{parsed.scheme}://{parsed.netloc}/feed",
            f"{parsed.scheme}://{parsed.netloc}/feeds",
        ]
        import feedparser
        for rss_url in rss_paths:
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    papers = []
                    for entry in feed.entries[:50]:
                        papers.append(Paper(
                            journal_url=url,
                            title=self.clean_text(entry.get("title", "")),
                            authors=[a.get("name", "") for a in entry.get("authors", [])],
                            abstract=self.clean_text(entry.get("summary", "")),
                            paper_url=entry.get("link", ""),
                            doi=entry.get("id", ""),
                            published_date=entry.get("published", ""),
                        ))
                    return papers
            except Exception:
                continue
        return []

    # ── 策略 4: 启发式 HTML 解析 ─────────────────────────

    def _heuristic_parse(self, soup: BeautifulSoup, journal_url: str) -> list[Paper]:
        """智能解析：寻找重复的卡片/列表模式"""
        # 移除导航、footer、header
        for tag in soup.find_all(["nav", "footer", "header", "aside"]):
            tag.decompose()

        papers = []

        # 查找常见的论文容器
        candidates = []

        # 查找 article 标签
        candidates.extend(soup.find_all("article"))

        # 查找包含标题链接的 li
        for li in soup.find_all("li"):
            h = li.find(["h2", "h3", "h4", "strong"])
            link = li.find("a", href=True)
            if h and link:
                text_len = len(link.get_text(strip=True))
                if text_len > 15:
                    candidates.append(li)

        # 查找 class/id 包含 paper/article/toc/item 的 div
        for div in soup.find_all("div"):
            cls = " ".join(div.get("class", []))
            div_id = div.get("id", "")
            if any(kw in (cls + div_id).lower() for kw in ["paper", "article", "toc-item", "issue-item", "card"]):
                h = div.find(["h2", "h3", "h4"])
                if h:
                    candidates.append(div)

        # 去重（父级包含子级时只保留父级）
        candidates = self._deduplicate(candidates)

        for cand in candidates:
            title, paper_url = self._find_title_link(cand, journal_url)
            if not title or len(title) < 10:
                continue

            authors = self._find_authors(cand)
            abstract = self._find_abstract(cand)
            doi = self._find_doi(cand)
            date = self._find_date(cand)

            papers.append(Paper(
                journal_url=journal_url,
                title=title,
                authors=authors,
                abstract=abstract,
                paper_url=paper_url,
                doi=doi,
                published_date=date,
            ))

        return papers[:50]  # 最多 50 篇

    # ── 辅助方法 ─────────────────────────────────────────

    def _deduplicate(self, elements: list) -> list:
        """移除被其他元素包含的子元素"""
        result = []
        for el in elements:
            is_child = False
            for other in elements:
                if el is not other and other in el.parents if hasattr(el, 'parents') else False:
                    is_child = True
                    break
            if not is_child:
                result.append(el)
        return result

    def _find_title_link(self, element, base_url: str) -> tuple[str, str]:
        """从元素中提取标题和链接"""
        # 优先找 h2/h3 中的链接
        for tag_name in ("h2", "h3", "h4", "strong", "span"):
            for h in element.find_all(tag_name):
                link = h.find("a", href=True)
                if link:
                    title = self.clean_text(link.get_text())
                    href = urljoin(base_url, link["href"])
                    if len(title) > 10:
                        return title, href

        # 降级：找第一个有意义的链接
        links = element.find_all("a", href=True)
        for link in links:
            text = self.clean_text(link.get_text())
            href = urljoin(base_url, link["href"])
            # 跳过导航类链接
            skip = ("home", "about", "login", "subscribe", "search", "next", "prev")
            if text and len(text) > 15 and not any(s in text.lower().split()[:2] for s in skip):
                return text, href

        return "", ""

    def _find_authors(self, element) -> list[str]:
        """查找作者"""
        # 常见模式
        patterns = [
            r'[Cc]lass=["\'].*author.*["\']',
            r'[Ii]temprop=["\']author["\']',
        ]
        author_els = []
        for pattern in patterns:
            author_els.extend(element.find_all(["span", "a", "div"], class_=re.compile(r"author|contrib", re.I)))

        if author_els:
            return list({self.clean_text(a.get_text()) for a in author_els if self.clean_text(a.get_text())})

        # 从文本中匹配 "By ..." 模式
        text = element.get_text(" ", strip=True)
        by_match = re.search(r'(?:By|by)\s+([A-Z][^.,;]+(?:,\s*[A-Z][^.,;]+)*)', text)
        if by_match:
            return [a.strip() for a in by_match.group(1).split(",") if a.strip()]

        return []

    def _find_abstract(self, element) -> str:
        """查找摘要"""
        for cls_pat in ["abstract", "summary", "excerpt", "description", "snippet"]:
            el = element.find(["p", "div", "span"], class_=re.compile(cls_pat, re.I))
            if el:
                text = self.clean_text(el.get_text())
                if len(text) > 30:
                    return text[:2000]
        return ""

    def _find_doi(self, element) -> str:
        """查找 DOI"""
        text = str(element)
        match = re.search(r'10\.\d{4,}/[^\s"\'<>]+', text)
        return match.group(0).rstrip('.,;"\'') if match else ""

    def _find_date(self, element) -> str:
        """查找日期"""
        time_el = element.find("time")
        if time_el:
            return time_el.get("datetime", "") or self.clean_text(time_el.get_text())
        date_el = element.find(["span", "div"], class_=re.compile(r"date|published", re.I))
        if date_el:
            return self.clean_text(date_el.get_text())
        return ""
