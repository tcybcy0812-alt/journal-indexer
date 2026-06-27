from crawler.base import BaseCrawler
from crawler.generic import GenericCrawler
from crawler.science import ScienceCrawler
from crawler.nature import NatureCrawler
from crawler.arxiv import ArxivCrawler


def get_crawler(url: str) -> BaseCrawler:
    """根据 URL 自动选择合适的爬虫"""
    if "science.org" in url:
        return ScienceCrawler()
    if "nature.com" in url:
        return NatureCrawler()
    if "arxiv.org" in url:
        return ArxivCrawler()
    return GenericCrawler()
