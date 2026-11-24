
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.services.audit import get_document_by_id, get_connection
from app.services.ingestion import reindex_file, calculate_file_hash
from app.rag.vectorstore import (
    delete_document_records,
    get_document_records
)
import uuid

settings = get_settings()


def soft_delete_document(
    document_id: int,
    performed_by: str = "admin"
) -> dict:
    """Dokümanı çöp kutusuna taşır ve ChromaDB kayıtlarını kaldırır."""

    document = get_document_by_id(document_id)

    if document is None:
        raise ValueError("Doküman bulunamadı.")

    if document["status"] != "active":
        raise ValueError("Doküman zaten silinmiş.")

    original_path = Path(
        document["original_path"] or document["source_id"]
    )

    if not original_path.is_file():
        raise FileNotFoundError(
            f"Doküman dosyası bulunamadı: {original_path}"
        )

    trash_dir = Path(settings.trash_dir)
    trash_dir.mkdir(parents=True, exist_ok=True)

    trash_path = trash_dir / (
        f"{document_id}_{document['original_filename']}"
    )

    if trash_path.exists():
        raise FileExistsError(
            "Çöp kutusunda aynı hedef dosya zaten mevcut."
        )

    source_id = document["source_id"]
    deleted_at = datetime.now(timezone.utc).isoformat()

    file_moved = False
    deletion_started = False

    try:
        # 1. Dosyayı çöp kutusuna taşı
        shutil.move(str(original_path), str(trash_path))
        file_moved = True

        # 2. ChromaDB kayıtlarını kaldır
        deletion_started = True
        deleted_count = delete_document_records(source_id)

        # 3. SQLite durumunu ve geçmişi birlikte güncelle
        with get_connection() as con:
            con.execute(
                """
                UPDATE document_registry
                SET status = 'deleted',
                    deleted_at = ?,
                    deleted_by = ?,
                    original_path = ?,
                    trash_path = ?
                WHERE id = ?
                """,
                (
                    deleted_at,
                    performed_by,
                    str(original_path),
                    str(trash_path),
                    document_id
                )
            )

            con.execute(
                """
                INSERT INTO document_history(
                    document_id,
                    original_filename,
                    action,
                    performed_by,
                    details_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    document["original_filename"],
                    "DELETE",
                    performed_by,
                    json.dumps(
                        {"chunks_deleted": deleted_count},
                        ensure_ascii=False
                    ),
                    deleted_at
                )
            )

        return {
            "success": True,
            "document_id": document_id,
            "filename": document["original_filename"],
            "chunks_deleted": deleted_count,
            "status": "deleted"
        }

    except Exception as exc:
        # Hata durumunda mümkün olduğunca eski duruma dön
        try:
            if deletion_started:
                # Kısmi silme ihtimalini kontrol et
                remaining = get_document_records(source_id)

                if remaining["ids"]:
                    delete_document_records(source_id)

                # Orijinal embedding kayıtlarını yeniden oluştur
                recovery_path = (
                    trash_path if trash_path.exists()
                    else original_path
                )

                reindex_file(recovery_path, source_id)

            if file_moved and trash_path.exists():
                shutil.move(str(trash_path), str(original_path))

        except Exception as recovery_error:
            raise RuntimeError(
                "Silme işlemi başarısız oldu ve otomatik "
                f"kurtarma tamamlanamadı. Dosya: {trash_path}. "
                f"Kurtarma hatası: {recovery_error}"
            ) from exc

        raise RuntimeError(
            f"Doküman silinemedi: {exc}"
        ) from exc


def restore_document(
    document_id: int,
    performed_by: str = "admin"
) -> dict:
    """Silinmiş dokümanı yeniden indeksleyerek geri yükler."""

    document = get_document_by_id(document_id)

    if document is None:
        raise ValueError("Doküman bulunamadı.")

    if document["status"] != "deleted":
        raise ValueError("Doküman zaten aktif.")

    trash_path = Path(document["trash_path"])
    original_path = Path(document["original_path"])
    source_id = document["source_id"]

    if not trash_path.is_file():
        raise FileNotFoundError(
            f"Çöp kutusu dosyası bulunamadı: {trash_path}"
        )

    if original_path.exists():
        raise FileExistsError(
            f"Orijinal konumda başka bir dosya mevcut: {original_path}"
        )

    # Dosyanın değiştirilmediğini doğrula
    current_hash = calculate_file_hash(trash_path)

    if current_hash != document["file_hash"]:
        raise ValueError(
            "Dosyanın içeriği değişmiş. Geri yükleme durduruldu."
        )

    # Beklenmeyen mevcut embedding kayıtlarını koru
    existing_records = get_document_records(source_id)

    if existing_records["ids"]:
        raise ValueError(
            "Geri yükleme öncesinde ChromaDB'de mevcut kayıt bulundu."
        )

    indexing_started = False
    file_moved = False

    try:
        # 1. Dosyayı yeniden indeksle
        indexing_started = True
        chunks_count = reindex_file(trash_path, source_id)

        # 2. Dosyayı eski konumuna taşı
        original_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(trash_path), str(original_path))
        file_moved = True

        restored_at = datetime.now(timezone.utc).isoformat()

        # 3. SQLite durumunu ve geçmişi birlikte güncelle
        with get_connection() as con:
            con.execute(
                """
                UPDATE document_registry
                SET status = 'active',
                    deleted_at = NULL,
                    deleted_by = NULL,
                    trash_path = NULL
                WHERE id = ?
                """,
                (document_id,)
            )

            con.execute(
                """
                INSERT INTO document_history(
                    document_id,
                    original_filename,
                    action,
                    performed_by,
                    details_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    document["original_filename"],
                    "RESTORE",
                    performed_by,
                    json.dumps(
                        {"chunks_created": chunks_count},
                        ensure_ascii=False
                    ),
                    restored_at
                )
            )

        return {
            "success": True,
            "document_id": document_id,
            "filename": document["original_filename"],
            "chunks_created": chunks_count,
            "status": "active"
        }

    except Exception as exc:
        # Başarısız geri yüklemede yeni embedding kayıtlarını temizle
        try:
            if indexing_started:
                delete_document_records(source_id)

            if file_moved and original_path.exists():
                shutil.move(str(original_path), str(trash_path))

        except Exception as recovery_error:
            raise RuntimeError(
                "Geri yükleme başarısız oldu ve otomatik "
                f"kurtarma tamamlanamadı. Dosya: {trash_path}. "
                f"Kurtarma hatası: {recovery_error}"
            ) from exc

        raise RuntimeError(
            f"Doküman geri yüklenemedi: {exc}"
        ) from exc

