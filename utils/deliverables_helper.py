import json
from typing import List, Dict, Union

def format_deliverables(deliverables: Union[str, List[Dict]]) -> str:
    """
    Convert deliverables to formatted string for display
    Supports both old format (comma-separated) and new format (JSON)
    """
    if not deliverables:
        return "• Digital product delivery"
    
    # Try to parse as JSON first
    if isinstance(deliverables, str):
        try:
            deliverables_list = json.loads(deliverables)
            if isinstance(deliverables_list, list):
                formatted = []
                for item in deliverables_list:
                    if isinstance(item, dict):
                        # New format: dict with item, type, details
                        emoji = get_type_emoji(item.get('type', ''))
                        formatted.append(f"{emoji} {item['item']}")
                    else:
                        # Fallback for simple strings in list
                        formatted.append(f"• {item}")
                return "\n".join(formatted)
        except json.JSONDecodeError:
            # Old format: comma-separated string
            items = deliverables.split(',')
            return "\n".join(f"• {item.strip()}" for item in items)
    
    return "• Digital product delivery"

def get_type_emoji(item_type: str) -> str:
    """Get emoji based on deliverable type"""
    emoji_map = {
        'code': '🔑',
        'account': '👤',
        'file': '📁',
        'link': '🔗',
        'guide': '📖',
        'support': '💬',
        'service': '⚡',
        'warranty': '🛡️',
        'key': '🔐'
    }
    return emoji_map.get(item_type.lower(), '✓')

def create_deliverables_json(items: List[Dict[str, str]]) -> str:
    """
    Create JSON string from deliverables list
    Example: [{"item": "Code", "type": "code"}, {"item": "Guide", "type": "guide"}]
    """
    return json.dumps(items)

# Example usage for new products:
EXAMPLE_DELIVERABLES = [
    {"item": "Discord Nitro Gift Link", "type": "code"},
    {"item": "Activation instructions", "type": "guide"},
    {"item": "24/7 Support", "type": "support"}
]
