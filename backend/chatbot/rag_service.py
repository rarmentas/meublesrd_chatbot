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

# Load environment variables from backend_django root .env file
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


# ============================================================
# Claim Analysis Agent
# ============================================================


def _extract_sources_from_docs(docs):
    """Extract section names from documents, filtering out PDF filenames."""
    import re

    SECTION_PATTERNS = [
        r"(\d+\.?\d*\.-[A-Za-z\s]+)",
        r"(\d+\.\s*[A-Z][A-Za-z\s]+(?:of|and|the|in|to|for|with)?[A-Za-z\s]*)",
    ]

    def extract_section_from_content(content: str) -> str:
        for pattern in SECTION_PATTERNS:
            match = re.search(pattern, content)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 10:
                    return title[:80]
        first_line = content.split('\n')[0].strip()
        if first_line and len(first_line) < 100 and not first_line.endswith('.'):
            return first_line[:80]
        return None

    sources = []
    seen = set()

    for doc in docs:
        source = None
        if hasattr(doc, "metadata"):
            meta_source = doc.metadata.get("source", "")
            if meta_source and not meta_source.lower().endswith('.pdf'):
                source = meta_source
        if not source and hasattr(doc, "page_content"):
            source = extract_section_from_content(doc.page_content)
        if source and source not in seen:
            seen.add(source)
            sources.append(source)

    return sources


@tool(response_format="content_and_artifact")
def retrieve_policies(query: str):
    """Retrieve relevant MueblesRD policies for handling customer claims."""
    retrieved_docs = vectorstore.as_retriever().invoke(query, k=4)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Unknown')}\n\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


@tool
def analyze_tone(message: str) -> Dict[str, Any]:
    """Analyze customer message tone as neutral, kind, or aggressive."""
    tone_prompt = f"""Analyze the tone of this customer message and classify it as one of:
- "neutral": Factual, no strong emotion
- "kind": Polite, understanding, patient
- "aggressive": Frustrated, angry, demanding

Message: "{message}"

Return ONLY valid JSON with these exact keys:
- "tone": one of "neutral", "kind", or "aggressive"
- "confidence": a number between 0.0 and 1.0
- "indicators": a list of 2-4 specific text examples or patterns from the message that support your classification

Example response format:
{{"tone": "aggressive", "confidence": 0.85, "indicators": ["Use of 'unacceptable'", "Exclamation marks"]}}"""

    response = model.invoke(tone_prompt)
    import json
    try:
        # Try to parse JSON from the response
        content = response.content.strip()
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception:
        return {"tone": "neutral", "confidence": 0.5, "indicators": []}


