import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .prompts import QUERY_ENHANCER_SYSTEM_PROMPT, CLASSIFIER_SYSTEM_PROMPT

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# Pydantic Schemas
# ==========================================

class EnhancedQueries(BaseModel):
    enhanced_query_1: str = Field(description="Enhanced version of the current query. Use the chat summary when available; if absent, enhance using the current query alone.")
    enhanced_query_2: str = Field(description="Another enhanced version of the current query. Use the chat summary when available; if absent, enhance using the current query alone.")

class UserIntent(BaseModel):
    is_ycoin_related: bool = Field(description="True if the user's message is related to Y-Coin.")
    is_general_message: bool = Field(description="True if the user's message is a general/non-Y-Coin message.")

# ==========================================
# Processor Functions
# ==========================================

async def enhance_user_query(
    user_query: str, 
    chat_summary: Optional[str] = None
) -> EnhancedQueries:
    """
    Enhances a user query using the conversation summary for better retrieval.
    Returns fallback queries (the original query) if the API fails.
    """
    if not user_query or not user_query.strip():
        logger.warning("Empty user_query provided. Returning empty enhanced queries.")
        return EnhancedQueries(enhanced_query_1="", enhanced_query_2="")

    try:
        llm = ChatOpenAI(model="gpt-5-nano-2025-08-07", temperature=0.2, max_retries=3, timeout=15.0)
        structured_llm = llm.with_structured_output(EnhancedQueries, method="json_schema")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUERY_ENHANCER_SYSTEM_PROMPT),
            ("user", "Chat Summary: {chat_summary}\n\nUser Query: {user_query}")
        ])
        
        chain = prompt | structured_llm
        safe_summary = chat_summary.strip() if chat_summary else "No previous conversation."
        
        response = chain.invoke({
            "chat_summary": safe_summary,
            "user_query": user_query.strip()
        })
        
        if not response or not isinstance(response, EnhancedQueries):
            logger.error("Received an invalid response type from the structured LLM.")
            raise ValueError("Invalid response structure.")
            
        return response
        
    except Exception as e:
        logger.error(f"Error enhancing query: {e}", exc_info=True)
        safe_fallback = user_query.strip()
        return EnhancedQueries(enhanced_query_1=safe_fallback, enhanced_query_2=safe_fallback)


async def classify_user_intent(
    user_query: str, 
    chat_summary: Optional[str] = None
) -> UserIntent:
    """
    Classifies whether a user's query is about Y-Coin or just a general message.
    Returns a default fallback (general message) if the API fails.
    """
    if not user_query or not user_query.strip():
        logger.warning("Empty user_query provided. Defaulting to general message.")
        return UserIntent(is_ycoin_related=False, is_general_message=True)

    try:
        # Temperature 0.0 for deterministic classification
        llm = ChatOpenAI(model="gpt-5-nano-2025-08-07", temperature=0.0, max_retries=3, timeout=15.0)
        structured_llm = llm.with_structured_output(UserIntent, method="json_schema")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", CLASSIFIER_SYSTEM_PROMPT),
            ("user", "Chat Summary: {chat_summary}\n\nUser Query: {user_query}")
        ])
        
        chain = prompt | structured_llm
        safe_summary = chat_summary.strip() if chat_summary else "No previous conversation."
        
        response = chain.invoke({
            "chat_summary": safe_summary,
            "user_query": user_query.strip()
        })
        
        if not response or not isinstance(response, UserIntent):
            logger.error("Received an invalid response type from the structured LLM.")
            raise ValueError("Invalid response structure.")
            
        return response
        
    except Exception as e:
        logger.error(f"Error classifying user intent: {e}", exc_info=True)
        return UserIntent(is_ycoin_related=False, is_general_message=True)