def permanent_delete_document(
    document_id: int,
    performed_by: str = "admin"
) -> dict:
    """Dokümanı tüm sistemlerden kalıcı olarak siler."""

    document = get_document_by_id(document_id)

    if document is None:
        raise ValueError("Doküman bulunamadı.")

    if document["status"] != "deleted":
        raise ValueError(
            "Kalıcı silme için doküman önce çöp kutusuna taşınmalıdır."
        )

    trash_path = Path(document["trash_path"])
    source_id = document["source_id"]

    if not trash_path.is_file():
        raise FileNotFoundError(
            f"Çöp kutusu dosyası bulunamadı: {trash_path}"
        )

    # Dosyayı geçici konuma taşı
    temporary_path = trash_path.with_name(
        f".{trash_path.name}.{uuid.uuid4().hex}.purge"
    )

    file_moved = False
    vectors_deleted = False

    try:
        shutil.move(str(trash_path), str(temporary_path))
        file_moved = True

        # ChromaDB kayıtlarını temizle
        deleted_count = delete_document_records(source_id)
        vectors_deleted = True

        # SQLite kayıtlarını transaction içerisinde sil
        with get_connection() as con:
            con.execute(
                """
                DELETE FROM document_history
                WHERE document_id = ?
                """,
                (document_id,)
            )

            cursor = con.execute(
                """
                DELETE FROM document_registry
                WHERE id = ? AND status = 'deleted'
                """,
                (document_id,)
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Doküman veritabanından silinemedi."
                )

        # Son aşamada fiziksel dosyayı sil
        temporary_path.unlink()

        return {
            "success": True,
            "document_id": document_id,
            "filename": document["original_filename"],
            "chunks_deleted": deleted_count,
            "status": "permanently_deleted"
        }

    except Exception as exc:
        # Hata durumunda kurtarma
        try:
            if vectors_deleted:
                if temporary_path.exists():
                    reindex_file(temporary_path, source_id)

            if file_moved and temporary_path.exists():
                shutil.move(
                    str(temporary_path),
                    str(trash_path)
                )

        except Exception as recovery_error:
            raise RuntimeError(
                "Kalıcı silme başarısız oldu ve otomatik "
                f"kurtarma tamamlanamadı. Dosya: {temporary_path}. "
                f"Kurtarma hatası: {recovery_error}"
            ) from exc

        raise RuntimeError(
            f"Kalıcı silme başarısız: {exc}"
        ) from exc
