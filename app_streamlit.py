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
# 2. АНАЛИЗ ЧЕРЕЗ OPENROUTER (НОВЫЙ ПРОМПТ)
# ============================================================
def analyze_document_with_openrouter(text, api_key):
    """
    Отправляет текст в OpenRouter для проверки пункта UPD_002
    Возвращает русский текст с обоснованием
    """
    
    if not api_key or api_key == "sk-or-v1-...":
        return {
            "answer": "Н/Д",
            "evidence": "❌ API-ключ не указан. Вставьте ключ в код или введите в интерфейсе.",
            "confidence": 0.0
        }

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""
Ты — эксперт по комплаенсу и AML (противодействие легализации доходов).

Твоя задача — проверить, соответствует ли загруженный документ требованию из чек-листа. 
Ответ должен быть понятным для юриста или комплаенс-менеджера, без технического жаргона.

=== ЧТО ПРОВЕРЯЕМ ===
Пункт чек-листа: UPD_002 — Обновление информации о бенефициарных владельцах

Суть требования:
Юридическое лицо обязано регулярно обновлять информацию о своих бенефициарных владельцах. 
Обновление должно проводиться не реже одного раза в год, а также при любом изменении сведений о бенефициарах.

Что именно нужно подтвердить в документе:
1. Компания обновляет информацию о бенефициарных владельцах
2. Обновление проводится не реже 1 раза в год
3. Информация документально фиксируется

Кто должен выполнять: Юридическое лицо (сама компания)

=== ТЕКСТ НОРМЫ ===
Юридическое лицо обязано регулярно, но не реже одного раза в год либо в случае изменения сведений обновлять информацию о своих бенефициарных владельцах и документально фиксировать полученную информацию.

=== ДОКУМЕНТ ПОЛЬЗОВАТЕЛЯ ===
{text[:8000]}

=== ЧТО Я ИЩУ В ДОКУМЕНТЕ ===
Я анализирую документ по трём критериям:

1. КТО ВЫПОЛНЯЕТ ДЕЙСТВИЕ (субъект):
   — Должно быть: юридическое лицо (компания)
   — Может быть указано как: "Общество", "ООО", "Компания", "Организация", "Юридическое лицо"
   — Если в документе указано, что обновление проводит учредитель, директор или другое лицо от имени компании — это НЕПРАВИЛЬНЫЙ субъект
   — Если субъект не указан — отмечаю как "частично"

2. О ЧЁМ ИДЁТ РЕЧЬ (объект):
   — Должно быть: информация о бенефициарных владельцах
   — Это физические лица с долей >25% или те, кто контролирует компанию
   — Если речь идёт о сотрудниках, партнёрах или другой информации — это НЕПРАВИЛЬНЫЙ объект
   — Если объект не указан — отмечаю как "частично"

3. КАК ВЫПОЛНЯЕТСЯ (периодичность):
   — Должно быть: не реже 1 раза в год
   — "Ежегодно", "каждый год", "1 раз в год", "ежеквартально" (4 раза в год) — ЭТО ПРАВИЛЬНО
   — "Раз в 2 года", "по требованию", "в случае необходимости" — ЭТО НЕПРАВИЛЬНО
   — Если периодичность не указана — отмечаю как "частично"

=== ПРИМЕРЫ ПРАВИЛЬНЫХ И НЕПРАВИЛЬНЫХ ОТВЕТОВ ===

Правильно (ДА):
"В компании утверждён регламент, согласно которому информация о бенефициарных владельцах обновляется ежегодно." 
→ субъект: компания (✅), объект: бенефициары (✅), периодичность: ежегодно (✅)

Неправильно (НЕТ):
"Учредитель Иванов И.И. ежегодно обновляет сведения о сотрудниках организации."
→ субъект: учредитель (❌), объект: сотрудники (❌), периодичность: ежегодно (✅, но неважно)

Неправильно (НЕТ):
"Информация о бенефициарных владельцах проверяется по мере необходимости."
→ субъект: не указан (❌), объект: бенефициары (✅), периодичность: по мере необходимости (❌)

