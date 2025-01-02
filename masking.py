import spacy
import re
from typing import Tuple, Dict

# Загружаем модель spaCy для русского
# nlp = spacy.load("ru_core_news_md")

import ru_core_news_md

nlp = ru_core_news_md.load()

def detect_and_mask(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Возвращает masked_text и token_map.
    - masked_text: текст с заменёнными на токены чувствительными фрагментами
    - token_map: словарь {token: original_value}
    """

    # 1. Создаём doc объект
    doc = nlp(text)

    # 2. Подготовим структуру для токенов
    token_map = {}
    token_count = 0
    masked_text = text

    # 3. Соберём span’ы (персональные данные, организации, адреса и т. п.)
    # Обратим внимание: если много сущностей, нужно их заменять с конца к началу,
    # чтобы не сбились индексы в строке
    entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)

    for ent in entities:
        if ent.label_ in ["PERSON", "ORG", "LOC", "GPE"]:
            token_count += 1
            token = f"#TOKEN_{token_count}#"
            original_value = ent.text
            token_map[token] = original_value

            start_idx = ent.start_char
            end_idx = ent.end_char
            masked_text = masked_text[:start_idx] + token + masked_text[end_idx:]

    # 4. Дополнительно обработаем «регулярками» номера паспорта РФ (упрощённый пример)
    # РПО: серия (4 цифры) + номер (6 цифр).
    # Важно: после замены spaCy индексы могли сдвинуться, поэтому здесь используем отдельный подход.
    # Можно использовать отдельный вызов detect_and_mask_regex() или что-то подобное.
    masked_text, token_map = detect_and_mask_inn(masked_text, token_map)
    masked_text, token_map = detect_and_mask_passport(masked_text, token_map)
    masked_text, token_map = detect_and_mask_credit_card(masked_text, token_map)

    return masked_text, token_map

def detect_and_mask_passport(text: str, token_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Находит конструкции типа 'паспорт 1234 567890' и заменяет их на токены.
    """
    pattern = r"(паспорт\s?\d{4}\s?\d{6})"
    # Проходим по всем совпадениям
    def replace_func(match):
        match_text = match.group(1)
        # Ищем, нет ли уже такого текства в token_map
        for k, v in token_map.items():
            if v == match_text:
                return k
        # Если нет, создаём новый токен
        new_token = f"#TOKEN_{len(token_map) + 1}#"
        token_map[new_token] = match_text
        return new_token

    new_text = re.sub(pattern, replace_func, text)
    return new_text, token_map

def detect_and_mask_inn(text: str, token_map: dict) -> (str, dict):
    """
    Ищем ИНН: обычно 10 или 12 цифр (в зависимости от типа).
    Для упрощения будем считать любой блок из 10 цифр, 
    перед которым написано 'ИНН' или 'ИНН:'.
    """
    pattern = r"(ИНН\s?\d{10,12})"

    def replace_func(match):
        match_text = match.group(1)
        # проверяем, есть ли уже в token_map
        for k, v in token_map.items():
            if v == match_text:
                return k
        new_token = f"#TOKEN_{len(token_map) + 1}#"
        token_map[new_token] = match_text
        return new_token

    new_text = re.sub(pattern, replace_func, text)
    return new_text, token_map


def detect_and_mask_credit_card(text: str, token_map: dict) -> (str, dict):
    """
    Ищем классическую 16-значную карту (Visa/MasterCard) в формате 
    'dddd dddd dddd dddd' или 'dddd-dddd-dddd-dddd' и т.п.
    """
    # Упростим: ищем 16 цифр в группах по 4
    pattern = r"(\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b)"

    def replace_func(match):
        match_text = match.group(1)
        for k, v in token_map.items():
            if v == match_text:
                return k
        new_token = f"#TOKEN_{len(token_map) + 1}#"
        token_map[new_token] = match_text
        return new_token

    new_text = re.sub(pattern, replace_func, text)
    return new_text, token_map
