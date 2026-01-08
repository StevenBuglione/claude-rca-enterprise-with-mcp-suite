from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import psycopg

from app.evidence.models import EvidenceItem

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evidence (
  run_id TEXT NOT NULL,
  evidence_id TEXT NOT NULL,
  source TEXT NOT NULL,
  locator TEXT NOT NULL,
  content TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (run_id, evidence_id)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_evidence_run_id ON evidence(run_id);
"""

SELECT_COLUMNS = "run_id, evidence_id, source, locator, content, content_sha256, metadata_json, created_at"


def _lock_id(run_id: str) -> int:
    digest = hashlib.sha256(run_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


class EvidenceStore:
    def add(self, *, run_id: str, source: str, locator: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        raise NotImplementedError

    def get(self, *, run_id: str, evidence_id: str) -> EvidenceItem:
        raise NotImplementedError

    def list(self, *, run_id: str) -> List[EvidenceItem]:
        raise NotImplementedError

    def search(self, *, run_id: str, query: str, limit: int = 20) -> List[EvidenceItem]:
        raise NotImplementedError


class PostgresEvidenceStore(EvidenceStore):
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._init_db()

    def _conn(self) -> psycopg.Connection:
        return psycopg.connect(self._dsn)

    def _item_from_row(self, row: Sequence[Any]) -> EvidenceItem:
        run_id, evidence_id, source, locator, content, content_sha256, metadata_json, created_at = row
        return EvidenceItem(
            run_id=run_id,
            evidence_id=evidence_id,
            source=source,
            locator=locator,
            content=content,
            content_sha256=content_sha256,
            metadata=json.loads(metadata_json) if metadata_json else {},
            created_at=created_at,
        )

    def _init_db(self) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                cur.execute(CREATE_INDEX_SQL)

    def add(self, *, run_id: str, source: str, locator: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> EvidenceItem:
        meta = metadata or {}
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        created_at = datetime.now(timezone.utc)
        lock_id = _lock_id(run_id)

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_lock(%s)", (lock_id,))
                try:
                    cur.execute("SELECT COUNT(*) FROM evidence WHERE run_id = %s", (run_id,))
                    row = cur.fetchone()
                    if row is None:
                        raise RuntimeError("Failed to count evidence rows.")
                    n = int(row[0])
                    evidence_id = f"E{n + 1}"

                    cur.execute(
                        "INSERT INTO evidence(run_id,evidence_id,source,locator,content,content_sha256,metadata_json,created_at) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            run_id,
                            evidence_id,
                            source,
                            locator,
                            content,
                            content_sha256,
                            json.dumps(meta, separators=(",", ":")),
                            created_at,
                        ),
                    )
                finally:
                    cur.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))

        return EvidenceItem(
            run_id=run_id,
            evidence_id=evidence_id,
            source=source,
            locator=locator,
            content=content,
            content_sha256=content_sha256,
            metadata=meta,
            created_at=created_at,
        )

    def get(self, *, run_id: str, evidence_id: str) -> EvidenceItem:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {SELECT_COLUMNS} FROM evidence WHERE run_id = %s AND evidence_id = %s",
                    (run_id, evidence_id),
                )
                row = cur.fetchone()
        if not row:
            raise KeyError(f"Evidence not found: {run_id=} {evidence_id=}")
        return self._item_from_row(row)

    def list(self, *, run_id: str) -> List[EvidenceItem]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {SELECT_COLUMNS} FROM evidence WHERE run_id = %s ORDER BY CAST(SUBSTRING(evidence_id FROM 2) AS INT) ASC",
                    (run_id,),
                )
                rows = cur.fetchall()
        return [self._item_from_row(row) for row in rows]

    def search(self, *, run_id: str, query: str, limit: int = 20) -> List[EvidenceItem]:
        q = f"%{query}%"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {SELECT_COLUMNS} FROM evidence WHERE run_id = %s AND (content ILIKE %s OR locator ILIKE %s) LIMIT %s",
                    (run_id, q, q, limit),
                )
                rows = cur.fetchall()
        return [self._item_from_row(row) for row in rows]


def build_evidence_store(store_url: str) -> EvidenceStore:
    if store_url.startswith(("postgresql://", "postgres://")):
        return PostgresEvidenceStore(store_url)
    raise RuntimeError(f"Unsupported EVIDENCE_STORE_URL: {store_url}. Use a postgres URL.")
