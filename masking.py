import spacy
import re
from typing import Tuple, Dict
import ru_core_news_md

nlp = ru_core_news_md.load()

def detect_and_mask(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Возвращает masked_text и token_map.
    - masked_text: текст с заменёнными на токены чувствительными фрагментами
    - token_map: словарь {token: original_value}
    """

    # Cоздаём doc объект
    doc = nlp(text)

    # Подготовим структуру для токенов
    token_map = {}
    masked_text = text

    # Маскируем сущности, распознанные spaCy (PERSON, LOC, ORG и т.д.)
    masked_text, token_map = mask_spacy_entities(doc, masked_text, token_map)

    # Регулярные выражения для дополнительных данных
    masked_text, token_map = detect_and_mask_passport(masked_text, token_map)
    masked_text, token_map = detect_and_mask_credit_card(masked_text, token_map)
    masked_text, token_map = detect_and_mask_kz_iban(masked_text, token_map)
    masked_text, token_map = detect_and_mask_financial_amounts(masked_text, token_map)
    masked_text, token_map = detect_and_mask_kz_docs(masked_text, token_map)

    return masked_text, token_map

def mask_spacy_entities(doc, text: str, token_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Маскируем сущности, распознанные spaCy (PERSON, LOC, ORG и т.д.).
    """
    entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)
    masked_text = text
    token_count = len(token_map)

    for ent in entities:
        if ent.label_ in ["PERSON", "LOC", "GPE", "ORG"]:
            token_count += 1
            token_key = f"#TOKEN_{token_count}#"
            token_map[token_key] = ent.text
            start_idx, end_idx = ent.start_char, ent.end_char
            masked_text = masked_text[:start_idx] + token_key + masked_text[end_idx:]

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

def detect_and_mask_kz_iban(text: str, token_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Ищем казахстанские IBAN: формат обычно: 'KZxx xxxx xxxx xxxx xxxx'
    В общем случае IBAN = 20 символов (2 буквы + 18 цифр), 
    но встречаются и варианты с буквами и т. п.
    Для MVP упрощаем до: KZ + 16..20 символов (цифры/буквы).
    """
    # Упрощённый паттерн: 'KZ' + 18 символов (цифр/букв). 
    # Можно варьировать:
    pattern = r"(KZ[A-Za-z0-9]{16,18})"

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

def detect_and_mask_financial_amounts(text: str, token_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Маскируем суммы денег: числа с единицами (млн, млрд, тенге, долларов и т.д.).
    """
    # Шаблон для чисел с единицами измерения
    pattern = r"(\b\d+(?:\s?[,.]?\d+)*\s?(?:млн|млрд|тыс|тенге|руб|долларов|евро|₽|$|€)\b)"

    def replace_func(match):
        match_text = match.group(1)
        for k, v in token_map.items():
            if v == match_text:
                return k  # Уже существует токен для этого текста
        new_token = f"#TOKEN_{len(token_map) + 1}#"
        token_map[new_token] = match_text
        return new_token

    new_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
    return new_text, token_map

def detect_and_mask_kz_docs(text: str, token_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    """
    Находит и маскирует 12-значные номера для 'ИИН', 'БИН', 'BIN'.
    При этом сохраняет сам префикс (ИИН/БИН) и слово 'компании', 
    а маскирует только цифры.
    
    Примеры:
      - "ИИН 123456789012" -> "ИИН #TOKEN_1#"
      - "БИН компании 123456789012" -> "БИН компании #TOKEN_2#"
      - "BIN 123456789012" -> "BIN #TOKEN_3#"
    """

    pattern = r"(?i)\b(?P<doc_type>(?:ИИН|БИН|BIN))(?P<company>\s+компании)?\s+(?P<digits>\d{12})\b"
    # (?i) — флаг ignorecase, чтобы обрабатывать 'бин'/'Bin'/'БИН' и т.д. 
    # \b — граница слова, чтобы отделяться от текста

    def replace_func(match):
        # Захватываем группы
        doc_type = match.group("doc_type")      # 'ИИН' или 'БИН' или 'BIN'
        company_part = match.group("company")   # либо None, либо ' компании'
        digits = match.group("digits")          # '123456789012'
        
        # Если в token_map уже есть эти цифры, вернём соответствующий токен
        for token_key, original_val in token_map.items():
            if original_val == digits:
                # уже замаскировано
                # формируем "doc_type + company_part + token_key"
                return doc_type + (company_part if company_part else "") + " " + token_key
        
        # Генерируем новый токен для чисел
        new_token = f"#TOKEN_{len(token_map) + 1}#"
        token_map[new_token] = digits  # сохраняем именно цифры
        
        # Возвращаем строку: "doc_type + [компании] + пробел + Токен"
        return doc_type + (company_part if company_part else "") + " " + new_token

    new_text = re.sub(pattern, replace_func, text)
    return new_text, token_map
