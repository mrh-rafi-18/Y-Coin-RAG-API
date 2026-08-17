import logging
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your modules
from .instances import get_chunker, get_vector_store, get_retriever, get_chat
from .query_processor import classify_user_intent, enhance_user_query

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def setup_ycoin_knowledge_base() -> None:
    """
    Step 1 & 2: Generate long, detailed dummy documents about Y-Coin, 
    chunk them using the Chunker service, and store them in the Vector Store.
    """
    logger.info("--- Step 1: Initializing Chunker and Vector Store ---")
    chunker = get_chunker()
    vector_store_service = get_vector_store()

    # Create long, highly specific dummy texts about Y-Coin
    ycoin_raw_documents = [
        """
        Y-Coin is a next-generation decentralized cryptocurrency built on an advanced proof-of-stake (PoS) 
        consensus mechanism designed specifically for fast, eco-friendly global transactions. Unlike legacy 
        blockchains that consume vast amounts of electricity, Y-Coin utilizes an optimized validation protocol 
        that reduces energy consumption by over 99 percent. The native token, YCOIN, powers the entire ecosystem, 
        serving as the primary medium of exchange, governance token, and staking asset. Launched in early 2025, 
        the network features sub-second transaction finality, making it ideal for micro-transactions, retail checkout 
        integrations, and enterprise-grade cross-border settlements. Security is enforced through cryptographic zero-knowledge 
        proofs, ensuring complete user privacy while maintaining regulatory compliance through optional compliance view-keys.
        """,
        """
        Staking rewards and tokenomics form the backbone of the Y-Coin economic model. Holders of YCOIN can lock 
        their assets into the official network staking contract to secure the blockchain and earn passive yield. 
        The current annual percentage yield (APY) ranges dynamically between 4.5 percent and 7.2 percent, depending 
        upon the total circulating supply locked in the staking pool. Rewards are distributed automatically every 24 hours 
        directly to the staker's self-custody wallet. Furthermore, Y-Coin implements a deflationary burn mechanism: 
        exactly 30 percent of all network transaction fees are permanently burned on a weekly basis, steadily reducing 
        the total max supply from 1 billion tokens over a projected 10-year deflationary cycle. Governance participation 
        requires a minimum lock-up of 500 YCOIN, granting holders voting rights on protocol upgrades, fee adjustments, 
        and treasury grant allocations.
        """,
        """
        Transaction fees and network economics on the Y-Coin blockchain are engineered to remain predictably low, 
        protecting users from the volatile gas price spikes common on older networks. The standard base fee for a 
        standard peer-to-peer wallet transfer is fixed at 0.0005 YCOIN, regardless of network congestion, because 
        of the network's dynamic block-sizing architecture. For smart contract interactions and decentralized application 
        (dApp) deployments, gas computations use an optimized virtual machine bytecode interpreter that slashes execution 
        overhead. Developers building on Y-Coin benefit from comprehensive software development kits (SDKs) available 
        in Python, JavaScript, and Rust, alongside native support for cross-chain bridges connecting Y-Coin to Ethereum, 
        Solana, and Arbitrum ecosystems seamlessly.
        """,
        """
        The security model of the Y-Coin network relies on a robust distributed network of validator nodes operating 
        under a modified Byzantine Fault Tolerance (mBFT) algorithm. To become an active validator, an entity must 
        stake a minimum of 50,000 YCOIN in a verifiable smart contract and maintain a server uptime of at least 99.9 
        percent. To prevent malicious behavior, the network employs a strict slashing condition: any validator attempting 
        to double-sign a block, censor transactions, or manipulate block timestamps will instantly lose up to 50 percent 
        of their staked tokens, which are redistributed to honest nodes. Hardware requirements for running a validator 
        are surprisingly lightweight compared to historical networks, requiring only a quad-core processor, 16 gigabytes 
        of RAM, and a high-speed solid-state drive (SSD) to handle the rapid block generation time of 800 milliseconds.
        """,
        """
        To bridge the gap between digital assets and traditional finance, the Y-Coin Foundation recently launched the 
        Y-Pay Merchant API, a seamless payment gateway that integrates directly into major e-commerce platforms like 
        Shopify, WooCommerce, and Magento. When a customer selects Y-Coin at checkout, the merchant has the option 
        to instantly convert the received YCOIN into fiat currency (such as USD or EUR) through liquidity partners, 
        eliminating volatility risk. Alternatively, merchants holding YCOIN receive a 2 percent cashback incentive 
        on all wholesale supply chain orders placed within the Y-Network. In conjunction with software APIs, the foundation 
        has deployed over 5,000 physical Point of Sale (POS) terminals across Europe and Southeast Asia, enabling 
        contactless NFC payments directly from decentralized mobile wallets.
        """,
        """
        The Decentralized Finance (DeFi) ecosystem native to Y-Coin is experiencing rapid growth, spearheaded by the 
        deployment of Y-Swap, an automated market maker (AMM) that facilitates instant, permissionless token exchanges. 
        Liquidity providers (LPs) on Y-Swap can deposit paired assets—such as YCOIN and bridged stablecoins—into smart 
        contracts to earn a proportional share of the 0.3 percent trading fee generated by the protocol. Because of 
        Y-Coin's sub-second finality, arbitrageurs can effectively synchronize prices across multiple decentralized 
        exchanges without the risk of front-running or Maximum Extractable Value (MEV) attacks, which are systematically 
        mitigated by encrypted mempools. The upcoming network upgrade, dubbed 'Epoch 2', will introduce native lending 
        and borrowing protocols, allowing users to use staked YCOIN as collateral for zero-interest overcollateralized loans.
        """
    ]

    # Corresponding metadata ensuring alignment
    ycoin_metadata_list = [
        {"document_id": "doc_001", "topic": "overview_and_consensus", "source": "ycoin_whitepaper_v1.pdf"},
        {"document_id": "doc_002", "topic": "staking_and_tokenomics", "source": "ycoin_tokenomics_spec.pdf"},
        {"document_id": "doc_003", "topic": "fees_and_developer_sdk", "source": "ycoin_developer_docs.pdf"},
        {"document_id": "doc_004", "topic": "validator_nodes_and_security", "source": "ycoin_node_operator_manual.pdf"},
        {"document_id": "doc_005", "topic": "merchant_adoption_and_payments", "source": "ycoin_integration_guide.pdf"},
        {"document_id": "doc_006", "topic": "defi_and_liquidity", "source": "ycoin_defi_landscape.pdf"},
    ]

    logger.info("--- Step 2: Processing texts through the Chunker ---")
    # This invokes your chunker.py logic with chunk size constraints
    langchain_documents = chunker.create_chunks(
        texts=ycoin_raw_documents, 
        metadata_list=ycoin_metadata_list
    )
    logger.info(f"Successfully split raw texts into {len(langchain_documents)} individual chunks.")

    logger.info("--- Step 3: Upserting chunks into Pinecone Vector Store ---")
    # Custom chunk IDs to guarantee clean tracking
    chunk_ids = [f"ycoin_chunk_{i}" for i in range(len(langchain_documents))]
    
    # Inject chunk_id into metadata so the retriever's dedup logic handles them safely
    for idx, doc in enumerate(langchain_documents):
        doc.metadata["chunk_id"] = chunk_ids[idx]

    vector_store_service.add_documents(documents=langchain_documents, ids=chunk_ids)
    logger.info("Vector database initialization complete. All Y-Coin data embedded and stored.")


