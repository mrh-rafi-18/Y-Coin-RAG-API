import os
import time
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config.settings import PINECONE_API_KEY


load_dotenv()


class VectorStoreService:
    def __init__(
        self,
        index_name: str = "y-coin-ai",
        embedding_model: str = "text-embedding-3-small",
        dimension: int = 512,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
        namespace: str | None = None,
    ):
        self.index_name = index_name
        self.dimension = dimension
        self.namespace = namespace

        api_key = PINECONE_API_KEY
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is not set.")

        self.pc = Pinecone(api_key=api_key)

        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=dimension,
        )

        self._ensure_index(metric, cloud, region)

        self.index = self.pc.Index(self.index_name)

        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
            namespace=self.namespace,
        )




    def _ensure_index(self, metric: str, cloud: str, region: str) -> None:
        """Create the Pinecone index if it does not already exist."""

        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=metric,
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            self._wait_for_index()

        index_info = self.pc.describe_index(self.index_name)
        actual_dimension = index_info.dimension

        if actual_dimension != self.dimension:
            raise ValueError(
                f"Pinecone index '{self.index_name}' has dimension "
                f"{actual_dimension}, but the embedding configuration "
                f"requires {self.dimension}."
            )

        

    def _wait_for_index(self, timeout: int = 60, interval: int = 2) -> None:
        """Wait until the Pinecone index becomes ready."""

        start_time = time.time()

        while time.time() - start_time < timeout:
            index_info = self.pc.describe_index(self.index_name)

            if index_info.status["ready"]:
                return

            time.sleep(interval)

        raise TimeoutError(
            f"Pinecone index '{self.index_name}' was not ready "
            f"within {timeout} seconds."
        )



    

    @staticmethod
    def _validate_documents(documents: list[Document]) -> None:
        """Validate documents before sending them to Pinecone."""

        if not isinstance(documents, list):
            raise TypeError("documents must be a list of LangChain Document objects.")

        if not documents:
            raise ValueError("documents cannot be empty.")

        for index, document in enumerate(documents):
            if not isinstance(document, Document):
                raise TypeError(
                    f"documents[{index}] must be a LangChain Document object."
                )

            if not document.page_content.strip():
                raise ValueError(f"documents[{index}] has empty page_content.")

            if not isinstance(document.metadata, dict):
                raise TypeError(
                    f"documents[{index}].metadata must be a dictionary."
                )

            

    def add_documents(self, documents: list[Document], ids: list[str] | None = None) -> list[str]:
        """Embed and store LangChain documents in Pinecone."""

        self._validate_documents(documents)

        if ids is not None:
            if len(ids) != len(documents):
                raise ValueError("The number of IDs must match the number of documents.")

            if any(not isinstance(doc_id, str) or not doc_id.strip() for doc_id in ids):
                raise ValueError("Every document ID must be a non-empty string.")

        try:
            return self.vector_store.add_documents(documents=documents, ids=ids)

        except Exception as exc:
            raise RuntimeError(
                f"Failed to add {len(documents)} document(s) to "
                f"Pinecone index '{self.index_name}'."
            ) from exc


        

    def delete_documents(self, ids: list[str]) -> None:
        """Delete vectors from Pinecone by their IDs."""

        if not ids:
            raise ValueError("ids cannot be empty.")

        if any(not isinstance(doc_id, str) or not doc_id.strip() for doc_id in ids):
            raise ValueError("Every ID must be a non-empty string.")

        try:
            self.vector_store.delete(ids=ids)

        except Exception as exc:
            raise RuntimeError(
                f"Failed to delete documents from Pinecone index "
                f"'{self.index_name}'."
            ) from exc


        

    def similarity_search(self, query: str, k: int = 4, filter: dict[str, Any] | None = None) -> list[Document]:
        """Search for documents semantically similar to the query."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")

        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer.")

        try:
            return self.vector_store.similarity_search(query=query, k=k, filter=filter)

        except Exception as exc:
            raise RuntimeError(
                f"Failed to perform similarity search in "
                f"Pinecone index '{self.index_name}'."
            ) from exc


        

    def similarity_search_with_score(self, query: str, k: int = 4, filter: dict[str, Any] | None = None) -> list[tuple[Document, float]]:
        """Search for similar documents and return their similarity scores."""

        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")

        if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            raise ValueError("k must be a positive integer.")

        try:
            return self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter,
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to perform similarity search with scores in "
                f"Pinecone index '{self.index_name}'."
            ) from exc

    def get_retriever(self, search_kwargs: dict[str, Any] | None = None):
        """Return a LangChain retriever backed by Pinecone."""

        return self.vector_store.as_retriever(
            search_kwargs=search_kwargs or {"k": 4}
        )









if __name__ == "__main__":
    documents = [
        Document(
            page_content="I had chocolate chip pancakes and scrambled eggs for breakfast this morning.",
            metadata={"source": "tweet"},
        ),
        Document(
            page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
            metadata={"source": "news"},
        ),
        Document(
            page_content="Building an exciting new project with LangChain - come check it out!",
            metadata={"source": "tweet"},
        ),
    ]

    vector_service = VectorStoreService()

    ids = vector_service.add_documents(documents)

    print("Inserted IDs:")
    print(ids)

    results = vector_service.similarity_search(
        query="What will the weather be like tomorrow?",
        k=2,
    )

    print("\nSearch results:")
    for result in results:
        print(result.page_content)
        print(result.metadata)

    filtered_results = vector_service.similarity_search(
        query="What will the weather be like tomorrow?",
        k=2,
        filter={"source": {"$eq": "news"}},
    )

    print("\nFiltered search results:")
    for result in filtered_results:
        print(result.page_content)
        print(result.metadata)

    vector_service.delete_documents(ids=[ids[-1]])

    print("\nDeleted:", ids[-1])