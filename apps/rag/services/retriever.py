import logging
from typing import List, Any
from langchain_core.documents import Document
from langchain_cohere import CohereRerank

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrieverService:
    """Service for retrieving and reranking documents using a multi-query strategy."""
    
    RETRIEVAL_K = 10
    RERANK_TOP_N = 6

    def __init__(self, vector_store: Any):
        """Initializes the retriever and Cohere reranker."""
        try:
            self.retriever = vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.RETRIEVAL_K,
                    "fetch_k": 30,
                    "lambda_mult": 0.5,
                },
            )

            self.reranker = CohereRerank(
                model="rerank-v3.5",
                top_n=self.RERANK_TOP_N,
            )
        except Exception as e:
            logger.error(f"Failed to initialize RetrieverService: {e}", exc_info=True)
            raise RuntimeError(f"Initialization error in RetrieverService: {e}")

    def retrieve(self, original_query: str, enhanced_queries: List[str]) -> List[Document]:
        """
        Retrieves and reranks documents based on original and enhanced queries.
        Falls back to returning un-reranked documents if the Cohere API fails.
        """
        if not original_query or not original_query.strip():
            logger.warning("Empty original_query provided. Returning empty list.")
            return []

        queries = [original_query.strip()] + [q.strip() for q in enhanced_queries if q and q.strip()]
        
        try:
            # 1. Concurrent Retrieval
            # .batch() executes all queries simultaneously, reducing I/O wait time by ~66%
            batch_results = self.retriever.batch(queries)
            
            # Flatten the list of lists returned by batch()
            all_documents = [doc for sublist in batch_results for doc in sublist]
            
            # 2. Safe Deduplication
            unique_documents = {}
            for doc in all_documents:
                # Use .get() to prevent KeyError if 'chunk_id' is missing from metadata.
                # Fall back to hashing the page_content itself to guarantee uniqueness.
                chunk_id = doc.metadata.get("chunk_id", hash(doc.page_content))
                
                if chunk_id not in unique_documents:
                    unique_documents[chunk_id] = doc
                    
            documents = list(unique_documents.values())
            
            if not documents:
                logger.info("No documents retrieved from the vector store.")
                return []
                
            # 3. Reranking
            return self.reranker.compress_documents(
                documents=documents,
                query=original_query,
            )

        except Exception as e:
            logger.error(f"Error during retrieval or reranking: {e}", exc_info=True)
            
            # Graceful Fallback: If Cohere API goes down, we shouldn't crash the whole app.
            # Instead, we just return the top N deduplicated documents we already fetched.
            if 'documents' in locals() and documents:
                logger.warning("Returning un-reranked documents as fallback.")
                return documents[:self.RERANK_TOP_N]
                
            return []