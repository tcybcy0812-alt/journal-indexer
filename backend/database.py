import sqlite3
import json
from datetime import datetime
from typing import Optional
from models import Paper


DB_PATH = "journal_indexer.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_url TEXT NOT NULL,
            title TEXT NOT NULL,
            authors TEXT DEFAULT '[]',
            abstract TEXT DEFAULT '',
            paper_url TEXT DEFAULT '',
            doi TEXT DEFAULT '',
            published_date TEXT DEFAULT '',
            crawled_at TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            crawled_at TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def save_papers(journal_url: str, papers: list[Paper]) -> int:
    """保存论文到数据库，返回保存数量"""
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 记录已爬取的期刊
    conn.execute(
        "INSERT OR REPLACE INTO journals (url, crawled_at) VALUES (?, ?)",
        (journal_url, now)
    )

    saved = 0
    for p in papers:
        # 检查是否已存在（按 DOI 或 URL 去重）
        if p.doi:
            existing = conn.execute(
                "SELECT id FROM papers WHERE doi = ?", (p.doi,)
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id FROM papers WHERE paper_url = ? AND title = ?",
                (p.paper_url, p.title)
            ).fetchone()

        if existing:
            continue

        conn.execute("""
            INSERT INTO papers (journal_url, title, authors, abstract, paper_url, doi, published_date, crawled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            journal_url,
            p.title,
            json.dumps(p.authors, ensure_ascii=False),
            p.abstract,
            p.paper_url,
            p.doi,
            p.published_date,
            now
        ))
        saved += 1

    conn.commit()
    conn.close()
    return saved


def get_papers(journal_url: Optional[str] = None, limit: int = 100, offset: int = 0) -> list[Paper]:
    """获取论文列表"""
    conn = get_db()
    if journal_url:
        rows = conn.execute(
            "SELECT * FROM papers WHERE journal_url = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (journal_url, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM papers ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    conn.close()
    return [_row_to_paper(r) for r in rows]


def get_paper(paper_id: int) -> Optional[Paper]:
    conn = get_db()
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    conn.close()
    return _row_to_paper(row) if row else None


def get_journals() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM journals ORDER BY crawled_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_paper_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()
    return count


def search_papers(query: str, limit: int = 50) -> list[Paper]:
    conn = get_db()
    q = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM papers WHERE title LIKE ? OR abstract LIKE ? ORDER BY id DESC LIMIT ?",
        (q, q, limit)
    ).fetchall()
    conn.close()
    return [_row_to_paper(r) for r in rows]


def _row_to_paper(row) -> Paper:
    d = dict(row)
    try:
        d["authors"] = json.loads(d.get("authors", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["authors"] = []
    return Paper(**d)
