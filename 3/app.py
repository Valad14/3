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

# --- 1. НАСТРОЙКИ СТРАНИЦЫ И ПОЛНОСТЬЮ СВЕТЛЫЙ ИНТЕРФЕЙС ---
st.set_page_config(
    page_title="Лингвистический компаратор",
    page_icon="📘",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --light-bg: #f7f9fc;
        --light-bg-subtle: #fbfcfe;
        --surface: #ffffff;
        --surface-soft: #f9fafb;
        --surface-hover: #f3f6fb;
        --border: #e4e7ec;
        --border-strong: #d0d5dd;
        --text: #1d2939;
        --text-soft: #475467;
        --text-muted: #667085;
        --accent: #315efb;
        --accent-hover: #2448c9;
        --accent-soft: #eef4ff;
        --accent-border: #c7d7fe;
        --shadow-sm: 0 1px 2px rgba(16, 24, 40, 0.04);
        --shadow-md: 0 10px 30px rgba(16, 24, 40, 0.07);
        --radius-lg: 22px;
        --radius-md: 16px;
        --historic-font: 'Noto Serif', 'DejaVu Serif', 'Segoe UI Historic', 'Times New Roman', serif;
        --ui-font: Inter, 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--light-bg) !important;
        color: var(--text) !important;
        font-family: var(--ui-font) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(247, 249, 252, 0.92) !important;
        border-bottom: 1px solid rgba(228, 231, 236, 0.72);
        backdrop-filter: blur(10px);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1240px;
    }

    h1, h2, h3, h4,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text) !important;
        letter-spacing: -0.02em;
        font-weight: 850;
    }

    p, li, label, .stMarkdown, [data-testid="stMarkdownContainer"] {
        color: var(--text-soft) !important;
    }

    a {
        color: var(--accent) !important;
        text-decoration: none !important;
        font-weight: 700;
    }

    a:hover {
        color: var(--accent-hover) !important;
        text-decoration: underline !important;
    }

    .hero-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 28px;
        padding: 30px 34px;
        margin-bottom: 1.25rem;
        box-shadow: var(--shadow-md);
    }

    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
        padding: 7px 12px;
        border: 1px solid var(--accent-border);
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent) !important;
        font-size: 0.86rem;
        font-weight: 850;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }

    .hero-title {
        margin: 0;
        max-width: 980px;
        color: var(--text) !important;
        font-size: clamp(2rem, 4.3vw, 4.15rem);
        font-weight: 900;
        line-height: 1.04;
    }

    .hero-subtitle {
        margin: 14px 0 0 0;
        max-width: 980px;
        color: var(--text-soft) !important;
        font-size: 1.08rem;
        line-height: 1.65;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-top: 24px;
    }

    .feature-card {
        background: var(--surface-soft);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 14px 15px;
        min-height: 105px;
    }

    .feature-index {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        margin-bottom: 10px;
        border-radius: 10px;
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--accent) !important;
        font-size: 0.82rem;
        font-weight: 900;
    }

    .feature-title {
        display: block;
        color: var(--text) !important;
        font-weight: 850;
        margin-bottom: 4px;
    }

    .feature-copy {
        color: var(--text-muted) !important;
        font-size: 0.9rem;
        line-height: 1.4;
    }

    @media (max-width: 980px) {
        .feature-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 640px) {
        .hero-card {
            padding: 22px;
            border-radius: 22px;
        }
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }

    [data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--border);
        box-shadow: 4px 0 18px rgba(16, 24, 40, 0.03);
    }

    [data-testid="stSidebar"] * {
        color: var(--text) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stHeader {
        color: var(--text) !important;
        font-weight: 850 !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: var(--surface-soft) !important;
        border: 1.5px dashed var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
        transition: border-color 0.2s ease, background 0.2s ease;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
        background: var(--surface-hover) !important;
        border-color: var(--accent-border) !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    input,
    textarea,
    [data-baseweb="select"] > div {
        background: var(--surface) !important;
        border-color: var(--border-strong) !important;
        color: var(--text) !important;
        border-radius: 14px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stSidebar"] .stAlert,
    div[data-testid="stAlert"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text) !important;
        box-shadow: var(--shadow-sm);
    }

    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] div,
    div[data-testid="stAlert"] span {
        color: var(--text-soft) !important;
    }

    section.main div[data-testid="stExpander"],
    div[data-testid="stMetric"],
    div[data-testid="stDataEditor"],
    div[data-testid="stDataFrame"] {
        border-radius: var(--radius-lg) !important;
    }

    section.main div[data-testid="stExpander"],
    div[data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden;
    }

    section.main div[data-testid="stExpander"] details {
        background: var(--surface) !important;
        border-radius: var(--radius-lg) !important;
    }

    section.main div[data-testid="stExpander"] summary {
        background: var(--surface) !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 0.85rem 1rem !important;
        color: var(--text) !important;
    }

    section.main div[data-testid="stExpander"] summary *,
    section.main div[data-testid="stExpander"] button,
    section.main div[data-testid="stExpander"] button * {
        background: transparent !important;
        color: var(--text) !important;
        font-weight: 850 !important;
    }

    section.main div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
        padding-top: 0.2rem;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"] {
        border-radius: 12px !important;
        min-height: 2.7rem;
        font-weight: 850 !important;
        transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease, border-color 0.16s ease !important;
    }

    button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 18px rgba(49, 94, 251, 0.18) !important;
    }

    .stDownloadButton > button,
    .stButton > button:not([kind="primary"]) {
        background: var(--surface) !important;
        border: 1px solid var(--border-strong) !important;
        color: var(--text) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md) !important;
        border-color: var(--accent-border) !important;
    }

    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
        border-color: var(--accent-hover) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        background: transparent !important;
        color: var(--text-soft) !important;
        font-weight: 850;
    }

    .stTabs [aria-selected="true"] {
        background: var(--surface) !important;
        color: var(--accent) !important;
        border: 1px solid var(--border) !important;
        border-bottom-color: var(--surface) !important;
    }

    div[data-testid="stMetric"] {
        padding: 17px 18px;
        border-left: 4px solid var(--accent) !important;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] label * {
        color: var(--text-muted) !important;
        font-weight: 850 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] * {
        color: var(--text) !important;
        font-weight: 900 !important;
    }

    [data-testid="stDataEditor"] div[role="grid"],
    [data-testid="stDataFrame"] div[role="grid"] {
        border-radius: var(--radius-md);
        overflow: hidden;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        background: var(--surface) !important;
    }

    [data-testid="stDataEditor"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background: var(--surface-soft) !important;
        color: var(--text) !important;
        font-weight: 900 !important;
        border-bottom: 1px solid var(--border) !important;
    }

    [data-testid="stDataEditor"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th,
    .stDataFrame td,
    .dataframe td,
    .dataframe th {
        font-family: var(--historic-font) !important;
        font-size: 18px !important;
        color: var(--text) !important;
    }

    .big-word {
        font-family: var(--historic-font);
        font-size: 60px;
        color: var(--text);
        padding: 20px;
        background: var(--surface);
        border-radius: var(--radius-lg);
        text-align: center;
        border: 1px solid var(--border);
        margin: 15px 0;
        box-shadow: var(--shadow-sm);
    }

    .context-box {
        background: var(--surface);
        padding: 20px;
        border-radius: var(--radius-lg);
        font-family: var(--historic-font);
        font-size: 20px;
        margin: 12px 0;
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        box-shadow: var(--shadow-sm);
        color: var(--text);
        line-height: 1.7;
    }

    .context-box b {
        font-family: var(--ui-font);
        color: var(--text) !important;
    }

    .context-muted {
        color: var(--text-muted) !important;
    }

    .context-source {
        font-family: var(--ui-font);
        font-size: 12px;
        color: var(--text-muted) !important;
    }

    .context-highlight {
        background: var(--accent-soft);
        color: var(--accent) !important;
        padding: 4px 10px;
        border-radius: 10px;
        font-weight: 900;
        border: 1px solid var(--accent-border);
    }

    .stat-card {
        background: var(--surface);
        padding: 18px;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        margin-bottom: 12px;
        box-shadow: var(--shadow-sm);
    }

    .instruction-step,
    .instruction-note {
        background: var(--surface);
        padding: 16px;
        border-radius: var(--radius-md);
        margin: 10px 0;
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        border-radius: 999px;
        font-size: 0.92rem;
        font-weight: 850;
        background: var(--surface);
        color: var(--text) !important;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }

    .stProgress > div > div > div > div {
        background: var(--accent) !important;
    }

    hr, [data-testid="stDivider"] {
        border-color: var(--border) !important;
    }

    table {
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 14px;
    }

    th {
        background: var(--surface-soft) !important;
        color: var(--text) !important;
        font-weight: 850 !important;
    }

    td, th {
        border-color: var(--border) !important;
    }

    code {
        background: var(--surface-soft) !important;
        color: var(--text) !important;
        border: 1px solid var(--border);
        border-radius: 7px;
        padding: 0.08rem 0.28rem;
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
        <div class="hero-eyebrow">Светлая тема · XML-TEI · сравнение списков</div>
        <h1 class="hero-title">Сравнительный анализ параллельных корпусов</h1>
        <p class="hero-subtitle">
            Загрузите XML-TEI файлы, выберите эталонный список и получите аккуратную таблицу
            выравнивания с контекстом, статистикой и экспортом результатов.
        </p>
        <div class="feature-grid">
            <div class="feature-card">
                <span class="feature-index">01</span>
                <span class="feature-title">Загрузка XML</span>
                <span class="feature-copy">Несколько списков для параллельного сравнения.</span>
            </div>
            <div class="feature-card">
                <span class="feature-index">02</span>
                <span class="feature-title">Выравнивание</span>
                <span class="feature-copy">Автоматическое сопоставление словоформ.</span>
            </div>
            <div class="feature-card">
                <span class="feature-index">03</span>
                <span class="feature-title">Редактор</span>
                <span class="feature-copy">Проверка и ручная правка типов разночтений.</span>
            </div>
            <div class="feature-card">
                <span class="feature-index">04</span>
                <span class="feature-title">Экспорт</span>
                <span class="feature-copy">Сохранение результатов в CSV и XML-TEI ZIP.</span>
            </div>
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
        with st.spinner("Синхронизация текстов..."):
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
                    styles[i] = 'background-color: #fde2e7; color: #7f1d1d; font-weight: 800'
                elif val == "Морфологическое":
                    styles[i] = 'background-color: #fff4cc; color: #78350f; font-weight: 800'
                elif val == "Графическое":
                    styles[i] = 'background-color: #e0f2fe; color: #075985; font-weight: 800'
                elif val == "Фонетическое":
                    styles[i] = 'background-color: #efe7ff; color: #5b21b6; font-weight: 800'
                elif val == "Идентично":
                    styles[i] = 'background-color: #dcfce7; color: #166534; font-weight: 800'
                elif val == "Пропуск":
                    styles[i] = 'background-color: #f3f4f6; color: #374151; font-weight: 800'
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
                context_html += '<span class="context-muted">... ' + ' '.join(
                    [w['surface'] for w in before]
                ) + ' </span>'

            context_html += f'<span class="context-highlight">{selected_word}</span>'

            if after:
                context_html += '<span class="context-muted"> ' + ' '.join(
                    [w['surface'] for w in after]
                ) + ' </span>'

            context_html += f'<br><br><span class="context-source">📌 Источник: {source_name}</span>'
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