Частично (ЧАСТИЧНО):
"Компания проводит проверку данных о бенефициарных владельцах, но периодичность не установлена."
→ субъект: компания (✅), объект: бенефициары (✅), периодичность: не установлена (❌)

=== ИНСТРУКЦИЯ ПО ОТВЕТУ ===

Твой ответ должен быть на русском языке, понятным для юриста или менеджера по комплаенсу.

Структура ответа:

1. ОТВЕТ (одно слово): ДА / НЕТ / ЧАСТИЧНО
   — ДА — если все три критерия выполнены
   — НЕТ — если хотя бы один критерий не выполнен
   — ЧАСТИЧНО — если есть сомнения или неполные данные

2. ОБОСНОВАНИЕ: 2-3 предложения, почему такой ответ.

3. РАЗБОР ПО КРИТЕРИЯМ:
   — Субъект: (кто указан в документе) — ДА/НЕТ/ЧАСТИЧНО — (почему)
   — Объект: (что указано в документе) — ДА/НЕТ/ЧАСТИЧНО — (почему)
   — Периодичность: (что указано в документе) — ДА/НЕТ/ЧАСТИЧНО — (почему)

4. ЧТО НУЖНО СДЕЛАТЬ (если ответ НЕТ или ЧАСТИЧНО):
   — Конкретная рекомендация, что нужно исправить или добавить в документ

ВАЖНО:
- НЕ ПРИДУМЫВАЙ того, чего нет в документе.
- Если информации недостаточно — ставь ЧАСТИЧНО и объясни, чего не хватает.
- ОТВЕТ ДОЛЖЕН БЫТЬ НА РУССКОМ ЯЗЫКЕ.
- Только факты из документа, без домыслов.

