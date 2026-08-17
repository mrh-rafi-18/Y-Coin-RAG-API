from threading import Lock

from .vector_store import VectorStoreService
from .rag_chat_engine import RAGChat
from .chunker import TextProcessor
from .retriever import RetrieverService


_vector_store = None
_retriever = None
_chat = None
_chunker = None

_vector_store_lock = Lock()
_retriever_lock = Lock()
_chat_lock = Lock()
_chunker_lock = Lock()


def get_vector_store():
    global _vector_store

    if _vector_store is None:
        with _vector_store_lock:
            if _vector_store is None:
                _vector_store = VectorStoreService()

    return _vector_store


def get_retriever():
    global _retriever

    if _retriever is None:
        with _retriever_lock:
            if _retriever is None:
                _retriever = RetrieverService(get_vector_store().vector_store)

    return _retriever


def get_chat():
    global _chat

    if _chat is None:
        with _chat_lock:
            if _chat is None:
                _chat = RAGChat()

    return _chat


def get_chunker():
    global _chunker

    if _chunker is None:
        with _chunker_lock:
            if _chunker is None:
                _chunker = TextProcessor()

    return _chunker