def stream_chat_pipeline(
    user_query: str,
    chat_summary: str,
    system_message: str = "You are an expert, helpful AI assistant for the Y-Coin crypto ecosystem."
) -> Generator[str, None, None]:
    """
    Orchestrates the entire end-to-end pipeline:
    Intent Classification -> Query Enhancement -> Hybrid Retrieval & Cohere Rerank -> LLM Streaming -> Background Summary Update.
    """
    logger.info("--- Starting Orchestration Pipeline ---")
    
    if not user_query or not user_query.strip():
        logger.warning("Empty query received.")
        yield "I didn't catch that. How can I help you today?"
        return

    chat_engine = get_chat()
    full_response = ""

    try:
        # Step 4: Classify User Intent using query_processor.py
        logger.info("Classifying user intent...")
        intent = classify_user_intent(user_query=user_query, chat_summary=chat_summary)
        
        # Step 5: Route based on classification flags
        if intent.is_general_message:
            logger.info("Route: Standard Chat (No Vector Search needed)")
            
            response_stream = chat_engine.stream_standard_response(
                system_message=system_message,
                prev_chat_summary=chat_summary,
                user_query=user_query
            )
            
        elif intent.is_ycoin_related:
            logger.info("Route: RAG Chat (Vector Retrieval & Reranking required)")
            
            # 5a. Enhance queries using query_processor.py
            logger.info("Enhancing queries for optimal context expansion...")
            enhanced = enhance_user_query(user_query=user_query, chat_summary=chat_summary)
            enhanced_list = [enhanced.enhanced_query_1, enhanced.enhanced_query_2]
            logger.info(f"Enhanced Queries generated: {enhanced_list}")
            
            # 5b. Retrieve documents using retriever.py (MMR + Cohere Rerank)
            logger.info("Executing MMR retrieval and Cohere compression...")
            retriever = get_retriever()
            documents = retriever.retrieve(original_query=user_query, enhanced_queries=enhanced_list)
            
            # 5c. Format context string securely
            if documents:
                context_string = "\n\n".join([doc.page_content for doc in documents])
                logger.info(f"Successfully retrieved and reranked {len(documents)} document chunks.")
            else:
                context_string = "No relevant Y-Coin documents found in the database."
                logger.warning("Retriever returned zero documents.")
                
            # 5d. Stream RAG response using rag_chat_engine.py
            response_stream = chat_engine.stream_rag_response(
                system_message=system_message,
                prev_chat_summary=chat_summary,
                context=context_string,
                user_query=user_query
            )
        else:
            yield "I encountered an error understanding your request. Please try again."
            return

        # Step 6: Stream chunks out to the client application interface
        logger.info("Streaming response tokens to client...")
        for chunk in response_stream:
            full_response += chunk
            yield chunk

    except Exception as e:
        logger.error(f"Execution failed during pipeline run: {e}", exc_info=True)
        yield "\n[Error: An internal system error occurred while processing your request.]"
        return

    # Step 7: Update and generate new chat summary state in the background
    try:
        logger.info("Generating updated conversation summary...")
        new_summary = chat_engine.summarize_chat(
            prev_chat_summary=chat_summary,
            current_query=user_query,
            current_response=full_response
        )
        logger.info(f"--- Pipeline Cycle Complete ---\nUpdated Summary State: {new_summary}")
        
    except Exception as e:
        logger.error(f"Failed to update chat summary: {e}", exc_info=True)


