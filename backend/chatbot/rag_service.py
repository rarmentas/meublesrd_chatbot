"""
Self-contained RAG pipeline for MueblesRD chatbot.
Replicates the logic from backend/core.py.
"""

import os
from typing import Any, Dict
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain.tools import tool
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# Load environment variables from parent directory's .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Initialize embeddings (same as ingestion.py)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize vector store
vectorstore = PineconeVectorStore(
    index_name="mueblesrd-index", embedding=embeddings
)

# Initialize chat model
model = init_chat_model("gpt-5.2", model_provider="openai")


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve relevant MueblesRD policies and procedures to help answer customer service questions."""
    # Retrieve top 4 most similar documents
    retrieved_docs = vectorstore.as_retriever().invoke(query, k=4)

    # Serialize documents for the model
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Unknown')}\n\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )

    # Return both serialized content and raw documents
    return serialized, retrieved_docs


def run_llm(query: str) -> Dict[str, Any]:
    """
    Run the RAG pipeline to answer a query using retrieved documentation.

    Args:
        query: The user's question

    Returns:
        Dictionary containing:
            - answer: The generated answer
            - context: List of retrieved documents
    """
    # Create the agent with retrieval tool
    system_prompt = (
        "You are an internal assistant for MueblesRD store agents. The user is a store employee "
        "who handles customer requests and needs guidance on company policies and procedures. "
        "Your role is to help the agent:\n"
        "- Process customer requests correctly following company procedures\n"
        "- Verify Law 25 compliance when handling customer data\n"
        "- Validate contracts and customer information in Salesforce and Meublex\n"
        "- Check deadlines and delivery dates\n"
        "- Determine request admissibility (aesthetic vs mechanical damage)\n"
        "- Handle duplicate requests and merge them properly\n"
        "- Follow up on ADS (After-Sales Service) requests\n\n"
        "Always respond as if you are guiding a colleague through the steps. "
        "Use clear, actionable instructions like 'You should...', 'First, check...', 'Navigate to...'. "
        "You have access to a tool that retrieves relevant policy documentation. "
        "Use the tool to find relevant information before answering questions. "
        "When citing sources, DO NOT mention the filename. Instead, cite the specific section name "
        "or policy topic (e.g., 'Section 1: Compliance with Law 25', 'Duplicate Verification procedure', "
        "'Validation of Contract Number', 'Respecting Deadlines', 'Information Verification', etc.). "
        "Always reference the relevant procedure number and title in your answer. "
        "If you cannot find the answer in the retrieved documentation, say so."
    )

    agent = create_agent(model, tools=[retrieve_context], system_prompt=system_prompt)

    # Build messages list
    messages = [{"role": "user", "content": query}]

    # Invoke the agent
    response = agent.invoke({"messages": messages})

    # Extract the answer from the last AI message
    answer = response["messages"][-1].content

    # Extract context documents from ToolMessage artifacts
    context_docs = []
    for message in response["messages"]:
        # Check if this is a ToolMessage with artifact
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            # The artifact should contain the list of Document objects
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)

    return {
        "answer": answer,
        "context": context_docs
    }
