import logging
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Standard production practice: set up a module-level logger
logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Splits large texts into smaller chunks for NLP tasks while preserving 
    metadata alignment and enforcing chunk size/overlap constraints.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def create_chunks(
        self, texts: list[str], metadata_list: list[dict[str, Any]] | None = None
    ) -> list[Document]:
        """
        Processes a list of strings into LangChain Document chunks.
        Filters out empty strings and ensures metadata stays aligned.
        """
        if not texts:
            return []

        if metadata_list is not None and len(texts) != len(metadata_list):
            raise ValueError("texts and metadata_list must have the same length.")

        valid_texts = []
        valid_metadatas = []

        # Filter out empty texts. Using zip() ensures metadata stays perfectly 
        # aligned with the texts we keep, in a single fast iteration.
        if metadata_list is not None:
            for text, meta in zip(texts, metadata_list):
                if text.strip():
                    valid_texts.append(text)
                    valid_metadatas.append(meta)
        else:
            for text in texts:
                if text.strip():
                    valid_texts.append(text)
            
            # Explicitly set to None to satisfy LangChain's expected signature
            valid_metadatas = None 

        if not valid_texts:
            return []

        # Isolate the external library call. This makes debugging easier (you can 
        # place a breakpoint on 'return chunks') and prevents unhandled crashes.
        try:
            chunks = self.text_splitter.create_documents(
                texts=valid_texts,
                metadatas=valid_metadatas,
            )
        except Exception as error:
            logger.error("LangChain text splitting failed: %s", error)
            raise RuntimeError("Failed to process the text batch.") from error

        return chunks


if __name__ == "__main__":
    # Basic logging config so we can see any errors if they happen
    logging.basicConfig(level=logging.INFO)

    processor = TextProcessor(chunk_size=100, chunk_overlap=20)

    # Example data with an empty string to prove the filter works
    sample_texts = [
        "This is the first document. " * 20,
        "   ",  # Will be safely ignored
        "This is the second document. " * 20,
    ]

    sample_metadata = [
        {"document_id": 1, "source": "first.txt"},
        {"document_id": 2, "source": "empty.txt"},
        {"document_id": 3, "source": "second.txt"},
    ]

    # Process
    documents = processor.create_chunks(sample_texts, sample_metadata)

    # Output
    for index, doc in enumerate(documents):
        print(f"\n--- Chunk {index} ---")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")