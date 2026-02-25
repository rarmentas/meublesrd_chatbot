"""
Semantic claim_type validation for RAG endpoints.

Hybrid approach: fast keyword matching handles most inputs instantly,
with an LLM fallback for ambiguous cases.

Supported claim types: defective products, damaged items, missing pieces,
missing/error products.
Unsupported: delivery complaints, home/property damage, warranty programs.
"""

import re
import logging

logger = logging.getLogger(__name__)

UNSUPPORTED_MESSAGE = (
    "This claim type is not supported. The system can only process claims "
    "related to defective products, damaged items, or missing pieces. "
    "Please verify the claim type and try again."
)

# ---- Keyword patterns ----

ACCEPT_PATTERNS = [
    # English
    r"defective",
    r"damaged",
    r"broken",
    r"missing\s*(part|piece|screw|component|hardware)",
    r"missing\s*product",
    r"error\s*product",
    r"wrong\s*product",
    r"wrong\s*item",
    r"cracked",
    r"scratched",
    r"dented",
    r"faulty",
    r"not\s*working",
    r"malfunction",
    r"chipped",
    r"bent",
    r"stain",
    r"torn",
    r"missing\s*item",
    # Spanish
    r"defectuoso",
    r"da[ñn]ado",
    r"roto",
    r"pieza\s*faltante",
    r"parte\s*faltante",
    r"producto\s*faltante",
    r"producto\s*equivocado",
    r"producto\s*err[oó]neo",
    r"producto\s*incorrecto",
    r"agrietado",
    r"rayado",
    r"abollado",
    r"no\s*funciona",
    r"averiado",
    r"manchado",
    r"desgarrado",
    r"falla",
]

REJECT_PATTERNS = [
    # English
    r"delivery\s*complaint",
    r"late\s*delivery",
    r"home\s*damage",
    r"property\s*damage",
    r"warranty\s*program",
    r"comford?\s*warranty",
    r"shipping\s*delay",
    r"never\s*arrived",
    r"not\s*delivered",
    # Spanish
    r"queja\s*de\s*entrega",
    r"da[ñn]o\s*(en\s*)?(el\s*)?(hogar|casa|propiedad)",
    r"garant[ií]a",
    r"retraso\s*(de|en)\s*entrega",
    r"no\s*(fue\s*)?entregado",
    r"nunca\s*lleg[oó]",
]

_accept_re = re.compile("|".join(ACCEPT_PATTERNS), re.IGNORECASE)
_reject_re = re.compile("|".join(REJECT_PATTERNS), re.IGNORECASE)


def classify_claim_type_fast(claim_type: str) -> str:
    """Fast keyword-based classification.

    Returns:
        "accept" — matches a supported claim pattern
        "reject" — matches an unsupported claim pattern
        "ambiguous" — no clear match or conflicting signals
    """
    text = claim_type.strip()
    has_accept = bool(_accept_re.search(text))
    has_reject = bool(_reject_re.search(text))

    if has_accept and has_reject:
        return "ambiguous"
    if has_accept:
        return "accept"
    if has_reject:
        return "reject"
    return "ambiguous"


def classify_claim_type_llm(claim_type: str) -> bool:
    """LLM-based classification fallback for ambiguous inputs.

    Returns True if the claim type is supported, False otherwise.
    """
    from .rag_service import model  # lazy import to avoid circular deps

    prompt = (
        "You are a claim-type classifier for a furniture company. "
        "The system ONLY handles these claim categories:\n"
        "- Defective products (broken, faulty, not working)\n"
        "- Damaged items (scratched, dented, cracked, stained)\n"
        "- Missing pieces or parts (screws, hardware, components)\n"
        "- Missing or wrong products (error product, wrong item)\n\n"
        "The system does NOT handle:\n"
        "- Delivery complaints (late delivery, never arrived)\n"
        "- Home or property damage caused by a product\n"
        "- Warranty programs or extended warranty claims\n\n"
        f'Is the following claim type supported? "{claim_type}"\n\n'
        "Answer ONLY with YES or NO."
    )

    try:
        response = model.invoke(prompt)
        answer = response.content.strip().upper()
        return answer.startswith("YES")
    except Exception:
        logger.exception("LLM claim-type classification failed for: %s", claim_type)
        # On LLM failure, accept to avoid blocking legitimate claims
        return True


def validate_claim_type(claim_type: str) -> tuple[bool, str]:
    """Validate whether a claim_type is supported.

    Returns:
        (is_valid, error_message) — error_message is empty when valid.
    """
    fast_result = classify_claim_type_fast(claim_type)

    if fast_result == "accept":
        return True, ""
    if fast_result == "reject":
        return False, UNSUPPORTED_MESSAGE

    # Ambiguous — ask the LLM
    is_supported = classify_claim_type_llm(claim_type)
    if is_supported:
        return True, ""
    return False, UNSUPPORTED_MESSAGE
