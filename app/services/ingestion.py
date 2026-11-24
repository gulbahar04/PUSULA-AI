
import hashlib
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from docx import Document as DocxDocument

from app.rag.vectorstore import (
    get_document_records,
    delete_document_records,
    add_documents
)


SUPPORTED = {".pdf", ".txt", ".md", ".docx"}


def calculate_file_hash(path: Path) -> str:
    """Dosya içeriğinin SHA-256 hash değerini hesaplar."""
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(8192), b""):
            sha256.update(block)

    return sha256.hexdigest()


def load_file(path: Path) -> list[Document]:
    """Desteklenen dosya türlerini yükler."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return PyPDFLoader(str(path)).load()

    if suffix in {".txt", ".md"}:
        return TextLoader(
            str(path),
            encoding="utf-8"
        ).load()

    if suffix == ".docx":
        doc = DocxDocument(str(path))

        text = "\n".join(
            p.text for p in doc.paragraphs
            if p.text.strip()
        )

        return [
            Document(
                page_content=text,
                metadata={"source": str(path)}
            )
        ]

    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_documents(
    docs: Iterable[Document]
) -> list[Document]:
    """Dokümanları küçük parçalara ayırır."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        add_start_index=True
    )

    return splitter.split_documents(list(docs))


def ingest_file(path: Path) -> int:
    """
    Dosyayı yükler, parçalara ayırır ve ChromaDB'ye kaydeder.
    Aynı dosyanın tekrar yüklenmesini kontrol eder.
    """

    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Desteklenmeyen dosya: {path.suffix}")

    file_hash = calculate_file_hash(path)
    source_id = str(path.resolve())

    # Mevcut doküman kayıtlarını kontrol et
    existing = get_document_records(source_id)

    # İçerik değişmemişse tekrar embedding oluşturma
    if existing["metadatas"]:
        existing_hash = existing["metadatas"][0].get("file_hash")

        if existing_hash == file_hash:
            return 0

    # Dosyayı oku ve parçala
    docs = load_file(path)
    chunks = chunk_documents(docs)

    if not chunks:
        return 0

    # Yeni metadata ve benzersiz ID oluştur
    ids = []

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = str(path)
        chunk.metadata["source_id"] = source_id
        chunk.metadata["file_hash"] = file_hash
        chunk.metadata["chunk_index"] = index

        chunk_id = hashlib.sha256(
            f"{source_id}:{index}".encode("utf-8")
        ).hexdigest()

        ids.append(chunk_id)

    # Eski kayıtları sil ve yeni parçaları ekle
    if existing["ids"]:
        delete_document_records(source_id)

    add_documents(chunks, ids=ids)

    return len(chunks)


def reindex_file(path: Path, source_id: str) -> int:
    """
    Çöp kutusundan geri yüklenen dosyayı yeniden indeksler.
    Orijinal source_id değerini korur.
    """

    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Desteklenmeyen dosya: {path.suffix}")

    # Aynı dokümanın zaten indekslenip indekslenmediğini kontrol et
    existing = get_document_records(source_id)

    if existing["ids"]:
        raise ValueError(
            "Bu doküman zaten ChromaDB içerisinde indekslenmiş."
        )

    # Dosyayı oku ve parçalara ayır
    file_hash = calculate_file_hash(path)
    docs = load_file(path)
    chunks = chunk_documents(docs)

    if not chunks:
        raise ValueError("Dosyadan indekslenebilir metin çıkarılamadı.")

    ids = []

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = source_id
        chunk.metadata["source_id"] = source_id
        chunk.metadata["file_hash"] = file_hash
        chunk.metadata["chunk_index"] = index

        chunk_id = hashlib.sha256(
            f"{source_id}:{index}".encode("utf-8")
        ).hexdigest()

        ids.append(chunk_id)

    # Yeni embedding kayıtlarını oluştur
    add_documents(chunks, ids=ids)

    # Eklenen kayıt sayısını doğrula
    result = get_document_records(source_id)

    if len(result["ids"]) != len(chunks):
        raise RuntimeError(
            "ChromaDB indeksleme doğrulaması başarısız."
        )

    return len(chunks)
