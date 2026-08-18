cat > app_streamlit.py <<'EOF'
import streamlit as st
import os
import json
import requests
import re
from io import BytesIO

# ============================================================
# ⚠️ ВСТАВЬ СВОЙ API-КЛЮЧ СЮДА ДЛЯ ТЕСТА
# ============================================================
OPENROUTER_API_KEY = "sk-or-v1-..."  # ← ЗАМЕНИ НА СВОЙ КЛЮЧ
# ============================================================

# Конфигурация
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# 1. ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ ФАЙЛОВ
# ============================================================
def extract_text_from_docx(file_bytes):
    """Извлекает текст из .docx"""
    try:
        import docx
        from io import BytesIO
        doc = docx.Document(BytesIO(file_bytes))
        return '\n'.join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Ошибка при извлечении текста из DOCX: {e}"

def extract_text_from_pdf(file_bytes):
    """Извлекает текст из .pdf"""
    try:
        import pdfplumber
        from io import BytesIO
        text = ''
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return text
    except Exception as e:
        return f"Ошибка при извлечении текста из PDF: {e}"

def extract_text(file_bytes, file_type):
    """Выбирает нужный экстрактор"""
    if file_type == "docx":
        return extract_text_from_docx(file_bytes)
    elif file_type == "pdf":
        return extract_text_from_pdf(file_bytes)
    else:
        return "Неподдерживаемый формат"

# ============================================================
# 2. АНАЛИЗ ЧЕРЕЗ OPENROUTER
# ============================================================
def analyze_document_with_openrouter(text, check_id, check_question, api_key):
    """Отправляет текст в OpenRouter для проверки пункта чек-листа"""
    
    if not api_key or api_key == "sk-or-v1-...":
        return {
            "answer": "UNKNOWN",
            "evidence": "❌ API-ключ не указан. Вставьте ключ в код или введите в интерфейсе.",
            "confidence": 0.0
        }

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
# 3. ЗАГРУЗКА ЧЕК-ЛИСТА ИЗ JSON
# ============================================================
@st.cache_data
def load_checklist():
    """Загружает чек-лист из JSON-файла"""
    json_path = "research/115fz/checklists/article_6.1_checklist_v1.0.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ Файл не найден: {json_path}")
        return None