=== ТЕПЕРЬ ТВОЙ ОТВЕТ ===
"""

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [
            {"role": "system", "content": "Ты — строгий эксперт по комплаенсу. Отвечаешь только на русском языке, структурированно, без технического жаргона."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 1200
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        if response.status_code != 200:
            return {
                "answer": "Ошибка",
                "evidence": f"❌ Ошибка OpenRouter: {response.status_code}",
                "confidence": 0.0
            }

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Парсим ответ: извлекаем ДА/НЕТ/ЧАСТИЧНО
        answer = "Н/Д"
        if "ДА" in content.upper() and "ЧАСТИЧНО" not in content.upper():
            answer = "ДА"
        elif "НЕТ" in content.upper():
            answer = "НЕТ"
        elif "ЧАСТИЧНО" in content.upper():
            answer = "ЧАСТИЧНО"
        
        return {
            "answer": answer,
            "evidence": content,
            "confidence": 0.9
        }

    except Exception as e:
        return {
            "answer": "Ошибка",
            "evidence": f"❌ Ошибка: {str(e)}",
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
# 5. ДВЕ КОЛОНКИ: ЧЕК-ЛИСТ + ПРОВЕРКА ДОКУМЕНТА
# ============================================================
col_left, col_right = st.columns([3, 2], gap="large")

# ============================================================
# 5.1 ЛЕВАЯ КОЛОНКА — ЧЕК-ЛИСТ
# ============================================================
with col_left:
    st.subheader("📋 Чек-лист для оператора")
    st.caption("Отмечайте ответы вручную или загрузите документ справа для автоматической проверки")
    
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
                        format_func=lambda x: {'UNKNOWN': '❓', 'YES': '✅', 'NO': '❌', 'PARTIAL': '⚠️'}[x]
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
    
    # Кнопки управления внизу чек-листа
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📤 Экспорт JSON", use_container_width=True):
            export_data = {
                "article": checklist_data['article'],
                "title": checklist_data['title'],
                "law": checklist_data['law'],
                "exported_at": str(st.session_state.get('_timestamp', '')),
                "answers": st.session_state.answers
            }
            st.json(export_data)
            st.download_button(
                label="📥 Скачать",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name="checklist_results.json",
                mime="application/json"
            )
    with col_btn2:
        if st.button("🔄 Сбросить всё", use_container_width=True):
            st.session_state.answers = {}
            if 'last_result' in st.session_state:
                del st.session_state['last_result']
            st.rerun()

# ============================================================
# 5.2 ПРАВАЯ КОЛОНКА — ПРОВЕРКА ДОКУМЕНТА
# ============================================================
with col_right:
    st.subheader("📎 Проверка документа")
    st.caption("Загрузите документ для проверки по пункту UPD_002")
    
    # Информация о пункте
    with st.expander("📌 Что проверяется", expanded=True):
        st.markdown("""
        **Пункт:** UPD_002 — Обновление информации о бенефициарных владельцах
        
        **Суть требования:**
        Юридическое лицо обязано регулярно обновлять информацию о своих бенефициарных владельцах.
        Обновление должно проводиться **не реже одного раза в год**, а также при любом изменении сведений.
        
        **Что должно быть в документе:**
        - Приказ или регламент об обновлении сведений о бенефициарах
        - Указание на периодичность: не реже 1 раза в год
        - Документальное фиксирование полученной информации
        """)
    
    # API-ключ
    api_key_input = st.text_input(
        "🔑 API-ключ OpenRouter",
        value=OPENROUTER_API_KEY if OPENROUTER_API_KEY != "sk-or-v1-..." else "",
        placeholder="sk-or-v1-...",
        type="password",
        help="Получить ключ на https://openrouter.ai/keys"
    )
    
    if OPENROUTER_API_KEY != "sk-or-v1-..." and not api_key_input:
        api_key_input = OPENROUTER_API_KEY
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        "📂 Загрузите документ (.docx или .pdf)",
        type=["docx", "pdf"],
        help="Поддерживаются файлы в формате .docx и .pdf"
    )
    
    # Кнопка проверки
    if uploaded_file:
        st.success(f"✅ Файл загружен: {uploaded_file.name}")
        
        if st.button("🔍 Проверить документ", type="primary", use_container_width=True):
            with st.spinner("⏳ Анализируем документ (до 30 секунд)..."):
                file_bytes = uploaded_file.getvalue()
                file_type = uploaded_file.name.split('.')[-1].lower()
                text = extract_text(file_bytes, file_type)
                
                if len(text.strip()) < 20:
                    st.error("❌ Извлечено мало текста. Возможно, файл содержит только изображения или таблицы.")
                else:
                    # Анализируем через OpenRouter
                    result = analyze_document_with_openrouter(text, api_key_input)
                    
                    # Сохраняем результат
                    st.session_state['last_result'] = result
                    st.rerun()
    else:
        st.info("📂 Загрузите файл для проверки")
    
    # ============================================================
    # ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА
    # ============================================================
    if 'last_result' in st.session_state:
        result = st.session_state['last_result']
        
        st.markdown("---")
        st.subheader("📊 Результат проверки")
        
        # Цвет ответа
        answer_colors = {
            "ДА": "🟢",
            "НЕТ": "🔴",
            "ЧАСТИЧНО": "🟡",
            "Н/Д": "⚪",
            "Ошибка": "⚪"
        }
        
        # Показываем ответ крупно
        st.markdown(f"""
        <div style="text-align:center; padding:20px; border-radius:10px; background:#f0f2f6; margin-bottom:15px;">
            <span style="font-size:48px;">{answer_colors.get(result.get('answer', 'Н/Д'), '⚪')}</span>
            <h2 style="margin:0; color:#1a1a2e;">{result.get('answer', 'Н/Д')}</h2>
            <span style="color:#64748b; font-size:14px;">Уверенность: {int(result.get('confidence', 0)*100)}%</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Показываем полный ответ
        st.markdown(result.get('evidence', 'Нет данных'))
        
        # Кнопка очистки
        if st.button("🔄 Очистить результат", use_container_width=True):
            del st.session_state['last_result']
            st.rerun()
    
       # Автоматическое заполнение чек-листа при получении результата
    if 'last_result' in st.session_state:
        result = st.session_state['last_result']
        answer_map = {"ДА": "YES", "НЕТ": "NO", "ЧАСТИЧНО": "PARTIAL"}
        if result.get('answer') in answer_map:
            st.session_state.answers["UPD_002"] = answer_map[result.get('answer')]
