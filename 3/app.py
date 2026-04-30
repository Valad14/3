import streamlit as st
import pandas as pd
from lxml import etree
from lxml.builder import ElementMaker
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime
import io
import zipfile

# --- 1. НАСТРОЙКИ СТРАНИЦЫ И ЯРКИЙ ИНТЕРФЕЙС ---
st.set_page_config(
    page_title="Лингвистический компаратор",
    page_icon="🌈",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --corpus-pink: #ff4f9a;
        --corpus-orange: #ff9f1c;
        --corpus-yellow: #ffeb3b;
        --corpus-green: #00d084;
        --corpus-cyan: #00c2ff;
        --corpus-blue: #3b82f6;
        --corpus-purple: #8b5cf6;
        --corpus-dark: #24124d;
        --corpus-ink: #1f1147;
        --corpus-card: rgba(255, 255, 255, 0.92);
        --historic-font: 'Noto Serif', 'DejaVu Serif', 'Segoe UI Historic', 'Times New Roman', serif;
        --ui-font: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 5%, rgba(255, 235, 59, 0.38) 0, transparent 28%),
            radial-gradient(circle at 96% 7%, rgba(255, 79, 154, 0.26) 0, transparent 34%),
            linear-gradient(135deg, #fff7ad 0%, #ffd7f1 30%, #d8f8ff 64%, #efe3ff 100%);
        color: var(--corpus-ink);
        font-family: var(--ui-font);
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--corpus-dark);
        letter-spacing: -0.02em;
    }

    .hero-card {
        padding: 28px 32px;
        border-radius: 28px;
        color: white;
        background:
            linear-gradient(135deg, rgba(255,79,154,0.98), rgba(139,92,246,0.96) 48%, rgba(0,194,255,0.94));
        box-shadow: 0 26px 60px rgba(99, 49, 179, 0.28);
        border: 1px solid rgba(255, 255, 255, 0.55);
        margin-bottom: 1.1rem;
        position: relative;
        overflow: hidden;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        right: -80px;
        top: -90px;
        width: 260px;
        height: 260px;
        border-radius: 999px;
        background: rgba(255, 235, 59, 0.28);
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 4rem);
        font-weight: 900;
        line-height: 1.02;
        margin: 0 0 0.5rem 0;
    }

    .hero-subtitle {
        font-size: 1.08rem;
        max-width: 980px;
        line-height: 1.55;
        margin: 0;
        opacity: 0.96;
    }

    .bright-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }

    .bright-pill {
        display: inline-flex;
        align-items: center;
        padding: 8px 14px;
        border-radius: 999px;
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.36);
        backdrop-filter: blur(6px);
        font-weight: 700;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(255,79,154,0.96), rgba(139,92,246,0.95) 54%, rgba(0,194,255,0.92));
        color: white;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.16);
        border: 2px dashed rgba(255, 255, 255, 0.78);
        border-radius: 22px;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: rgba(255, 255, 255, 0.18) !important;
        border-color: rgba(255, 255, 255, 0.42) !important;
        color: white !important;
        border-radius: 16px !important;
    }

    [data-testid="stSidebar"] .stAlert {
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.35);
        border-radius: 16px;
    }

    section.main div[data-testid="stExpander"],
    div[data-testid="stMetric"],
    div[data-testid="stAlert"],
    div[data-testid="stDataEditor"],
    div[data-testid="stDataFrame"] {
        border-radius: 22px !important;
    }

    section.main div[data-testid="stExpander"],
    div[data-testid="stMetric"] {
        background: var(--corpus-card);
        border: 1px solid rgba(255,255,255,0.86);
        box-shadow: 0 18px 44px rgba(69, 40, 140, 0.12);
    }

    div[data-testid="stMetric"] {
        padding: 16px 18px;
        border-left: 8px solid var(--corpus-orange);
    }

    div[data-testid="stMetric"] label {
        color: var(--corpus-dark) !important;
        font-weight: 800;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--corpus-purple) !important;
        font-weight: 900;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"] {
        border: 0 !important;
        border-radius: 999px !important;
        color: white !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, var(--corpus-pink), var(--corpus-purple), var(--corpus-cyan)) !important;
        box-shadow: 0 14px 30px rgba(139, 92, 246, 0.32) !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        filter: saturate(1.14) brightness(1.05);
        box-shadow: 0 18px 40px rgba(255, 79, 154, 0.35) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.7);
        color: var(--corpus-dark);
        font-weight: 800;
    }

    [data-testid="stDataEditor"] div[role="grid"],
    [data-testid="stDataFrame"] div[role="grid"] {
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid rgba(139, 92, 246, 0.22);
        box-shadow: 0 20px 48px rgba(36, 18, 77, 0.12);
    }

    [data-testid="stDataEditor"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background: linear-gradient(135deg, var(--corpus-purple), var(--corpus-blue)) !important;
        color: white !important;
        font-weight: 900 !important;
    }

    [data-testid="stDataEditor"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th,
    .stDataFrame td,
    .dataframe td,
    .dataframe th {
        font-family: var(--historic-font) !important;
        font-size: 19px !important;
    }

    .big-word {
        font-family: var(--historic-font);
        font-size: 64px;
        color: var(--corpus-purple);
        padding: 20px;
        background: linear-gradient(135deg, #fff7ad, #ffd7f1);
        border-radius: 22px;
        text-align: center;
        border: 2px solid rgba(139, 92, 246, 0.45);
        margin: 15px 0;
        box-shadow: 0 20px 42px rgba(139, 92, 246, 0.16);
    }

    .context-box {
        background:
            linear-gradient(135deg, rgba(255,255,255,0.94), rgba(216,248,255,0.92));
        padding: 20px;
        border-radius: 22px;
        font-family: var(--historic-font);
        font-size: 20px;
        margin: 12px 0;
        border-left: 9px solid var(--corpus-cyan);
        box-shadow: 0 18px 40px rgba(0, 194, 255, 0.14);
        color: var(--corpus-ink);
    }

    .context-highlight {
        background: linear-gradient(135deg, var(--corpus-pink), var(--corpus-purple));
        color: white;
        padding: 4px 10px;
        border-radius: 999px;
        font-weight: 900;
        box-shadow: 0 10px 22px rgba(255, 79, 154, 0.23);
    }

    .stat-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(255,247,173,0.72));
        padding: 18px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.85);
        margin-bottom: 12px;
        box-shadow: 0 16px 36px rgba(255, 159, 28, 0.14);
    }

    .instruction-step {
        background: linear-gradient(135deg, rgba(216,248,255,0.92), rgba(239,227,255,0.92));
        padding: 16px;
        border-radius: 18px;
        margin: 10px 0;
        border-left: 7px solid var(--corpus-blue);
    }

    .instruction-note {
        background: linear-gradient(135deg, rgba(255,235,59,0.36), rgba(255,215,241,0.72));
        padding: 16px;
        border-radius: 18px;
        margin: 10px 0;
        border-left: 7px solid var(--corpus-orange);
    }

    .status-badge {
        display: inline-flex;
        padding: 5px 12px;
        border-radius: 999px;
        font-weight: 900;
        background: linear-gradient(135deg, var(--corpus-green), var(--corpus-cyan));
        color: white;
        box-shadow: 0 10px 22px rgba(0, 208, 132, 0.22);
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--corpus-pink), var(--corpus-orange), var(--corpus-green), var(--corpus-cyan), var(--corpus-purple)) !important;
    }

    hr {
        border: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(139,92,246,0.58), transparent);
        margin: 1.8rem 0;
    }

    * {
        font-feature-settings: "liga" 1, "dlig" 1;
        text-rendering: optimizeLegibility;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- 2. ФУНКЦИЯ ПОЛНОЙ ЗАМЕНЫ ТИТЛОВ ---
def remove_titles(text):
    """
    ПОЛНОЕ УДАЛЕНИЕ ВСЕХ ТИТЛОВ И ЗАМЕНА ИХ НА ОБЫЧНЫЕ БУКВЫ
    """
    if not text:
        return text

    # Таблица замены титлов на буквы
    title_replacements = {
        'аⷣ': 'а', 'бⷣ': 'б', 'вⷣ': 'в', 'гⷣ': 'г', 'дⷣ': 'д',
        'еⷣ': 'е', 'жⷣ': 'ж', 'зⷣ': 'з', 'иⷣ': 'и', 'іⷣ': 'і',
        'кⷣ': 'к', 'лⷣ': 'л', 'мⷣ': 'м', 'нⷣ': 'н', 'оⷣ': 'о',
        'пⷣ': 'п', 'рⷣ': 'р', 'сⷣ': 'с', 'тⷣ': 'т', 'уⷣ': 'у',
        'фⷣ': 'ф', 'хⷣ': 'х', 'цⷣ': 'ц', 'чⷣ': 'ч', 'шⷣ': 'ш',
        'щⷣ': 'щ', 'ъⷣ': 'ъ', 'ыⷣ': 'ы', 'ьⷣ': 'ь', 'ѣⷣ': 'ѣ',
        'юⷣ': 'ю', 'яⷣ': 'я', 'ѧⷣ': 'ѧ', 'ѩⷣ': 'ѩ',
        'ⷢ҇': 'г', 'ⷭ҇': 'с', 'ⷣ҇': 'д', 'ⷡ҇': 'в', 'ⷦ҇': 'л',
        'ⷪ҇': 'о', 'ⷫ҇': 'п', 'ⷬ҇': 'р', 'ⷮ҇': 'т',
        'ⷯ҇': 'у', 'ⷴ҇': 'ц', 'ⷵ҇': 'ч', 'ⷹ҇': 'ѧ',
        '\u0483': '', '\u0484': '', '\u0485': '', '\u0486': '', '\u0487': '',
        '\u0300': '', '\u0301': '', '\u0302': '', '\u0303': '', '\u0304': '',
        '\u0306': '', '\u0307': '', '\u0308': '', '\u030A': '', '\u030B': '',
        '\u030C': '', '\u0331': '',
    }

    for old, new in title_replacements.items():
        text = text.replace(old, new)

    text = re.sub(r'[\u0300-\u036f\u0483-\u0489]', '', text)
    return text


def normalize_text(text):
    """Нормализация текста"""
    if not text:
        return ""

    text = text.lower()
    replacements = {
        'ѣ': 'е', 'ѳ': 'ф', 'ѵ': 'и', 'ѡ': 'о',
        '́': '', '̀': '', '̑': '', '҃': '',
        'ъ': 'ъ', 'ь': 'ь',
        'ꙗ': 'я', 'ѥ': 'е', 'ѕ': 'з',
        'ѯ': 'кс', 'ѱ': 'пс', 'ѿ': 'от',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def phonetic_normalize(text):
    """Фонетическая нормализация"""
    if not text:
        return ""

    text = normalize_text(text)
    replacements = {'о': 'а', 'е': 'и', 'я': 'а', 'ю': 'у'}

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def edit_distance_similarity(s1, s2):
    """Вычисление схожести строк"""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


# --- 3. ПАРСИНГ XML ---
def parse_xml_tei(file):
    raw = file.read()
    try:
        try:
            content = raw.decode('utf-16')
        except Exception:
            content = raw.decode('utf-8')

        content = re.sub(
            r'<\?xml[^>]+encoding=["\']UTF-16["\'][^>]*\?>',
            '<?xml version="1.0" encoding="UTF-8"?>',
            content,
            count=1,
        )

        root = etree.fromstring(content.encode('utf-8'), parser=etree.XMLParser(recover=True))
        words = []

        for w in root.xpath('.//*[local-name()="w"]'):
            word_id = w.get('{http://www.w3.org/XML/1998/namespace}id') or w.get('id', 'n/a')
            lemma = (w.get('lemma') or "").strip().lower()
            text = unicodedata.normalize('NFC', "".join(w.xpath('text()')).strip())
            text = remove_titles(text)

            morph = {}
            for f in w.xpath('.//*[local-name()="f"]'):
                name = f.get('name')
                sym_vals = f.xpath('.//*[local-name()="symbol"]/@value')
                if name and sym_vals:
                    morph[name] = sym_vals[0].strip()

            if text:
                words.append({
                    'id': word_id,
                    'surface': text,
                    'lemma': lemma,
                    'morph': morph,
                    'normalized': normalize_text(text),
                    'phonetic': phonetic_normalize(text),
                })

        return words

    except Exception as e:
        st.error(f"Ошибка в файле {file.name}: {e}")
        return []


# --- 4. АЛГОРИТМ ВЫРАВНИВАНИЯ ---
def similarity_score(w1, w2):
    if not w1 or not w2:
        return -4

    if w1['normalized'] == w2['normalized']:
        return 10

    if w1['lemma'] == w2['lemma'] and w1['lemma']:
        if w1['morph'] == w2['morph']:
            return 8

    if w1['lemma'] == w2['lemma'] and w1['lemma']:
        return 6

    if w1['phonetic'] == w2['phonetic']:
        return 5

    similarity = edit_distance_similarity(w1['normalized'], w2['normalized'])
    if similarity >= 0.8:
        return 3
    elif similarity >= 0.65:
        return 1

    return -4


def align_pair(base_list, target_list):
    n, m = len(base_list), len(target_list)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i * -2

    for j in range(m + 1):
        dp[0][j] = j * -2

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match_score = similarity_score(base_list[i - 1], target_list[j - 1])
            dp[i][j] = max(
                dp[i - 1][j - 1] + match_score,
                dp[i - 1][j] - 2,
                dp[i][j - 1] - 2,
            )

    matches = {}
    i, j = n, m
    while i > 0 and j > 0:
        current_score = dp[i][j]
        match_score = similarity_score(base_list[i - 1], target_list[j - 1])

        if current_score == dp[i - 1][j - 1] + match_score:
            matches[i - 1] = target_list[j - 1]
            i -= 1
            j -= 1
        elif current_score == dp[i - 1][j] - 2:
            matches[i - 1] = None
            i -= 1
        else:
            j -= 1

    return matches


# --- 5. КЛАССИФИКАЦИЯ ---
def classify_variant(main_word, witness_word):
    if not main_word or not witness_word:
        return "Пропуск"

    if main_word['normalized'] == witness_word['normalized']:
        if main_word['surface'] == witness_word['surface']:
            return "Идентично"
        else:
            return "Графическое"

    if main_word['phonetic'] == witness_word['phonetic']:
        return "Фонетическое"

    if main_word['lemma'] == witness_word['lemma'] and main_word['lemma']:
        if main_word['morph'] != witness_word['morph']:
            return "Морфологическое"
        else:
            return "Графическое"

    similarity = edit_distance_similarity(main_word['normalized'], witness_word['normalized'])
    if similarity >= 0.62:
        return "Графическое"

    return "Лексическое"


def get_context(words, index, context_size=10):
    start = max(0, index - context_size)
    end = min(len(words), index + context_size + 1)
    context_before = words[start:index]
    context_after = words[index + 1:end]
    return context_before, context_after


# --- 6. ЭКСПОРТ В XML-TEI ---
def export_aligned_xml(base_words, aligned_words, base_filename, target_filename, variant_types):
    """
    Экспорт выровненных списков в формат XML-TEI
    """
    E = ElementMaker(
        namespace="http://www.tei-c.org/ns/1.0",
        nsmap={None: "http://www.tei-c.org/ns/1.0"},
    )

    # Создаем TEI структуру
    tei = E.TEI(
        E.teiHeader(
            E.fileDesc(
                E.titleStmt(
                    E.title(f"Выровненный корпус: {base_filename} ↔ {target_filename}")
                ),
                E.publicationStmt(E.p("Создано Лингвистическим компаратором")),
                E.sourceDesc(
                    E.p(f"Основано на: {base_filename} и {target_filename}")
                ),
            ),
            E.encodingDesc(
                E.classDecl(
                    E.taxonomy(
                        E.category(
                            E.catDesc("Лингвистический компаратор - выровненный корпус")
                        )
                    )
                )
            ),
        ),
        E.text(
            E.body(
                E.div(
                    E.head("Выровненные тексты"),
                    type="aligned_corpus",
                )
            )
        ),
    )

    # Создаем AB элемент для выровненного текста
    ab = E.ab()

    # Добавляем информацию о выравнивании
    ab.append(E.note("Выравнивание выполнено алгоритмом Нидлмана-Вунша"))
    ab.append(E.note(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))

    # Добавляем выровненные слова
    for i, (base_word, aligned_word) in enumerate(zip(base_words, aligned_words)):
        # Создаем группу выравнивания
        alignment_group = E.milestone(unit="alignment", n=str(i))
        ab.append(alignment_group)

        # Базовое слово
        base_elem = E.w(
            base_word['surface'],
            xml_id=base_word['id'],
            lemma=base_word['lemma'],
            type="base",
        )

        # Добавляем морфологическую информацию
        for morph_name, morph_value in base_word['morph'].items():
            base_elem.append(E.fs(E.f(E.symbol(morph_value), name=morph_name)))

        ab.append(base_elem)

        # Целевое слово (если есть)
        if aligned_word:
            target_elem = E.w(
                aligned_word['surface'],
                xml_id=aligned_word['id'],
                lemma=aligned_word['lemma'],
                type="target",
                variant=variant_types.get(i, "unknown"),
            )
            for morph_name, morph_value in aligned_word['morph'].items():
                target_elem.append(E.fs(E.f(E.symbol(morph_value), name=morph_name)))
            ab.append(target_elem)
        else:
            # Если слово отсутствует в целевом тексте
            ab.append(E.w("---", type="missing", variant="Пропуск"))

        # Разделитель между парами
        ab.append(E.pc(" "))

    # Добавляем AB в тело документа
    tei.find('.//{http://www.tei-c.org/ns/1.0}div').append(ab)

    # Преобразуем в строку с красивым форматированием
    xml_string = etree.tostring(
        tei,
        encoding='utf-8',
        pretty_print=True,
        xml_declaration=True,
    ).decode('utf-8')
    return xml_string


def export_all_aligned(data, edited_df):
    """
    Экспорт всех выровненных списков в ZIP-архив
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, o_name in enumerate(data['others_list']):
            # Собираем выровненные слова
            base_words = data['base_words']
            aligned_words = []
            variant_types = {}

            for i, b_word in enumerate(base_words):
                m_word = data['all_aligns'][o_name].get(i)
                aligned_words.append(m_word)
                variant_types[i] = edited_df.iloc[i][f"Тип ({o_name})"]

            # Создаем XML
            xml_content = export_aligned_xml(
                base_words,
                aligned_words,
                data['main_file'],
                o_name,
                variant_types,
            )

            # Добавляем в ZIP
            filename = f"aligned_{data['main_file'].replace('.xml', '')}_vs_{o_name.replace('.xml', '')}.xml"
            zip_file.writestr(filename, xml_content)

    zip_buffer.seek(0)
    return zip_buffer


# --- 7. ИНТЕРФЕЙС ---
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Сравнительный анализ параллельных корпусов</div>
        <p class="hero-subtitle">
            Яркий интерфейс для загрузки XML-TEI, автоматического выравнивания списков,
            просмотра контекста, редактирования типов разночтений и экспорта результатов.
        </p>
        <div class="bright-pill-row">
            <span class="bright-pill">🌈 яркая тема</span>
            <span class="bright-pill">📚 XML-TEI</span>
            <span class="bright-pill">🧬 выравнивание</span>
            <span class="bright-pill">⬇️ CSV / ZIP</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ПОДРОБНАЯ ИНСТРУКЦИЯ
with st.expander("📘 ПОДРОБНАЯ ИНСТРУКЦИЯ ПОЛЬЗОВАТЕЛЯ (нажмите, чтобы развернуть)", expanded=True):
    st.markdown(
        """
        ### Ссылки
        - [GitHub репозиторий](https://github.com/cmetanok/histori-corpus)

        ### ОСНОВНЫЕ ВОЗМОЖНОСТИ ПРОГРАММЫ
        Данная программа позволяет сравнивать различные списки древнерусских евангельских текстов,
        автоматически выявлять разночтения и редактировать результаты.

        ---
        ### АЛГОРИТМ ОПРЕДЕЛЕНИЯ ТИПОВ РАЗНОЧТЕНИЙ
        | Приоритет | Тип | Условие | Пример |
        |-----------|-----|---------|--------|
        | 1 | **Идентично** | Normalized и surface совпадают | "странѣ" = "странѣ" |
        | 2 | **Графическое** | Normalized совпадает, surface разный | "грѣшницѣ" vs "грѣшници" |
        | 3 | **Фонетическое** | Phonetic форма совпадает | "оу" vs "у" |
        | 4 | **Морфологическое** | Lemma совпадает, morph разный | "грѣшницѣ" (дат.п.) vs "грѣшника" (вин.п.) |
        | 5 | **Лексическое** | Во всех остальных случаях | "человѣкъ" vs "господь" |

        ---
        ### ШАГ 1: ЗАГРУЗКА ФАЙЛОВ
        1. В левой боковой панели (**Sidebar**) нажмите **"Browse files"** или **"Загрузить XML"**
        2. Выберите один или несколько XML-файлов с евангельскими списками
        3. После загрузки в выпадающем списке **"Эталонный список"** выберите основной текст

        ---
        ### ✨ ШАГ 2: РАБОТА С ТАБЛИЦЕЙ-РЕДАКТОРОМ
        | Действие | Как выполнить |
        |----------|---------------|
        | **Сортировка** | Нажмите на заголовок колонки (▲▼) |
        | **Поиск** | Нажмите **Ctrl+F** (или Cmd+F на Mac) |
        | **Фильтрация** | Нажмите на значок фильтра (≡) в заголовке |
        | **Скрыть колонку** | Нажмите ☰ в правом верхнем углу таблицы |
        | **Редактировать тип** | Дважды кликните по ячейке в колонке "Тип (...)" |

        ---
        ### ШАГ 3: ПРОСМОТР КОНТЕКСТА
        Под таблицей находится блок **"Контекст слова"**:
        1. Введите номер строки
        2. Выберите источник (эталон или другой список)
        3. Программа покажет 10 слов до и 10 слов после

        ---
        ### ШАГ 4: СТАТИСТИКА И ЭКСПОРТ
        Внизу страницы:
        - **Статистика** по каждому списку (обновляется при редактировании)
        - **Кнопка "Скачать результаты (CSV)"** для сохранения в формате CSV
        - **Кнопка "Экспорт в XML-TEI"** для сохранения выровненных списков в формате XML-TEI (ZIP-архив)

        ---
        ### ФОРМАТЫ ЭКСПОРТА
        **CSV:** Таблица с результатами сравнения для анализа в Excel/Google Sheets

        **XML-TEI:** Выровненные списки в формате TEI (Text Encoding Initiative) для дальнейшей обработки
        в лингвистических программах. Экспортируется ZIP-архив с отдельными XML-файлами для каждой пары сравнения.
        """
    )

if 'raw_data' not in st.session_state:
    st.session_state.raw_data = {}

with st.sidebar:
    st.header("📂 Загрузка XML файлов")
    uploaded_files = st.file_uploader("Выберите XML файлы", type="xml", accept_multiple_files=True)

    if uploaded_files:
        for f in uploaded_files:
            if f.name not in st.session_state.raw_data:
                with st.spinner(f"Загрузка {f.name}..."):
                    st.session_state.raw_data[f.name] = parse_xml_tei(f)

    file_names = list(st.session_state.raw_data.keys())

    if file_names:
        main_file = st.selectbox("✨ Выберите эталонный список", file_names)
        st.success(f"✅ Загружено файлов: {len(file_names)}")
    else:
        main_file = None
        st.info("Загрузите минимум два XML-файла для сравнения.")

# ЗАПУСК АНАЛИЗА
if st.session_state.raw_data and st.button("🚀 Запустить сравнение", type="primary"):
    base_words = st.session_state.raw_data[main_file]
    others = [n for n in st.session_state.raw_data.keys() if n != main_file]

    if others:
        with st.spinner("🌈 Синхронизация текстов..."):
            all_aligns = {name: align_pair(base_words, st.session_state.raw_data[name]) for name in others}

            final_rows = []
            for i, b_word in enumerate(base_words):
                row = {
                    "ID": b_word['id'],
                    "Лемма": b_word['lemma'],
                    f"ЭТАЛОН ({main_file})": b_word['surface'],
                }

                for o_name in others:
                    m_word = all_aligns[o_name].get(i)
                    row[f"Слово ({o_name})"] = m_word['surface'] if m_word else "---"
                    row[f"Тип ({o_name})"] = classify_variant(b_word, m_word) if m_word else "Пропуск"

                final_rows.append(row)

            st.session_state.comp_df = pd.DataFrame(final_rows)
            st.session_state.others_list = others
            st.session_state.main_file = main_file
            st.session_state.base_words = base_words
            st.session_state.all_aligns = all_aligns

        st.success("✅ Сравнение завершено!")
    else:
        st.warning("⚠️ Загрузите хотя бы два файла для сравнения.")

# ВЫВОД РЕЗУЛЬТАТОВ
if 'comp_df' in st.session_state:
    df = st.session_state.comp_df
    main_file = st.session_state.main_file

    st.subheader("🧾 Таблица-редактор")
    st.info(
        "💡 **Совет:** Нажмите на значок ☰ в правом верхнем углу таблицы, чтобы скрыть ненужные колонки. "
        "Используйте Ctrl+F для поиска. Дважды кликните по ячейке 'Тип' для изменения категории."
    )

    def style_table(row):
        styles = [''] * len(row)
        for i, col in enumerate(row.index):
            if "Тип" in col:
                val = row[col]
                if val == "Лексическое":
                    styles[i] = 'background-color: #ff8fab; color: #3b0320; font-weight: 800'
                elif val == "Морфологическое":
                    styles[i] = 'background-color: #fff176; color: #4a3b00; font-weight: 800'
                elif val == "Графическое":
                    styles[i] = 'background-color: #7dd3fc; color: #083344; font-weight: 800'
                elif val == "Фонетическое":
                    styles[i] = 'background-color: #d8b4fe; color: #3b0764; font-weight: 800'
                elif val == "Идентично":
                    styles[i] = 'background-color: #86efac; color: #052e16; font-weight: 800'
                elif val == "Пропуск":
                    styles[i] = 'background-color: #fdba74; color: #431407; font-weight: 800'
        return styles

    edited_df = st.data_editor(
        df.style.apply(style_table, axis=1),
        use_container_width=True,
        height=500,
    )

    # КОНТЕКСТ
    st.divider()
    st.subheader("🔎 Контекст слова (10 слов до и после)")

    col1, col2 = st.columns([1, 2])

    with col1:
        if not edited_df.empty:
            selected_row = st.number_input(
                "Выберите строку для просмотра контекста:",
                0,
                len(edited_df) - 1,
                0,
                key="context_row",
            )

    with col2:
        st.markdown("**Выберите текст для просмотра:**")
        context_options = [f"ЭТАЛОН ({main_file})"] + [
            f"Слово ({name})" for name in st.session_state.others_list
        ]

        context_texts = st.radio(
            "Источник контекста:",
            options=context_options,
            horizontal=True,
            index=0,
            key="context_source",
        )

    if not edited_df.empty:
        selected_word = edited_df.iloc[selected_row][f"ЭТАЛОН ({main_file})"]

        if context_texts.startswith("ЭТАЛОН"):
            words_list = st.session_state.base_words
            word_index = selected_row
            source_name = main_file
        else:
            ms_name = context_texts.replace("Слово (", "").replace(")", "")
            aligned_word = st.session_state.all_aligns.get(ms_name, {}).get(selected_row)

            if aligned_word:
                target_words = st.session_state.raw_data[ms_name]
                word_index = next(
                    (i for i, w in enumerate(target_words) if w['surface'] == aligned_word['surface']),
                    selected_row,
                )
                words_list = target_words
                source_name = ms_name
            else:
                words_list = []
                word_index = 0

        if words_list and word_index < len(words_list):
            before, after = get_context(words_list, word_index)

            context_html = '<div class="context-box">'
            context_html += '<b>🔎 Контекст (10 слов до и после):</b><br><br>'

            if before:
                context_html += '<span style="color: #5b4b8a;">... ' + ' '.join(
                    [w['surface'] for w in before]
                ) + ' </span>'

            context_html += f'<span class="context-highlight">{selected_word}</span>'

            if after:
                context_html += '<span style="color: #5b4b8a;"> ' + ' '.join(
                    [w['surface'] for w in after]
                ) + ' </span>'

            context_html += f'<br><br><span style="font-size: 12px; color: #6d5aa8;">📌 Источник: {source_name}</span>'
            context_html += '</div>'

            st.markdown(context_html, unsafe_allow_html=True)
        else:
            st.info("⚠️ Слово не найдено в выбранном списке для отображения контекста.")

    # СТАТИСТИКА
    st.divider()
    st.subheader("📊 Статистика по текстам")

    for o_name in st.session_state.others_list:
        st.markdown(f"### <span class='status-badge'>Текст: {o_name}</span>", unsafe_allow_html=True)

        type_col = f"Тип ({o_name})"
        counts = edited_df[type_col].value_counts()
        total = len(edited_df)
        identical = counts.get("Идентично", 0)
        diffs = total - identical
        similarity = round(identical / total * 100, 1) if total > 0 else 0

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Всего слов", total)
            st.metric("Идентично", f"{identical} ({similarity}%)")
            st.metric("Различий", f"{diffs} ({100 - similarity}%)")

        with col2:
            st.progress(similarity / 100, text=f"Сходство: {similarity}%")
            st.caption("Типы различий:")

            for t_name in ["Лексическое", "Морфологическое", "Графическое", "Фонетическое", "Пропуск"]:
                c_val = counts.get(t_name, 0)
                if c_val > 0:
                    st.write(f"- {t_name}: {c_val}")

        st.divider()

    # ЭКСПОРТ
    st.divider()
    st.subheader("📦 Экспорт результатов")
    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "⬇️ Скачать CSV",
            csv,
            f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True,
            help="Экспорт таблицы в формате CSV для анализа в Excel",
        )

    with col_export2:
        # Экспорт в XML-TEI
        export_data = {
            'others_list': st.session_state.others_list,
            'base_words': st.session_state.base_words,
            'all_aligns': st.session_state.all_aligns,
            'main_file': st.session_state.main_file,
        }
        zip_buffer = export_all_aligned(export_data, edited_df)

        st.download_button(
            "🧾 Экспорт в XML-TEI (ZIP)",
            zip_buffer,
            f"aligned_corpora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "application/zip",
            use_container_width=True,
            help="Экспорт выровненных списков в формате XML-TEI (ZIP-архив с отдельными файлами для каждой пары)",
        )

    with col_export3:
        # Кнопка сброса
        if st.button("🔄 Новое сравнение", use_container_width=True):
            for key in ['comp_df', 'others_list', 'main_file', 'base_words', 'all_aligns']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
else:
    st.info("📥 Загрузите XML-файлы в боковой панели и нажмите кнопку 'Запустить сравнение'")
