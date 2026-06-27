from abc import ABC, abstractmethod
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from models import Paper

# 优先使用 curl_cffi（模拟浏览器 TLS 指纹，绕过反爬）
try:
    from curl_cffi import requests as req_lib
    IMPERSONATE = "chrome131"
    USE_CURL_CFFI = True
except ImportError:
    import requests as req_lib
    USE_CURL_CFFI = False


class BaseCrawler(ABC):
    """爬虫基类，自动使用 TLS 指纹模拟绕过反爬"""

    def __init__(self):
        if USE_CURL_CFFI:
            self.session = req_lib.Session()
        else:
            self.session = req_lib.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        })
        self._warmup = False

    def _ensure_warmup(self, url: str):
        """首次访问前预热，获取 cookie"""
        if self._warmup:
            return
        try:
            parsed = urlparse(url)
            home = f"{parsed.scheme}://{parsed.netloc}"
            self._get(home)
        except Exception:
            pass
        self._warmup = True

    def _get(self, url: str) -> str:
        """发起 GET 请求，返回 HTML"""
        if USE_CURL_CFFI:
            resp = self.session.get(url, impersonate=IMPERSONATE, timeout=30)
        else:
            resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        enc = getattr(resp, 'apparent_encoding', None) or getattr(resp, 'charset_encoding', None) or "utf-8"
        resp.encoding = enc
        return resp.text

    def fetch(self, url: str) -> str:
        """抓取页面 HTML"""
        self._ensure_warmup(url)
        return self._get(url)

    def fetch_soup(self, url: str) -> BeautifulSoup:
        """抓取页面并返回 BeautifulSoup"""
        html = self.fetch(url)
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    def crawl(self, url: str) -> list[Paper]:
        """爬取期刊页面，返回论文列表"""
        ...

    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        return " ".join(text.strip().split())
