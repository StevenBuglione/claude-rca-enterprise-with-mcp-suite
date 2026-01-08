from __future__ import annotations

RCA_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "contributing_factors": {"type": "array", "items": {"type": "string"}},
        "recommended_fixes": {"type": "array", "items": {"type": "string"}},
        "remediation_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action": {"type": "string"},
                    "rationale": {"type": "string"},
                    "validation": {"type": "string"},
                    "owner": {"type": "string"},
                    "priority": {"type": "string"},
                    "rollback": {"type": "string"}
                },
                "required": ["action", "validation"]
            }
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "evidence_id": {"type": "string"},
                    "source": {"type": "string"},
                    "locator": {"type": "string"},
                    "quote": {"type": "string"}
                },
                "required": ["evidence_id", "source", "locator", "quote"]
            }
        },
        "confidence": {"type": "string"}
    },
    "required": ["summary", "root_cause", "recommended_fixes", "remediation_steps", "citations"]
}