def analyze_claim(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a customer claim with RAG and tone analysis."""
    from datetime import datetime, date
    import json

    # Calculate days since delivery
    delivery_date = datetime.strptime(claim_data["delivery_date"], "%Y-%m-%d").date()
    days_since_delivery = (date.today() - delivery_date).days

    # Build claim context
    claim_context = f"""
Claim Details:
- Claim Type: {claim_data["claim_type"]}
- Damage Type: {claim_data["damage_type"]}
- Delivery: {claim_data["delivery_date"]} ({days_since_delivery} days ago)
- Product: {claim_data["product_type"]} by {claim_data["manufacturer"]}
- Store: {claim_data["store_of_purchase"]}
- Product Code: {claim_data["product_code"]}
- Has Attachments: {"Yes" if claim_data["has_attachments"] else "No"}

Customer Message:
"{claim_data["description"]}"
"""

    system_prompt = """You are a claims analyst for MueblesRD. Analyze claims using the available tools:
1. retrieve_policies - Find relevant company policies for the claim type
2. analyze_tone - Evaluate customer message tone

Your task is to:
1. First retrieve relevant policies for the claim type and damage type
2. Analyze the customer's message tone
3. Combine both analyses to provide structured recommendations

Based on your analysis, provide recommendations including:
- Policy-based recommendations with specific section references
- Communication approach based on tone (standard/empathetic/de-escalation/formal)
- Ordered next steps for the customer service agent

IMPORTANT: When citing sources, use policy section names, never PDF filenames.

Return your final response as valid JSON with this exact structure:
{
    "tone_analysis": {"tone": "...", "confidence": 0.0, "indicators": []},
    "policy_recommendations": [
        {"policy_reference": "Section X: Title", "recommendation": "...", "priority": "high|medium|low"}
    ],
    "communication_recommendations": {
        "approach": "standard|empathetic|de-escalation|formal",
        "tips": ["tip1", "tip2"],
        "suggested_opening": "..."
    },
    "next_steps": ["step1", "step2"]
}"""

    agent = create_agent(model, tools=[retrieve_policies, analyze_tone], system_prompt=system_prompt)

    user_message = f"""Analyze this claim and provide recommendations:
{claim_context}

Please:
1. Retrieve policies relevant to "{claim_data["claim_type"]}" with "{claim_data["damage_type"]}" damage on "{claim_data["product_type"]}"
2. Analyze the tone of the customer message
3. Provide structured recommendations in JSON format"""

    response = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    # Extract answer and context
    answer = response["messages"][-1].content

    context_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)

    # Parse structured response from answer (JSON)
    try:
        # Handle potential markdown code blocks
        content = answer.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content)
    except Exception:
        # Fallback structure if parsing fails
        parsed = {
            "policy_recommendations": [],
            "communication_recommendations": {
                "approach": "standard",
                "tips": [],
                "suggested_opening": ""
            },
            "next_steps": [],
            "tone_analysis": {"tone": "neutral", "confidence": 0.5, "indicators": []}
        }

    # Build final response
    return {
        "claim_summary": {
            "claim_type": claim_data["claim_type"],
            "product_type": claim_data["product_type"],
            "damage_type": claim_data["damage_type"],
            "days_since_delivery": days_since_delivery
        },
        "tone_analysis": parsed.get("tone_analysis", {}),
        "policy_recommendations": parsed.get("policy_recommendations", []),
        "communication_recommendations": parsed.get("communication_recommendations", {}),
        "next_steps": parsed.get("next_steps", []),
        "sources": _extract_sources_from_docs(context_docs)
    }


# ============================================================
# Agent Feedback Evaluation — Optimized (single LLM call)
# ============================================================


def evaluate_agent_feedback_optimized(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Optimized agent feedback: pre-fetches policies, deterministic criterion 1, single LLM call for 2-5."""
    from datetime import datetime, date
    import json

    # --- Deterministic check (criterion 1) ---
    has_contract_number = bool(feedback_data["contract_number"].strip())

    delivery_date = datetime.strptime(feedback_data["delivery_date"], "%Y-%m-%d").date()
    claim_date = datetime.strptime(feedback_data["claim_date"], "%Y-%m-%d").date()
    days_since_delivery = (date.today() - delivery_date).days
    days_delivery_to_claim = (claim_date - delivery_date).days

    # --- Pre-fetch policies in 2 batch queries ---
    retriever = vectorstore.as_retriever()

    query_1 = (
        f"{feedback_data['claim_type']} {feedback_data['damage_type']} "
        f"{feedback_data['product_type']} deadlines warranty eligibility"
    )
    query_2 = (
        f"attachments requirements claim evidence "
        f"{feedback_data['damage_type']} {feedback_data['product_type']}"
    )

    docs_1 = retriever.invoke(query_1, k=4)
    docs_2 = retriever.invoke(query_2, k=4)

    # Deduplicate docs
    all_docs = docs_1.copy()
    seen_contents = {doc.page_content for doc in docs_1}
    for doc in docs_2:
        if doc.page_content not in seen_contents:
            all_docs.append(doc)
            seen_contents.add(doc.page_content)

    policies_text = "\n\n---\n\n".join(
        f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
        for doc in all_docs
    )

    # --- Single LLM call for criteria 2-5 ---
    prompt = f"""You are a quality assurance evaluator for MueblesRD. Below are the claim details, pre-computed verification results, and relevant company policies.

Criterion 1 has already been evaluated deterministically:
- Criterion 1 (Contract Verification): {"PASS" if has_contract_number else "FAIL"} — Contract #: {feedback_data["contract_number"]}

=== CLAIM DETAILS ===
- Claim Type: {feedback_data["claim_type"]}
- Damage Type: {feedback_data["damage_type"]}
- Product Type: {feedback_data["product_type"]}
- Manufacturer: {feedback_data["manufacturer"]}
- Product Code: {feedback_data["product_code"]}
- Store: {feedback_data["store_of_purchase"]}
- Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Delivery Date: {feedback_data["delivery_date"]} ({days_since_delivery} days ago)
- Claim Date: {feedback_data["claim_date"]}
- Days Between Delivery and Claim: {days_delivery_to_claim}
- Agent's Eligibility Decision: {"Eligible" if feedback_data["eligible"] else "Not Eligible"}
- Customer Description: "{feedback_data["description"]}"

=== COMPANY POLICIES ===
{policies_text}

Using ONLY the policies above, evaluate criteria 2-5:

2. Delivery Date — Is the claim within the allowed warranty timeframe based on delivery_date, claim_date, description, manufacturer, and company policies? Result should be "In Warranty" or "Out of Warranty". Remind the agent to check the delivery date in other systems.
3. Damage Classification — Does the damage type match the customer description per policy and product type?
4. Attachments — Are attachments provided as required by policy for the claim description?
5. Eligibility Decision — Considering all 4 prior results, is the agent's eligibility decision correct?

Return ONLY valid JSON with this exact structure:
{{
    "delivery_date": {{"result": "In Warranty"/"Out of Warranty", "recommendation": "one sentence"}},
    "damage_classification_validation": {{"result": true/false, "recommendation": "one sentence"}},
    "attachments_verification": {{"result": true/false, "recommendation": "one sentence"}},
    "eligibility_decision": {{"isDecisionCorrect": true/false, "explanation": "one sentence"}},
    "final_recommendation": "summary recommendation for the agent",
    "final_eligibility": {{"isEligible": true/false, "justification": "one sentence"}}
}}"""

    response = model.invoke(prompt)
    answer = response.content.strip()

    # Parse JSON
    try:
        content = answer
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content)
    except Exception:
        parsed = {
            "delivery_date": {"result": "Unknown", "recommendation": "Unable to parse LLM response."},
            "damage_classification_validation": {"result": False, "recommendation": "Unable to parse LLM response."},
            "attachments_verification": {"result": feedback_data["has_attachments"], "recommendation": "Unable to parse LLM response."},
            "eligibility_decision": {"isDecisionCorrect": False, "explanation": "Unable to parse LLM response."},
            "final_recommendation": "Unable to parse LLM response. Please review manually.",
            "final_eligibility": {"isEligible": False, "justification": "Unable to parse LLM response."}
        }

    # Build deterministic criterion 1 result with explanation per prompt
    contract_result = "Correct" if has_contract_number else "Incorrect"
    contract_explanation = (
        f"Contract number {'is' if has_contract_number else 'is not'} provided "
        f"({feedback_data['contract_number'] if has_contract_number else 'missing'}). "
        "IMPORTANT: Please compare the name of the person that made the ticket or claim "
        "against the data in the contract to ensure they match."
    )

    # Merge deterministic + LLM results
    return {
        "claim_summary": {
            "claim_type": feedback_data["claim_type"],
            "product_type": feedback_data["product_type"],
            "damage_type": feedback_data["damage_type"],
            "manufacturer": feedback_data["manufacturer"],
            "claim_date": feedback_data["claim_date"],
            "days_since_delivery": days_since_delivery,
            "days_delivery_to_claim": days_delivery_to_claim,
            "eligible_input": feedback_data["eligible"]
        },
        "criteria_evaluations": {
            "contract_verification": {"result": contract_result, "explanation": contract_explanation},
            "delivery_date": parsed.get("delivery_date", {}),
            "damage_classification_validation": parsed.get("damage_classification_validation", {}),
            "attachments_verification": parsed.get("attachments_verification", {}),
            "eligibility_decision": parsed.get("eligibility_decision", {})
        },
        "final_recommendation": parsed.get("final_recommendation", ""),
        "final_eligibility": parsed.get("final_eligibility", {}),
        "sources": _extract_sources_from_docs(all_docs)
    }


