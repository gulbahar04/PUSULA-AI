
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.rag.workflow import ask

from app.services.ingestion import (
    ingest_file,
    calculate_file_hash,
    SUPPORTED
)

from app.services.audit import (
    write_audit,
    get_document_record,
    register_document,
    get_documents_by_status,
    get_document_history
)
import hashlib

from app.services.document_management import (
    soft_delete_document,
    restore_document,
    permanent_delete_document
)


router = APIRouter(prefix="/api")
settings = get_settings()


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name
    }



@router.post("/chat")
def chat(payload: ChatRequest):
    try:
        question = payload.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Lütfen geçerli bir soru girin."
            )

        result = ask(question)

        write_audit(
            question,
            result["source_used"],
            result.get("trace", [])
        )

        return {
            "answer": result["answer"],
            "source_used": result["source_used"],
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get(
                "current_query",
                question
            )
        }

    except HTTPException:
        raise

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            "Chat endpoint error"
        )

        raise HTTPException(
            status_code=500,
            detail="Yanıt oluşturulurken beklenmeyen bir hata oluştu."
        ) from exc


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    x_admin_key: str = Header(default="")
):
    # 1. Yönetici anahtarı kontrolü
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    # 2. Dosya adı ve uzantı kontrolü
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Dosya adı bulunamadı"
        )

    filename = Path(file.filename).name
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenen dosya türleri: {', '.join(sorted(SUPPORTED))}"
        )

    # 3. Dosya içeriğini oku
    content = await file.read()

    if not content or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Yüklenen dosya boş."
        )

    incoming_hash = hashlib.sha256(content).hexdigest()

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest = upload_dir / filename

    try:
        # 4. SQLite üzerinden dosya adı kontrolü
        existing_record = get_document_record(filename)

        if existing_record:
            if existing_record["file_hash"] == incoming_hash:
                return {
                    "message": "Doküman zaten kayıtlı ve güncel.",
                    "file": filename,
                    "chunks": 0,
                    "ids_created": 0
                }

            raise HTTPException(
                status_code=409,
                detail=(
                    "Bu isimde farklı içerikli bir dosya zaten mevcut. "
                    "Lütfen dosyanın adını değiştirerek tekrar yükleyin."
                )
            )

        # 5. Eski yüklemeler için geriye dönük kontrol
        if dest.exists():
            existing_hash = calculate_file_hash(dest)

            if existing_hash == incoming_hash:
                register_document(
                    filename,
                    incoming_hash,
                    str(dest.resolve())
                )

                return {
                    "message": "Doküman zaten kayıtlı ve güncel.",
                    "file": filename,
                    "chunks": 0,
                    "ids_created": 0
                }

            raise HTTPException(
                status_code=409,
                detail=(
                    "Bu isimde farklı içerikli bir dosya zaten mevcut. "
                    "Lütfen dosyanın adını değiştirerek tekrar yükleyin."
                )
            )

        # 6. Yeni dosyayı kaydet ve indeksle
        dest.write_bytes(content)

        chunks_count = ingest_file(dest)

        if chunks_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Dosyadan indekslenebilir metin çıkarılamadı."
            )

        # 7. Başarılı indeksleme sonrası SQLite'a kaydet
        register_document(
            filename,
            incoming_hash,
            str(dest.resolve())
        )

        return {
            "message": "Doküman başarıyla indekslendi.",
            "file": filename,
            "chunks": chunks_count,
            "ids_created": chunks_count
        }

    except HTTPException:
        raise

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            "Document ingestion error"
        )

        # Yeni dosya başarısız olduysa yüklenen dosyayı temizle
        if dest.exists() and not get_document_record(filename):
            dest.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Doküman işlenirken beklenmeyen bir hata oluştu."
        ) from exc

    finally:
        await file.close()

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    x_admin_key: str = Header(default="")
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    try:
        return soft_delete_document(
            document_id=document_id,
            performed_by="admin"
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@router.post("/documents/{document_id}/restore")
def restore_document_endpoint(
    document_id: int,
    x_admin_key: str = Header(default="")
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    try:
        return restore_document(
            document_id=document_id,
            performed_by="admin"
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@router.get("/documents")
def list_documents(
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
    x_admin_key: str = Header(default="")
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    try:
        documents = get_documents_by_status(
            status=status,
            limit=limit,
            offset=offset
        )

        return {
            "count": len(documents),
            "documents": documents
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/documents/{document_id}/history")
def document_history(
    document_id: int,
    x_admin_key: str = Header(default="")
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    history = get_document_history(document_id)

    return {
        "document_id": document_id,
        "count": len(history),
        "history": history
    }

@router.delete("/documents/{document_id}/permanent")
def permanent_delete(
    document_id: int,
    confirm: bool = False,
    x_admin_key: str = Header(default="")
):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Geçersiz yönetici anahtarı"
        )

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Kalıcı silme için confirm=true gönderilmelidir."
        )

    try:
        return permanent_delete_document(
            document_id=document_id,
            performed_by="admin"
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Permanent delete endpoint error"
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc




