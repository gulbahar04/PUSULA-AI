
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings


settings = get_settings()


def get_embeddings():
    """EmbeddingGemma modelini Ollama üzerinden kullanır."""
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url
    )


def get_vectorstore():
    """ChromaDB bağlantısını oluşturur."""
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_directory
    )


def get_retriever():
    """ChromaDB üzerinden ilgili dokümanları getirir."""
    vectorstore = get_vectorstore()

    return vectorstore.as_retriever(
        search_kwargs={"k": settings.top_k}
    )


def get_document_records(source_id: str):
    """Belirli bir dokümana ait mevcut kayıtları getirir."""
    store = get_vectorstore()

    return store.get(
        where={"source_id": source_id},
        include=["metadatas"]
    )


def delete_document_records(source_id: str) -> int:
    """Belirli bir dokümana ait parçaları güvenli şekilde siler."""

    store = get_vectorstore()

    # Silinecek kayıtların ID'lerini bul
    records = store.get(
        where={"source_id": source_id},
        include=["metadatas"]
    )

    ids = records["ids"]

    if not ids:
        return 0

    # Yalnızca bulunan ID'leri sil
    store.delete(ids=ids)

    return len(ids)


def add_documents(chunks, ids=None):
    """Doküman parçalarını ChromaDB'ye ekler."""
    store = get_vectorstore()

    if ids is not None:
        return store.add_documents(
            documents=chunks,
            ids=ids
        )

    return store.add_documents(chunks)