# ============================================================
# 4. ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================
st.set_page_config(
    page_title="Чек-лист по ст.6.1 115-ФЗ",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Чек-лист по статье 6.1 115-ФЗ")
st.caption("Обязанности юридического лица по раскрытию информации о своих бенефициарных владельцах")

# Загрузка чек-листа
checklist_data = load_checklist()
if not checklist_data:
    st.stop()

# Инициализация состояния
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# ============================================================
# 4.1 ПАНЕЛЬ ЗАГРУЗКИ
# ============================================================
with st.expander("📎 Загрузить документ для проверки", expanded=True):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Поле для API-ключа (можно ввести или использовать из кода)
        api_key_input = st.text_input(
            "🔑 API-ключ OpenRouter",
            value=OPENROUTER_API_KEY if OPENROUTER_API_KEY != "sk-or-v1-..." else "",
            placeholder="sk-or-v1-... (или оставьте ключ в коде)",
            type="password",
            help="Получить ключ на https://openrouter.ai/keys"
        )
        
        # Если ключ в коде не заполнен, используем введённый
        if OPENROUTER_API_KEY != "sk-or-v1-..." and not api_key_input:
            api_key_input = OPENROUTER_API_KEY
        
        uploaded_file = st.file_uploader(
            "📂 Загрузите документ (.docx или .pdf)",
            type=["docx", "pdf"],
            help="Поддерживаются файлы в формате .docx и .pdf"
        )
        
        # Выбор пункта чек-листа
        check_options = {
            "UPD_002": "Обновление не реже 1 раза в год",
            "BO_001": "Наличие информации о бенефициарных владельцах",
            "STR_003": "Хранение не менее 5 лет",
            "REQ_002": "Запрос у учредителей и участников",
            "AUTH_001": "Предоставление по запросу органов"
        }
        selected_check = st.selectbox(
            "📋 Выберите пункт чек-листа для проверки",
            options=list(check_options.keys()),
            format_func=lambda x: f"{x} — {check_options[x]}"
        )
    
    with col2:
        st.write("")
        st.write("")
        if uploaded_file:
            st.success(f"✅ Файл загружен:\n{uploaded_file.name}")
            if st.button("🔍 Проверить документ", type="primary", use_container_width=True):
                with st.spinner("⏳ Анализируем документ (до 30 секунд)..."):
                    # Получаем текст из файла
                    file_bytes = uploaded_file.getvalue()
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    text = extract_text(file_bytes, file_type)
                    
                    if len(text.strip()) < 50:
                        st.error("❌ Извлечено мало текста. Возможно, файл содержит только изображения или таблицы.")
                    else:
                        # Отправляем в OpenRouter
                        result = analyze_document_with_openrouter(
                            text, 
                            selected_check, 
                            check_options[selected_check],
                            api_key_input
                        )
                        
                        # Сохраняем результат
                        st.session_state['last_result'] = {
                            "check_id": selected_check,
                            "question": check_options[selected_check],
                            "answer": result.get('answer', 'UNKNOWN'),
                            "evidence": result.get('evidence', ''),
                            "confidence": result.get('confidence', 0.0)
                        }
                        
                        # Автоматически заполняем чек-лист
                        if result.get('answer') in ['YES', 'NO', 'PARTIAL']:
                            st.session_state.answers[selected_check] = result.get('answer')
                        
                        st.rerun()
        else:
            st.info("📂 Загрузите файл для проверки")

# ============================================================
# 4.2 ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА
# ============================================================
if 'last_result' in st.session_state:
    result = st.session_state['last_result']
    
    answer_map = {
        "YES": ("✅ ДА", "success"),
        "NO": ("❌ НЕТ", "error"),
        "PARTIAL": ("⚠️ ЧАСТИЧНО", "warning"),
        "UNKNOWN": ("❓ Н/Д", "info")
    }
    answer_text, answer_type = answer_map.get(result['answer'], ("❓ Н/Д", "info"))
    
    with st.container():
        st.markdown("---")
        st.subheader("📊 Результат проверки")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.metric("Ответ", answer_text)
        with col2:
            st.metric("Уверенность", f"{result['confidence']*100:.0f}%")
        with col3:
            st.metric("Пункт", result['check_id'])
        
        st.info(f"**📌 Обоснование:**\n\n{result['evidence']}")
        
        if st.button("🔄 Очистить результат"):
            del st.session_state['last_result']
            st.rerun()

# ============================================================
# 4.3 ЧЕК-ЛИСТ
# ============================================================
st.markdown("---")
st.subheader("📋 Чек-лист по статье 6.1")

# Прогресс
total = 0
answered = 0
for group in checklist_data['groups']:
    for check in group['checks']:
        total += 1
        if st.session_state.answers.get(check['id']) and st.session_state.answers[check['id']] != 'UNKNOWN':
            answered += 1

progress = answered / total if total > 0 else 0
st.progress(progress, text=f"Заполнено {answered}/{total} ({int(progress*100)}%)")

# Группы
for group in checklist_data['groups']:
    with st.expander(f"{group['name']} ({group['description']})"):
        for check in group['checks']:
            val = st.session_state.answers.get(check['id'], 'UNKNOWN')
            
            # Цвет статуса
            status_colors = {
                'YES': '🟢',
                'NO': '🔴',
                'PARTIAL': '🟡',
                'UNKNOWN': '⚪'
            }
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{status_colors.get(val, '⚪')} **{check['id']}** — {check['question']}")
            with col2:
                selected = st.selectbox(
                    "Ответ",
                    options=['UNKNOWN', 'YES', 'NO', 'PARTIAL'],
                    index=['UNKNOWN', 'YES', 'NO', 'PARTIAL'].index(val),
                    key=f"answer_{check['id']}",
                    label_visibility="collapsed",
                    format_func=lambda x: {'UNKNOWN': '❓ Н/Д', 'YES': '✅ Да', 'NO': '❌ Нет', 'PARTIAL': '⚠️ Частично'}[x]
                )
                if selected != val:
                    st.session_state.answers[check['id']] = selected
                    st.rerun()
            
            # Рекомендация
            if val == 'NO' and check.get('recommendation_if_no'):
                st.warning(f"💡 {check['recommendation_if_no']}")
            elif val == 'PARTIAL' and check.get('recommendation_if_partial'):
                st.warning(f"💡 {check['recommendation_if_partial']}")
            elif val == 'YES':
                st.success("✅ Всё в порядке.")

# ============================================================
# 4.4 ЭКСПОРТ
# ============================================================
with st.expander("📤 Экспорт результатов"):
    if st.button("📤 Экспортировать JSON"):
        export_data = {
            "article": checklist_data['article'],
            "title": checklist_data['title'],
            "law": checklist_data['law'],
            "exported_at": str(st.session_state.get('_timestamp', '')),
            "answers": st.session_state.answers
        }
        st.json(export_data)
        
        # Кнопка скачивания
        st.download_button(
            label="📥 Скачать JSON",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name="checklist_results.json",
            mime="application/json"
        )

# ============================================================
# 4.5 СБРОС
# ============================================================
if st.button("🔄 Сбросить все ответы", type="secondary"):
    st.session_state.answers = {}
    if 'last_result' in st.session_state:
        del st.session_state['last_result']
    st.rerun()

st.caption("💡 Данные сохраняются в сессии. При обновлении страницы они сбросятся.")
EOF