# ============================================================
# Agent Feedback Evaluation
# ============================================================


def evaluate_agent_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a store agent's claim handling across 5 criteria using RAG (exhaustive, multi-step agent)."""
    from datetime import datetime, date
    import json

    # --- Pre-compute deterministic check (criterion 1) ---
    has_contract_number = bool(feedback_data["contract_number"].strip())

    delivery_date = datetime.strptime(feedback_data["delivery_date"], "%Y-%m-%d").date()
    claim_date = datetime.strptime(feedback_data["claim_date"], "%Y-%m-%d").date()
    days_since_delivery = (date.today() - delivery_date).days
    days_delivery_to_claim = (claim_date - delivery_date).days

    # --- Build context string ---
    claim_context = f"""
=== CLAIM DETAILS ===
- Claim Type: {feedback_data["claim_type"]}
- Damage Type: {feedback_data["damage_type"]}
- Product Type: {feedback_data["product_type"]}
- Manufacturer: {feedback_data["manufacturer"]}
- Store of Purchase: {feedback_data["store_of_purchase"]}
- Product Code: {feedback_data["product_code"]}
- Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Customer Description: "{feedback_data["description"]}"

=== VERIFICATION DATA ===
- Criterion 1 - Contract Number Provided: {"Yes" if has_contract_number else "No"} — Contract #: {feedback_data["contract_number"]}
- Criterion 2 - Delivery Date (from claim): {feedback_data["delivery_date"]} ({days_since_delivery} days ago)
- Criterion 2 - Claim Date: {feedback_data["claim_date"]}
- Criterion 2 - Days Between Delivery and Claim: {days_delivery_to_claim}
- Criterion 4 - Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Criterion 5 - Agent's Eligibility Decision: {"Eligible" if feedback_data["eligible"] else "Not Eligible"}
"""

    # Load prompt from file
    prompt_path = BASE_DIR / 'mueblesrd_api' / 'prompts' / 'feedback-agent.txt'
    with open(prompt_path, 'r') as f:
        feedback_prompt = f.read()

    system_prompt = f"""{feedback_prompt}

You have access to the retrieve_policies tool. Use it to look up company policies when needed.

Return your response as valid JSON with this EXACT structure:
{{
    "criteria_evaluations": {{
        "contract_verification": {{"result": "Correct"/"Incorrect", "explanation": "..."}},
        "delivery_date": {{"result": "In Warranty"/"Out of Warranty", "recommendation": "..."}},
        "damage_classification_validation": {{"result": true/false, "recommendation": "..."}},
        "attachments_verification": {{"result": true/false, "recommendation": "..."}},
        "eligibility_decision": {{"isDecisionCorrect": true/false, "explanation": "..."}}
    }},
    "final_recommendation": "A summary recommendation for the agent",
    "final_eligibility": {{"isEligible": true/false, "justification": "..."}}
}}"""

    agent = create_agent(model, tools=[retrieve_policies], system_prompt=system_prompt)

    user_message = f"""Evaluate this agent's claim handling:
{claim_context}

Please retrieve policies for the following topics to complete your evaluation:
1. Claim type "{feedback_data["claim_type"]}" policies and deadlines
2. Damage type "{feedback_data["damage_type"]}" classification rules for "{feedback_data["product_type"]}"
3. Attachment requirements for claims
4. Warranty periods and deadline policies for "{feedback_data["product_type"]}" by "{feedback_data["manufacturer"]}" with "{feedback_data["damage_type"]}" damage
5. Eligibility criteria and delivery deadline policies

After retrieving the relevant policies, evaluate all 5 criteria and return the structured JSON response."""

    response = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    # Extract answer and context docs
    answer = response["messages"][-1].content

    context_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                context_docs.extend(message.artifact)

    # Parse JSON response
    try:
        content = answer.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content)
    except Exception:
        parsed = {
            "criteria_evaluations": {
                "contract_verification": {"result": "Correct" if has_contract_number else "Incorrect", "explanation": "Unable to parse LLM response."},
                "delivery_date": {"result": "Unknown", "recommendation": "Unable to parse LLM response."},
                "damage_classification_validation": {"result": False, "recommendation": "Unable to parse LLM response."},
                "attachments_verification": {"result": feedback_data["has_attachments"], "recommendation": "Unable to parse LLM response."},
                "eligibility_decision": {"isDecisionCorrect": False, "explanation": "Unable to parse LLM response."}
            },
            "final_recommendation": "Unable to parse LLM response. Please review manually.",
            "final_eligibility": {"isEligible": False, "justification": "Unable to parse LLM response."}
        }

    return {
        "claim_summary": {
            "claim_type": feedback_data["claim_type"],
            "product_type": feedback_data["product_type"],
            "damage_type": feedback_data["damage_type"],
            "manufacturer": feedback_data["manufacturer"],
            "claim_date": feedback_data["claim_date"],
            "days_since_delivery": days_since_delivery,
            "days_delivery_to_claim": days_delivery_to_claim,
            "eligible_input": feedback_data["eligible"]
        },
        "criteria_evaluations": parsed.get("criteria_evaluations", {}),
        "final_recommendation": parsed.get("final_recommendation", ""),
        "final_eligibility": parsed.get("final_eligibility", {}),
        "sources": _extract_sources_from_docs(context_docs)
    }