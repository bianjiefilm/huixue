"""
BYOK (Bring Your Own Key) pure validation functions.

No logging, no I/O — only data in, data out.
"""
from typing import Optional, Dict, Any


def is_agentpilot_enabled(api_key: Optional[str], workspace_id: Optional[str]) -> bool:
    """Check whether AgentPilot integration is fully configured."""
    return bool(api_key and workspace_id)


def validate_api_key_format(key: Optional[str], *, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate an API key string.

    Returns {"valid": True/False, "reason": str | None}.
    """
    if not key:
        return {"valid": False, "reason": "API key is empty or missing"}
    if len(key) < min_length:
        return {"valid": False, "reason": f"API key too short (min {min_length} chars)"}
    if key.strip() != key:
        return {"valid": False, "reason": "API key has leading/trailing whitespace"}
    return {"valid": True, "reason": None}


def byok_status(
    agentpilot_key: Optional[str],
    agentpilot_workspace: Optional[str],
    ark_key: Optional[str],
) -> Dict[str, Any]:
    """
    Return a summary of which BYOK integrations are configured.

    Pure function — no side effects.
    """
    ap_enabled = is_agentpilot_enabled(agentpilot_key, agentpilot_workspace)
    return {
        "agentpilot_enabled": ap_enabled,
        "ark_configured": bool(ark_key),
        "fully_configured": ap_enabled and bool(ark_key),
    }
