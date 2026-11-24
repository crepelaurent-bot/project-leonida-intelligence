import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS http_cache (
  url TEXT PRIMARY KEY, etag TEXT, last_modified TEXT, body TEXT, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS repo_state (
  repo TEXT NOT NULL, branch TEXT NOT NULL, last_sha TEXT,
  checked_at TEXT NOT NULL, PRIMARY KEY(repo, branch)
);
CREATE TABLE IF NOT EXISTS events (
  event_key TEXT PRIMARY KEY, repo TEXT NOT NULL, kind TEXT NOT NULL,
  priority TEXT NOT NULL, confidence TEXT NOT NULL, created_at TEXT NOT NULL,
  title TEXT NOT NULL, summary TEXT NOT NULL, url TEXT NOT NULL,
  payload TEXT NOT NULL, report_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_repo ON events(repo);
"""

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def cached(self, url):
        row = self.db.execute("SELECT * FROM http_cache WHERE url=?", (url,)).fetchone()
        return dict(row) if row else None

    def save_cache(self, url, etag, last_modified, body):
        self.db.execute("""INSERT INTO http_cache(url,etag,last_modified,body,updated_at)
          VALUES(?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET etag=excluded.etag,
          last_modified=excluded.last_modified,body=excluded.body,updated_at=excluded.updated_at""",
          (url, etag, last_modified, body, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def has_event(self, key):
        return self.db.execute("SELECT 1 FROM events WHERE event_key=?", (key,)).fetchone() is not None

    def add_event(self, event):
        cur = self.db.execute("""INSERT OR IGNORE INTO events
          (event_key,repo,kind,priority,confidence,created_at,title,summary,url,payload)
          VALUES(?,?,?,?,?,?,?,?,?,?)""",
          (event["event_key"], event["repo"], event["kind"], event["priority"],
           event["confidence"], event["created_at"], event["title"], event["summary"],
           event["url"], json.dumps(event, ensure_ascii=False)))
        self.db.commit()
        return cur.rowcount == 1

    def set_cursor(self, repo, branch, sha):
        self.db.execute("""INSERT INTO repo_state(repo,branch,last_sha,checked_at)
          VALUES(?,?,?,?) ON CONFLICT(repo,branch) DO UPDATE SET
          last_sha=excluded.last_sha,checked_at=excluded.checked_at""",
          (repo, branch, sha, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def get_cursor(self, repo, branch):
        row = self.db.execute("SELECT last_sha FROM repo_state WHERE repo=? AND branch=?", (repo, branch)).fetchone()
        return row["last_sha"] if row else None

    def events_between(self, start_iso, end_iso):
        rows = self.db.execute("""SELECT payload FROM events WHERE created_at>=? AND created_at<?
          ORDER BY created_at ASC,event_key ASC""", (start_iso, end_iso)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def all_events(self):
        rows = self.db.execute("SELECT payload FROM events ORDER BY created_at,event_key").fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def close(self):
        self.db.close()
