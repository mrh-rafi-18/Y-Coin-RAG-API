import logging
from typing import Generator
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .prompts import CHAT_SUMMARIZER_SYSTEM_PROMPT


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGChat:
    """Manages dynamic context injection, prompt assembly, and standard LLM execution."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.5):
        """Initializes the LLM and the distinct prompt template layouts."""
        try:
            self.model = ChatOpenAI(
                model=model_name, 
                temperature=temperature,
                max_retries=3,
                timeout=30.0
            )
            
            # 1. RAG-specific template and chain (includes context)
            self.rag_template = ChatPromptTemplate.from_messages([
                ("system", "{system_message}"),
                ("system", "Here is the summary of the conversation so far:\n{prev_chat_summary}"),
                ("system", "Use only the following retrieved documents to answer the question:\n{context}"),
                ("user", "{user_query}")
            ])
            self.rag_chain = self.rag_template | self.model

            # 2. Standard chat template and chain (no context)
            self.standard_template = ChatPromptTemplate.from_messages([
                ("system", "{system_message}"),
                ("system", "Here is the summary of the conversation so far:\n{prev_chat_summary}"),
                ("user", "{user_query}")
            ])
            self.standard_chain = self.standard_template | self.model
            
            # 3. Chat summarizer template and chain
            self.summarizer_template = ChatPromptTemplate.from_messages([
                ("system", CHAT_SUMMARIZER_SYSTEM_PROMPT),
                ("user", "Previous Summary: {prev_chat_summary}\n\nNew Query: {current_query}\n\nNew Response: {current_response}")
            ])
            self.summarizer_chain = self.summarizer_template | self.model
            
        except Exception as e:
            logger.error(f"Failed to initialize RAGChat: {e}", exc_info=True)
            raise RuntimeError(f"Initialization error in RAGChat: {e}")

    def stream_rag_response(
        self, 
        system_message: str, 
        prev_chat_summary: str, 
        context: str, 
        user_query: str
    ) -> Generator[str, None, None]:
        """Streams the LLM response using retrieved RAG context."""
        if not user_query or not user_query.strip():
            logger.warning("Empty user_query provided. Skipping LLM call.")
            yield "I didn't receive a question. How can I help you today?"
            return

        try:
            safe_inputs = {
                "system_message": system_message or "You are a helpful assistant.",
                "prev_chat_summary": prev_chat_summary or "No previous conversation.",
                "context": context or "No context provided.",
                "user_query": user_query.strip()
            }
            
            for chunk in self.rag_chain.stream(safe_inputs):
                if chunk and hasattr(chunk, 'content'):
                    yield str(chunk.content)
                    
        except Exception as e:
            logger.error(f"Error streaming RAG response: {e}", exc_info=True)
            yield "\n[Error: I'm sorry, I encountered a network or API error while generating the response.]"

    def stream_standard_response(
        self, 
        system_message: str, 
        prev_chat_summary: str, 
        user_query: str
    ) -> Generator[str, None, None]:
        """Streams the LLM response using only chat history and the user query."""
        if not user_query or not user_query.strip():
            logger.warning("Empty user_query provided. Skipping LLM call.")
            yield "I didn't receive a question. How can I help you today?"
            return

        try:
            safe_inputs = {
                "system_message": system_message or "You are a helpful assistant.",
                "prev_chat_summary": prev_chat_summary or "No previous conversation.",
                "user_query": user_query.strip()
            }
            
            for chunk in self.standard_chain.stream(safe_inputs):
                if chunk and hasattr(chunk, 'content'):
                    yield str(chunk.content)
                    
        except Exception as e:
            logger.error(f"Error streaming standard response: {e}", exc_info=True)
            yield "\n[Error: I'm sorry, I encountered a network or API error while generating the response.]"

    def summarize_chat(
        self, 
        prev_chat_summary: str, 
        current_query: str, 
        current_response: str
    ) -> str:
        """Generates an updated chat summary based on the new interaction."""
        if not current_query.strip() and not current_response.strip():
            logger.warning("Empty query and response provided to summarizer. Returning previous summary.")
            return prev_chat_summary or ""

        try:
            safe_inputs = {
                "prev_chat_summary": prev_chat_summary or "No previous conversation.",
                "current_query": current_query.strip(),
                "current_response": current_response.strip()
            }
            
            # Using .invoke() here because summaries are usually internal state updates, not streamed to the user
            response = self.summarizer_chain.invoke(safe_inputs)
            
            if not response or not hasattr(response, 'content'):
                logger.error("Received an invalid response object from the summarizer LLM.")
                return prev_chat_summary  # Graceful fallback to avoid losing the old summary
                
            return str(response.content)
            
        except Exception as e:
            logger.error(f"Error generating chat summary: {e}", exc_info=True)
            # Fallback to the previous summary so the application state isn't destroyed by a network error
            return prev_chat_summary