if __name__ == "__main__":
    # Ensure all required API keys are present before running
    required_keys = ["OPENAI_API_KEY", "PINECONE_API_KEY", "COHERE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"\n[ERROR] Missing required environment variables in your .env file: {missing_keys}")
        print("Please configure them to execute this orchestrator script successfully.")
    else:
        # EXECUTION FLOW:
        # 1. Populate Vector Store with long Y-Coin dummy text chunks
        setup_ycoin_knowledge_base()

        # 2. Initialize the starting state
        current_summary = "No previous conversation."
        chat_engine = get_chat()
        
        print("\n" + "="*60)
        print("Y-Coin Knowledge Base Initialized.")
        print("Type your questions below. Type 'exit' or 'quit' to stop.")
        print("="*60)

        # 3. Interactive Chat Loop
        while True:
            try:
                user_input = input("\nUser: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting chat. Goodbye!")
                    break
                    
                if not user_input:
                    continue

                print("Assistant: ", end="")
                
                # 4. Run orchestrator stream
                output_stream = stream_chat_pipeline(
                    user_query=user_input,
                    chat_summary=current_summary
                )

                # 5. Print chunks and capture the full response for the summarizer
                full_response = ""
                for response_chunk in output_stream:
                    print(response_chunk, end="", flush=True)
                    full_response += response_chunk
                    
                print("\n")
                
                # 6. Update the in-memory summary for the next loop iteration
                # (In a production app, stream_chat_pipeline would save this to a database instead)
                current_summary = chat_engine.summarize_chat(
                    prev_chat_summary=current_summary,
                    current_query=user_input,
                    current_response=full_response
                )
                
            except KeyboardInterrupt:
                # Handle CTRL+C gracefully
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] An unexpected error occurred in the chat loop: {e}")