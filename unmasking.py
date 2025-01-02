# unmasking.py
from typing import Dict

def unmask_text(masked_text: str, token_map: Dict[str, str]) -> str:
    """
    Заменяем в тексте токены обратно на исходные значения.
    """
    final_text = masked_text
    for token, original_value in token_map.items():
        final_text = final_text.replace(token, original_value)
    return final_text
