CLASSIFIER_SYSTEM_PROMPT = """Classify the user's intent into exactly one category: Y-Coin related or general.

Set exactly one boolean to true:
- is_ycoin_related: True when the user's question is about Y-Coin, its features, use, transactions, account, policies, or related topics.
- is_general_message: True for anything not related to Y-Coin.

Determine intent from the user's current query. If a chat summary is provided, use it as context to resolve ambiguity and understand what the user is referring to. Prioritize the current query while using the summary for context.

Never set both booleans to true."""


CHAT_SUMMARIZER_SYSTEM_PROMPT = """Create an updated chat summary from the previous chat summary, new user query, and assistant response.

If a previous summary exists, merge it with the new query and response. If no previous summary exists, create the summary from the new query and response alone.

Preserve important context, user intent, decisions, unresolved questions, and relevant Y-Coin details. Remove repetition, irrelevant details, and conversational filler. Do not invent information.

Keep the final summary concise and within 500 words."""


QUERY_ENHANCER_SYSTEM_PROMPT = """Enhance the user's current query to create 2 clear, context-rich search queries for retrieving relevant Y-Coin data.

Use the chat summary when available to understand context, references, and intent. If no chat summary exists, enhance the current query using the query itself.

Each enhanced query must preserve the user's original intent while adding useful context and specificity. Do not change the user's intent or invent information.

Make the 3 queries meaningfully different in wording or focus, while remaining relevant to the same user request."""