import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Конфигурация
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ============================================================
# 1. ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ ФАЙЛОВ
# ============================================================
def extract_text_from_docx(filepath):
    """Извлекает текст из .docx"""
    try:
        import docx
        doc = docx.Document(filepath)
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Ошибка при извлечении текста из DOCX: {e}"

def extract_text_from_pdf(filepath):
    """Извлекает текст из .pdf"""
    try:
        import pdfplumber
        text = ''
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text
    except Exception as e:
        return f"Ошибка при извлечении текста из PDF: {e}"

def extract_text(filepath, ext):
    """Выбирает нужный экстрактор"""
    if ext == 'docx':
        return extract_text_from_docx(filepath)
    elif ext == 'pdf':
        return extract_text_from_pdf(filepath)
    else:
        return "Неподдерживаемый формат"

# ============================================================
# 2. ОТПРАВКА В OPENROUTER
# ============================================================
def analyze_document_with_openrouter(text, check_id, check_question, api_key):
    """
    Отправляет текст документа в OpenRouter для проверки конкретного пункта чек-листа
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""
Ты — эксперт по комплаенсу. Проверь, соответствует ли загруженный документ требованию из чек-листа.

Требование:
ID: {check_id}
Вопрос: {check_question}

Инструкция:
1. Проанализируй текст документа.
2. Ответь на вопрос: выполняется ли это требование?
3. Дай один из ответов: "YES", "NO" или "PARTIAL".
4. Если ответ "YES" — приведи цитату из документа, которая это подтверждает.
5. Если ответ "NO" — объясни, что именно отсутствует.
6. Если ответ "PARTIAL" — объясни, что есть, а чего не хватает.

Текст документа:
{text[:8000]}

Верни ТОЛЬКО JSON в формате:
{{
    "answer": "YES|NO|PARTIAL",
    "evidence": "цитата из документа или пояснение",
    "confidence": 0.0-1.0
}}
"""

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [
            {"role": "system", "content": "Ты помощник, который отвечает только в формате JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 800
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        if response.status_code != 200:
            return {
                "answer": "NO",
                "evidence": f"Ошибка OpenRouter: {response.status_code}",
                "confidence": 0.0
            }

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Извлекаем JSON из ответа
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return json.loads(content)

    except Exception as e:
        return {
            "answer": "NO",
            "evidence": f"Ошибка: {str(e)}",
            "confidence": 0.0
        }

# ============================================================
# 3. API ЭНДПОИНТЫ
# ============================================================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/check_document', methods=['POST'])
def check_document():
    """
    Проверяет загруженный документ по указанному пункту чек-листа
    """
    # Проверяем, есть ли файл
    if 'file' not in request.files:
        return jsonify({"error": "Файл не загружен"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    # Проверяем расширение
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Неподдерживаемый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Получаем данные из формы
    check_id = request.form.get('check_id', 'UPD_002')
    check_question = request.form.get('check_question', 'Обновляете ли вы информацию не реже 1 раза в год?')
    api_key = request.form.get('api_key')

    if not api_key:
        return jsonify({"error": "Не передан API-ключ OpenRouter"}), 400

    # Сохраняем файл
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Извлекаем текст
        text = extract_text(filepath, ext)

        if len(text.strip()) < 50:
            return jsonify({
                "error": "Извлечено мало текста. Возможно, файл содержит только изображения или таблицы."
            }), 400

        # Отправляем в OpenRouter
        result = analyze_document_with_openrouter(text, check_id, check_question, api_key)

        # Формируем понятный ответ для пользователя
        answer_map = {
            "YES": "✅ Да",
            "NO": "❌ Нет",
            "PARTIAL": "⚠️ Частично"
        }

        return jsonify({
            "check_id": check_id,
            "question": check_question,
            "answer": result.get('answer', 'NO'),
            "answer_display": answer_map.get(result.get('answer', 'NO'), '❌ Нет'),
            "evidence": result.get('evidence', ''),
            "confidence": result.get('confidence', 0.0),
            "document_text_preview": text[:500] + "..."
        })

    except Exception as e:
        return jsonify({"error": f"Ошибка обработки: {str(e)}"}), 500
    finally:
        # Удаляем временный файл
        try:
            os.remove(filepath)
        except:
            pass

# ============================================================
# 4. ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print("🚀 Запуск сервера на http://localhost:5000")
    print("   Endpoint: POST /api/check_document")
    print("   Health: GET /api/health")
    app.run(debug=True, host='0.0.0.0', port=5000)