import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

from contextlib import contextmanager


settings = get_settings()


@contextmanager
def get_connection():
    """SQLite bağlantısını güvenli şekilde yönetir."""

    db_path = settings.audit_db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db_path, timeout=30)

    try:
        yield con
        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


def init_db() -> None:
    """Audit ve doküman kayıt tablolarını oluşturur ve günceller."""

    with get_connection() as con:

        # Kullanıcı sorgularının kayıtları
        con.execute("""
            CREATE TABLE IF NOT EXISTS query_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                question TEXT NOT NULL,
                source_used TEXT NOT NULL,
                trace_json TEXT NOT NULL
            )
        """)

        # Doküman kayıtları
        con.execute("""
            CREATE TABLE IF NOT EXISTS document_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                filename_key TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                source_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Mevcut tabloya yeni alanları ekle
        existing_columns = {
            row[1]
            for row in con.execute(
                "PRAGMA table_info(document_registry)"
            ).fetchall()
        }

        new_columns = {
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "deleted_at": "TEXT",
            "deleted_by": "TEXT",
            "original_path": "TEXT",
            "trash_path": "TEXT",
        }

        for column, definition in new_columns.items():
            if column not in existing_columns:
                con.execute(
                    f"ALTER TABLE document_registry "
                    f"ADD COLUMN {column} {definition}"
                )

        # Doküman işlem geçmişi
        con.execute("""
            CREATE TABLE IF NOT EXISTS document_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                original_filename TEXT NOT NULL,
                action TEXT NOT NULL,
                performed_by TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

def write_audit(
    question: str,
    source_used: str,
    trace: list[str]
) -> None:
    """Kullanıcı sorgusunu audit tablosuna kaydeder."""

    with get_connection() as con:
        con.execute(
            """INSERT INTO query_audit(
                created_at, question, source_used, trace_json
            ) VALUES (?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                question,
                source_used,
                json.dumps(trace, ensure_ascii=False),
            ),
        )


def get_document_record(filename: str):
    """Dosya adına göre kayıtlı dokümanı getirir."""

    filename_key = filename.casefold()

    with get_connection() as con:
        con.row_factory = sqlite3.Row

        row = con.execute(
            """SELECT * FROM document_registry
               WHERE filename_key = ?""",
            (filename_key,)
        ).fetchone()

    return dict(row) if row else None


def register_document(
    filename: str,
    file_hash: str,
    source_id: str
) -> None:
    """Başarıyla indekslenen dokümanı kayıt altına alır."""

    filename_key = filename.casefold()

    with get_connection() as con:
        con.execute(
            """INSERT INTO document_registry(
                original_filename,
                filename_key,
                file_hash,
                source_id,
                created_at,
                original_path,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                filename,
                filename_key,
                file_hash,
                source_id,
                datetime.now(timezone.utc).isoformat(),
                source_id,
                "active"
            )
        )

def write_document_history(
    document_id: int,
    filename: str,
    action: str,
    performed_by: str,
    details: dict | None = None
) -> None:
    """Doküman üzerindeki işlemleri geçmişe kaydeder."""

    with get_connection() as con:
        con.execute(
            """INSERT INTO document_history(
                document_id,
                original_filename,
                action,
                performed_by,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                document_id,
                filename,
                action,
                performed_by,
                json.dumps(details or {}, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat()
            )
        )

def get_document_by_id(document_id: int):
    """ID üzerinden doküman kaydını getirir."""

    with get_connection() as con:
        con.row_factory = sqlite3.Row

        row = con.execute(
            """SELECT * FROM document_registry
               WHERE id = ?""",
            (document_id,)
        ).fetchone()

    return dict(row) if row else None

def update_document_status(
    document_id: int,
    status: str,
    deleted_at: str | None = None,
    deleted_by: str | None = None,
    original_path: str | None = None,
    trash_path: str | None = None
) -> None:
    """Dokümanın durum ve silinme bilgilerini günceller."""

    if status not in {"active", "deleted"}:
        raise ValueError("Geçersiz doküman durumu.")

    with get_connection() as con:
        cursor = con.execute(
            """UPDATE document_registry
               SET status = ?,
                   deleted_at = ?,
                   deleted_by = ?,
                   original_path = ?,
                   trash_path = ?
               WHERE id = ?""",
            (
                status,
                deleted_at,
                deleted_by,
                original_path,
                trash_path,
                document_id
            )
        )

        if cursor.rowcount == 0:
            raise ValueError("Doküman kaydı bulunamadı.")

def get_documents_by_status(
    status: str = "active",
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    """Dokümanları durumlarına göre listeler."""

    if status not in {"active", "deleted"}:
        raise ValueError("Geçersiz doküman durumu.")

    if limit < 1 or limit > 500:
        raise ValueError("Limit 1-500 arasında olmalıdır.")

    if offset < 0:
        raise ValueError("Offset negatif olamaz.")

    with get_connection() as con:
        con.row_factory = sqlite3.Row

        rows = con.execute(
            """
            SELECT *
            FROM document_registry
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (status, limit, offset)
        ).fetchall()

    return [dict(row) for row in rows]

def get_document_history(
    document_id: int
) -> list[dict]:
    """Bir dokümanın işlem geçmişini getirir."""

    with get_connection() as con:
        con.row_factory = sqlite3.Row

        rows = con.execute(
            """
            SELECT *
            FROM document_history
            WHERE document_id = ?
            ORDER BY created_at DESC
            """,
            (document_id,)
        ).fetchall()

    history = []

    for row in rows:
        record = dict(row)

        if record["details_json"]:
            try:
                record["details"] = json.loads(
                    record["details_json"]
                )
            except json.JSONDecodeError:
                record["details"] = {}

        else:
            record["details"] = {}

        history.append(record)

    return history

        