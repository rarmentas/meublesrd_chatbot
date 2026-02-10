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
- Request Type: {claim_data["request_type"]}
- Claim Type: {claim_data["claim_type"]}
- Multiple Products: {"Yes" if claim_data["multiple_products_damaged"] else "No"}
- Damage Type: {claim_data["damage_type"]}
- Delivery: {claim_data["delivery_date"]} ({days_since_delivery} days ago)
- Product: {claim_data["product_type"]} by {claim_data["manufacturer"]}
- Store: {claim_data["store_of_purchase"]}
- Product Code: {claim_data["product_code"]}
- Confirmation #: {claim_data["purchase_confirmation_number"]}
- Has Attachments: {"Yes" if claim_data["has_attachments"] else "No"}
- Data Consent: {"Yes" if claim_data["data_sharing_consent"] else "No"}

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
            "request_type": claim_data["request_type"],
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
    """Optimized agent feedback: pre-fetches policies, deterministic criteria 1-3, single LLM call."""
    from datetime import datetime, date
    import json

    # --- Deterministic checks (criteria 1-3) ---
    personal_info_ok = feedback_data["personal_info_verified"]
    contract_ownership_ok = feedback_data["contract_ownership"] and bool(feedback_data["contract_number"].strip())
    client_numbers_match = (
        feedback_data["salesforce_client_number"].strip()
        == feedback_data["meublex_client_number"].strip()
    )
    delivery_dates_match = (
        feedback_data["salesforce_delivery_date"]
        == feedback_data["meublex_delivery_date"]
    )

    delivery_date = datetime.strptime(feedback_data["delivery_date"], "%Y-%m-%d").date()
    claim_date = datetime.strptime(feedback_data["claim_date"], "%Y-%m-%d").date()
    days_since_delivery = (date.today() - delivery_date).days
    days_delivery_to_claim = (claim_date - delivery_date).days

    # --- Pre-fetch policies in 2 batch queries (instead of 5 agent tool calls) ---
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

    # --- Single LLM call for criteria 4-8 ---
    prompt = f"""You are a quality assurance evaluator for MueblesRD. Below are the claim details, pre-computed verification results, and relevant company policies.

Criteria 1-3 have already been evaluated deterministically:
- Criterion 1 (Personal Info Consistency): {"PASS" if personal_info_ok else "FAIL"}
- Criterion 2 (Contract Ownership): {"PASS" if contract_ownership_ok else "FAIL"} — Contract #: {feedback_data["contract_number"]}
- Criterion 3 (Client Number Match): {"PASS" if client_numbers_match else "FAIL"} — SF: {feedback_data["salesforce_client_number"]}, MX: {feedback_data["meublex_client_number"]}

=== CLAIM DETAILS ===
- Request Type: {feedback_data["request_type"]}
- Claim Type: {feedback_data["claim_type"]}
- Damage Type: {feedback_data["damage_type"]}
- Product Type: {feedback_data["product_type"]}
- Manufacturer: {feedback_data["manufacturer"]}
- Product Code: {feedback_data["product_code"]}
- Store: {feedback_data["store_of_purchase"]}
- Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Delivery Date: {feedback_data["delivery_date"]} ({days_since_delivery} days ago)
- Salesforce Delivery Date: {feedback_data["salesforce_delivery_date"]}
- Meublex Delivery Date: {feedback_data["meublex_delivery_date"]}
- Delivery Dates Match: {delivery_dates_match}
- Claim Date: {feedback_data["claim_date"]}
- Days Between Delivery and Claim: {days_delivery_to_claim}
- Agent's Eligibility Decision: {"Eligible" if feedback_data["eligible"] else "Not Eligible"}
- Customer Description: "{feedback_data["description"]}"

=== COMPANY POLICIES ===
{policies_text}

Using ONLY the policies above, evaluate criteria 4-8:

4. Delivery Date Consistency — Are delivery dates consistent? Is the claim within the allowed timeframe?
5. Damage Classification — Does the damage type match the customer description per policy?
6. Attachments — Are attachments provided as required by policy?
7. Warranty Eligibility by Claim Date — Was the claim filed within the warranty window for this product/damage/manufacturer?
8. Eligibility Decision — Considering all 7 prior results, is the agent's eligibility decision correct?

Return ONLY valid JSON with this exact structure:
{{
    "delivery_date_consistency": {{"result": true/false, "recommendation": "one sentence"}},
    "damage_classification_validation": {{"result": true/false, "recommendation": "one sentence"}},
    "attachments_verification": {{"result": true/false, "recommendation": "one sentence"}},
    "warranty_eligibility_by_claim_date": {{"result": true/false, "recommendation": "one sentence"}},
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
            "delivery_date_consistency": {"result": delivery_dates_match, "recommendation": "Unable to parse LLM response."},
            "damage_classification_validation": {"result": False, "recommendation": "Unable to parse LLM response."},
            "attachments_verification": {"result": feedback_data["has_attachments"], "recommendation": "Unable to parse LLM response."},
            "warranty_eligibility_by_claim_date": {"result": False, "recommendation": "Unable to parse LLM response."},
            "eligibility_decision": {"isDecisionCorrect": False, "explanation": "Unable to parse LLM response."},
            "final_recommendation": "Unable to parse LLM response. Please review manually.",
            "final_eligibility": {"isEligible": False, "justification": "Unable to parse LLM response."}
        }

    # Merge deterministic + LLM results
    return {
        "claim_summary": {
            "request_type": feedback_data["request_type"],
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
            "personal_information_consistency": {"result": personal_info_ok},
            "contract_ownership_verification": {"result": contract_ownership_ok},
            "client_number_validation": {"result": client_numbers_match},
            "delivery_date_consistency": parsed.get("delivery_date_consistency", {}),
            "damage_classification_validation": parsed.get("damage_classification_validation", {}),
            "attachments_verification": parsed.get("attachments_verification", {}),
            "warranty_eligibility_by_claim_date": parsed.get("warranty_eligibility_by_claim_date", {}),
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
    """Evaluate a store agent's claim handling across 7 criteria using RAG."""
    from datetime import datetime, date
    import json

    # --- Pre-compute deterministic checks ---
    personal_info_verified = feedback_data["personal_info_verified"]
    client_numbers_match = (
        feedback_data["salesforce_client_number"].strip()
        == feedback_data["meublex_client_number"].strip()
    )
    delivery_dates_match = (
        feedback_data["salesforce_delivery_date"]
        == feedback_data["meublex_delivery_date"]
    )

    delivery_date = datetime.strptime(feedback_data["delivery_date"], "%Y-%m-%d").date()
    claim_date = datetime.strptime(feedback_data["claim_date"], "%Y-%m-%d").date()
    days_since_delivery = (date.today() - delivery_date).days
    days_delivery_to_claim = (claim_date - delivery_date).days

    # --- Build context string ---
    claim_context = f"""
=== CLAIM DETAILS ===
- Request Type: {feedback_data["request_type"]}
- Claim Type: {feedback_data["claim_type"]}
- Multiple Products Damaged: {"Yes" if feedback_data["multiple_products_damaged"] else "No"}
- Damage Type: {feedback_data["damage_type"]}
- Product Type: {feedback_data["product_type"]}
- Manufacturer: {feedback_data["manufacturer"]}
- Store of Purchase: {feedback_data["store_of_purchase"]}
- Product Code: {feedback_data["product_code"]}
- Purchase Confirmation #: {feedback_data["purchase_confirmation_number"]}
- Data Sharing Consent: {"Yes" if feedback_data["data_sharing_consent"] else "No"}
- Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Customer Description: "{feedback_data["description"]}"

=== VERIFICATION DATA ===
- Criterion 1 - Personal Info Verified (across Salesforce, Webform, Meublex): {personal_info_verified}
- Criterion 2 - Contract Ownership Verified: {feedback_data["contract_ownership"]}
- Criterion 2 - Contract Number: {feedback_data["contract_number"]}
- Criterion 3 - Salesforce Client Number: {feedback_data["salesforce_client_number"]}
- Criterion 3 - Meublex Client Number: {feedback_data["meublex_client_number"]}
- Criterion 3 - Client Numbers Match: {client_numbers_match}
- Criterion 4 - Delivery Date (from claim): {feedback_data["delivery_date"]} ({days_since_delivery} days ago)
- Criterion 4 - Salesforce Delivery Date: {feedback_data["salesforce_delivery_date"]}
- Criterion 4 - Meublex Delivery Date: {feedback_data["meublex_delivery_date"]}
- Criterion 4 - Delivery Dates Match: {delivery_dates_match}
- Criterion 6 - Has Attachments: {"Yes" if feedback_data["has_attachments"] else "No"}
- Criterion 7 - Agent's Eligibility Decision: {"Eligible" if feedback_data["eligible"] else "Not Eligible"}
- Criterion 8 - Claim Date: {feedback_data["claim_date"]}
- Criterion 8 - Days Between Delivery and Claim: {days_delivery_to_claim}
- Criterion 8 - Damage Type: {feedback_data["damage_type"]}
- Criterion 8 - Manufacturer: {feedback_data["manufacturer"]}
- Criterion 8 - Product Type: {feedback_data["product_type"]}
"""

    system_prompt = """You are a quality assurance evaluator for MueblesRD. Your task is to evaluate a store agent's handling of a customer claim across 8 criteria.

You have access to the retrieve_policies tool. Use it to look up company policies when needed.

EVALUATION CRITERIA:

1. Personal Information Consistency (Law 25 Compliance)
   - The `personal_info_verified` boolean indicates whether personal data (names, emails) was verified as consistent across Salesforce, Webform, and Meublex systems.
   - If true: personal data is consistent. Assess Law 25 compliance implications.
   - If false: there is a mismatch. Flag the compliance risk.

2. Contract Ownership Verification
   - The `contract_ownership` boolean indicates whether the agent confirmed the correct contract owner.
   - Verify the contract number is provided and appears valid (non-empty, reasonable format).
   - If contract_ownership is true: the agent confirmed ownership. Validate that a contract number is also present.
   - If contract_ownership is false: flag that ownership was not confirmed.

3. Client Number Validation
   - The pre-computed `client_numbers_match` boolean tells you if Salesforce and Meublex client numbers are identical.
   - Explain the implications of a match or mismatch.

4. Delivery Date Consistency (REQUIRES POLICY LOOKUP)
   - The pre-computed `delivery_dates_match` boolean tells you if Salesforce and Meublex delivery dates are identical.
   - Use retrieve_policies to look up deadline policies for the claim type.
   - Assess whether the claim is within the allowed timeframe based on days since delivery.

5. Damage Classification Validation (REQUIRES POLICY LOOKUP)
   - Compare the selected damage type against the customer's description.
   - Use retrieve_policies to look up policies for the damage type and product type.
   - Assess whether the classification is correct.

6. Attachments Verification (REQUIRES POLICY LOOKUP)
   - Check whether attachments are provided.
   - Use retrieve_policies to look up attachment requirements for this claim type.
   - Explain why attachments are or are not required.

7. Warranty Eligibility by Claim Date (REQUIRES POLICY LOOKUP)
   - Compare the claim date against the delivery date. The pre-computed `days_delivery_to_claim` tells you how many days elapsed between delivery and the claim submission.
   - Use retrieve_policies to look up warranty periods and deadline policies for the specific combination of: damage type, product type, and manufacturer.
   - Assess whether the claim was filed within the allowed warranty window according to company policies.
   - Consider the customer's description and damage type to determine if the timeframe is consistent with the reported issue.

8. Eligibility Decision (REQUIRES POLICY LOOKUP)
   - Synthesize results from all 7 previous criteria.
   - Use retrieve_policies to confirm eligibility rules.
   - Determine if the agent's eligibility decision is correct.

Return your response as valid JSON with this EXACT structure:
{
    "criteria_evaluations": {
        "personal_information_consistency": {"result": true/false, "explanation": "..."},
        "contract_ownership_verification": {"result": true/false, "explanation": "..."},
        "client_number_validation": {"result": true/false, "explanation": "..."},
        "delivery_date_consistency": {"result": true/false, "recommendation": "..."},
        "damage_classification_validation": {"result": true/false, "recommendation": "..."},
        "attachments_verification": {"result": true/false, "recommendation": "..."},
        "warranty_eligibility_by_claim_date": {"result": true/false, "recommendation": "..."},
        "eligibility_decision": {"isDecisionCorrect": true/false, "explanation": "..."}
    },
    "final_recommendation": "A summary recommendation for the agent",
    "final_eligibility": {"isEligible": true/false, "justification": "..."}
}"""

    agent = create_agent(model, tools=[retrieve_policies], system_prompt=system_prompt)

    user_message = f"""Evaluate this agent's claim handling:
{claim_context}

Please retrieve policies for the following topics to complete your evaluation:
1. Claim type "{feedback_data["claim_type"]}" policies and deadlines
2. Damage type "{feedback_data["damage_type"]}" classification rules for "{feedback_data["product_type"]}"
3. Attachment requirements for claims
4. Warranty periods and deadline policies for "{feedback_data["product_type"]}" by "{feedback_data["manufacturer"]}" with "{feedback_data["damage_type"]}" damage
5. Eligibility criteria and delivery deadline policies

After retrieving the relevant policies, evaluate all 8 criteria and return the structured JSON response."""

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
                "personal_information_consistency": {"result": personal_info_verified, "explanation": "Unable to parse LLM response."},
                "contract_ownership_verification": {"result": feedback_data["contract_ownership"], "explanation": "Unable to parse LLM response."},
                "client_number_validation": {"result": client_numbers_match, "explanation": "Unable to parse LLM response."},
                "delivery_date_consistency": {"result": delivery_dates_match, "recommendation": "Unable to parse LLM response."},
                "damage_classification_validation": {"result": False, "recommendation": "Unable to parse LLM response."},
                "attachments_verification": {"result": feedback_data["has_attachments"], "recommendation": "Unable to parse LLM response."},
                "warranty_eligibility_by_claim_date": {"result": False, "recommendation": "Unable to parse LLM response."},
                "eligibility_decision": {"isDecisionCorrect": False, "explanation": "Unable to parse LLM response."}
            },
            "final_recommendation": "Unable to parse LLM response. Please review manually.",
            "final_eligibility": {"isEligible": False, "justification": "Unable to parse LLM response."}
        }

    return {
        "claim_summary": {
            "request_type": feedback_data["request_type"],
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