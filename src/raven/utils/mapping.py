from typing import Dict

from ..utils.schemas import AgentListen


def listening_mapping(key: str) -> AgentListen:
    """Mapping of agent listening addresses.

    Args:
        key (str): The key to retrieve the mapping for a specific agent.

    Returns:
        AgentListen: Mapping dictionary of agent listening addresses.
    """
    mapping: Dict[str, AgentListen] = {
        "user": {"topic": "events", "partition": 5, "identifier": "user"},
        "intent": {"topic": "events", "partition": 4, "identifier": "intent"},
        "super": {"topic": "events", "partition": 3, "identifier": "super"},
        "graph": {"topic": "events", "partition": 2, "identifier": "graph"},
        "output": {"topic": "events", "partition": 1, "identifier": "output"},
        "plan": {"topic": "events", "partition": 0, "identifier": "plan"},
        "recon": {"topic": "pt_events", "partition": 4, "identifier": "recon"},
        "attack": {"topic": "pt_events", "partition": 3, "identifier": "attack"},
        "browser": {"topic": "pt_events", "partition": 2, "identifier": "browser"},
        "search": {"topic": "pt_events", "partition": 1, "identifier": "search"},
        "tool": {"topic": "pt_events", "partition": 0, "identifier": "tool"},
    }

    if key not in mapping:
        raise ValueError(f"Invalid key: {key}. Valid keys are: {', '.join(mapping.keys())}")

    return mapping[key]
