import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from masking import detect_and_mask
from unmasking import unmask_text
from llm_integration import call_external_llm

app = FastAPI(
    title="Secure ChatGPT Proxy MVP",
    description="MVP для безопасной передачи запросов в LLM",
    version="0.1.0"
)

# Для авторизации/аутентификации — пока упрощённая схема
class AuthData(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(auth_data: AuthData):
    # Простейшая проверка
    if auth_data.username == "admin" and auth_data.password == "admin123":
        return {"sessionToken": "test_session_token_12345"}
    else:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

# Модель данных для запроса чата
class ChatRequest(BaseModel):
    userQuery: str
    sessionToken: str

@app.post("/chat/query")
def chat_query(request: ChatRequest):
    # 1. Проверяем sessionToken (MVP-версия, без реальных проверок)
    if request.sessionToken != "test_session_token_12345":
        return JSONResponse(status_code=403, content={"error": "Invalid session token"})

    # 2. Детектируем и маскируем чувствительные данные
    masked_text, token_map = detect_and_mask(request.userQuery)

    # 3. Вызываем внешнюю LLM (здесь — заглушка)
    llm_response = call_external_llm(masked_text)

    # 4. Размаскировываем ответ
    final_response = unmask_text(llm_response, token_map)

    return {
        "maskedQuery": masked_text,
        "aiResponse": llm_response,
        "finalResponse": final_response
    }

@app.post("/chat/upload")
async def chat_upload(file: UploadFile, sessionToken: str = Form(...)):
    # 1. Проверяем токен (MVP)
    if sessionToken != "test_session_token_12345":
        return JSONResponse(status_code=403, content={"error": "Invalid session token"})
    
    # 2. Читаем содержимое файла
    file_bytes = await file.read()
    # Допустим, для упрощения считаем, что файл — простой txt
    # Или нужно подключать парсер (PyPDF2, python-docx, Apache Tika и т.д.)
    text_content = file_bytes.decode("utf-8", errors="ignore")

    # 3. Детект и маскировка
    masked_text, token_map = detect_and_mask(text_content)

    # 4. Запрос к LLM
    llm_response = call_external_llm(masked_text)

    # 5. Размаскировка
    final_response = unmask_text(llm_response, token_map)

    return {
        "maskedQuery": masked_text,
        "aiResponse": llm_response,
        "finalResponse": final_response
    }

@app.get("/health")
def health_check():
    return {
        "status": "OK",
        "version": app.version
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
