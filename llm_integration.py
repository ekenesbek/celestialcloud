# llm_integration.py
import os

def call_external_llm(masked_text: str) -> str:
    """
    Вызывает внешнюю LLM (в нашем случае ChatGPT) и возвращает ответ.
    Пока — заглушка.
    """
    # Пример реального вызова к ChatGPT API:
    #
    # import openai
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    #
    # response = openai.ChatCompletion.create(
    #   model="gpt-3.5-turbo",
    #   messages=[{"role":"user", "content": masked_text}]
    # )
    # return response.choices[0].message["content"]

    return f"Имитированный ответ LLM для текста: '{masked_text}'"
