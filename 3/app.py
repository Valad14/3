import html
import io
import re
import unicodedata
import zipfile
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st
from lxml import etree
from lxml.builder import ElementMaker


# -----------------------------------------------------------------------------
# 1. Общие настройки
# -----------------------------------------------------------------------------

TABLE_FONT_STACK = (
    '"Noto Sans", "Noto Serif", "Noto Sans Symbols 2", "Segoe UI Historic", '
    '"Segoe UI Symbol", "Arial Unicode MS", "DejaVu Sans", "FreeSerif", '
    '"Times New Roman", serif'
)

# Надстрочные кириллические буквы U+2DE0..U+2DFF и несколько редких знаков.
# Для сравнения они раскрываются в обычные буквы; для совместимого режима могут
# отображаться в квадратных скобках.
COMBINING_CYRILLIC_LETTERS = {
    "\u2de0": "б",
    "\u2de1": "в",
    "\u2de2": "г",
    "\u2de3": "д",
    "\u2de4": "ж",
    "\u2de5": "з",
    "\u2de6": "к",
    "\u2de7": "л",
    "\u2de8": "м",
    "\u2de9": "н",
    "\u2dea": "о",
    "\u2deb": "п",
    "\u2dec": "р",
    "\u2ded": "с",
    "\u2dee": "т",
    "\u2def": "х",
    "\u2df0": "ц",
    "\u2df1": "ч",
    "\u2df2": "ш",
    "\u2df3": "щ",
    "\u2df4": "ф",
    "\u2df5": "ст",
    "\u2df6": "а",
    "\u2df7": "е",
    "\u2df8": "д",
    "\u2df9": "оу",
    "\u2dfa": "ѣ",
    "\u2dfb": "ю",
    "\u2dfc": "ꙗ",
    "\u2dfd": "ѧ",
    "\u2dfe": "ѫ",
    "\u2dff": "ѭ",
    "\ua69f": "ѥ",
    "\ua675": "и",
    "\ua678": "ъ",
}

ORTHOGRAPHIC_REPLACEMENTS = {
    "ѣ": "е",
    "Ѣ": "е",
    "ѳ": "ф",
    "Ѳ": "ф",
    "ѵ": "и",
    "Ѵ": "и",
    "ѡ": "о",
    "Ѡ": "о",
    "ꙑ": "ы",
    "Ꙑ": "ы",
    "ꙗ": "я",
    "Ꙗ": "я",
    "ѥ": "е",
    "Ѥ": "е",
    "ѕ": "з",
    "Ѕ": "з",
    "ꙁ": "з",
    "Ꙁ": "з",
    "ѧ": "я",
    "Ѧ": "я",
    "ѩ": "я",
    "Ѩ": "я",
    "ѫ": "у",
    "Ѫ": "у",
    "ѭ": "ю",
    "Ѭ": "ю",
    "ѯ": "кс",
    "Ѯ": "кс",
    "ѱ": "пс",
    "Ѱ": "пс",
    "ѿ": "от",
    "Ѿ": "от",
    "ı": "и",
    "ꙋ": "у",
    "Ꙋ": "у",
}

COMPATIBLE_REPLACEMENTS = {
    **ORTHOGRAPHIC_REPLACEMENTS,
    "і": "и",
    "ї": "и",
    "ѐ": "е",
    "ѝ": "и",
}

PHONETIC_REPLACEMENTS = {
    "ѣ": "е",
    "Ѣ": "е",
    "ѧ": "я",
    "Ѧ": "я",
    "ѩ": "я",
    "Ѩ": "я",
    "ꙗ": "я",
    "Ꙗ": "я",
    "ѥ": "е",
    "Ѥ": "е",
    "ѫ": "у",
    "Ѫ": "у",
    "ѭ": "ю",
    "Ѭ": "ю",
    "ѡ": "о",
    "Ѡ": "о",
    "ꙑ": "ы",
    "Ꙑ": "ы",
    "ꙁ": "з",
    "Ꙁ": "з",
    "ѕ": "з",
    "Ѕ": "з",
    "ѳ": "ф",
    "Ѳ": "ф",
    "ѵ": "и",
    "Ѵ": "и",
    "ı": "и",
    "ꙋ": "у",
    "Ꙋ": "у",
}

WORD_COLUMN_PREFIXES = ("Основной список (", "Слово (")


# -----------------------------------------------------------------------------
# 2. Нормализация и чтение XML
# -----------------------------------------------------------------------------

def decode_xml_bytes(raw: bytes) -> str:
    """Читает XML, даже если в декларации указана неверная кодировка."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ["utf-16", "utf-8-sig", "utf-8", "cp1251"]
    else:
        # Загруженные проверочные файлы объявлены как UTF-16, но физически лежат в UTF-8.
        encodings = ["utf-8-sig", "utf-8", "utf-16", "cp1251"]

    for enc in encodings:
        try:
            text = raw.decode(enc)
            if "<" in text[:200]:
                return text
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_xml_declaration(text: str) -> str:
    return re.sub(r"^\s*<\?xml[^>]*\?>", "", text, count=1)


def expand_combining_letters(text: str, bracketed: bool = False) -> str:
    result = []
    for ch in text:
        if ch in COMBINING_CYRILLIC_LETTERS:
            repl = COMBINING_CYRILLIC_LETTERS[ch]
            result.append(f"[{repl}]" if bracketed else repl)
        else:
            result.append(ch)
    return "".join(result)


def remove_combining_marks(text: str, expand_letters: bool = True) -> str:
    """Убирает титла, ударения и прочие надстрочные знаки без потери базовых букв."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    if expand_letters:
        text = expand_combining_letters(text, bracketed=False)

    result = []
    for ch in unicodedata.normalize("NFD", text):
        code = ord(ch)
        if unicodedata.category(ch) == "Mn":
            continue
        if 0x0483 <= code <= 0x0489:  # титло, покрытие и др.
            continue
        if 0xA66F <= code <= 0xA67D:  # взмет и надстрочные буквы Extended-B
            continue
        if 0x0300 <= code <= 0x036F:
            continue
        result.append(ch)
    return unicodedata.normalize("NFC", "".join(result))


def normalize_letters(text: str, replacements: dict[str, str]) -> str:
    if not text:
        return ""
    text = str(text).lower().replace("ё", "е")
    text = text.replace("ѹ", "у").replace("ꙋ", "у").replace("оу", "у")
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Оставляем только буквы; пунктуация и пробелы не должны влиять на тип разночтения.
    return re.sub(r"[^а-яa-z]+", "", text, flags=re.IGNORECASE)


def orthographic_normalize(text: str) -> str:
    return normalize_letters(remove_combining_marks(text, expand_letters=True), ORTHOGRAPHIC_REPLACEMENTS)


def phonetic_normalize(text: str) -> str:
    text = normalize_letters(remove_combining_marks(text, expand_letters=True), PHONETIC_REPLACEMENTS)
    for old, new in {
        "о": "а",
        "е": "и",
        "я": "а",
        "ю": "у",
        "ы": "и",
        "ъ": "",
        "ь": "",
    }.items():
        text = text.replace(old, new)
    return text


def lemma_normalize(lemma: str) -> str:
    return orthographic_normalize(lemma or "")


def morph_key(morph: dict[str, tuple[str, ...]]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple((name, tuple(sorted(set(values)))) for name, values in sorted(morph.items()))


def format_morph(morph: dict[str, tuple[str, ...]]) -> str:
    if not morph:
        return "нет разметки"
    return "; ".join(f"{k}={','.join(v)}" for k, v in sorted(morph.items()))


def parse_xml_tei(file) -> list[dict]:
    """Парсинг XML-TEI: сохраняет оригинальную форму, лемму и все значения f/symbol."""
    raw = file.read()
    try:
        content = strip_xml_declaration(decode_xml_bytes(raw))
        root = etree.fromstring(
            content.encode("utf-8"),
            parser=etree.XMLParser(recover=True, huge_tree=True),
        )
        words = []
        for idx, w in enumerate(root.xpath('.//*[local-name()="w"]')):
            word_id = (
                w.get("{http://www.w3.org/XML/1998/namespace}id")
                or w.get("id")
                or f"w{idx + 1}"
            )
            lemma = (w.get("lemma") or "").strip().lower()
            surface = unicodedata.normalize("NFC", "".join(w.xpath("text()")).strip())
            if not surface:
                continue

            morph_values: dict[str, set[str]] = {}
            for f in w.xpath('.//*[local-name()="f"]'):
                name = (f.get("name") or "").strip()
                symbol_values = [
                    v.strip()
                    for v in f.xpath('.//*[local-name()="symbol"]/@value')
                    if v and v.strip()
                ]
                if name and symbol_values:
                    morph_values.setdefault(name, set()).update(symbol_values)

            morph = {k: tuple(sorted(v)) for k, v in morph_values.items()}
            words.append(
                {
                    "idx": len(words),
                    "id": word_id,
                    "surface": surface,
                    "surface_plain": remove_combining_marks(surface, expand_letters=True),
                    "lemma": lemma,
                    "lemma_norm": lemma_normalize(lemma),
                    "morph": morph,
                    "morph_key": morph_key(morph),
                    "orth": orthographic_normalize(surface),
                    "phonetic": phonetic_normalize(surface),
                }
            )
        return words
    except Exception as exc:
        file_name = getattr(file, "name", "XML")
        st.error(f"Ошибка в файле {file_name}: {exc}")
        return []


# -----------------------------------------------------------------------------
# 3. Выравнивание
# -----------------------------------------------------------------------------

def edit_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


def same_lemma(w1: dict, w2: dict) -> bool:
    return bool(w1.get("lemma_norm") and w2.get("lemma_norm") and w1["lemma_norm"] == w2["lemma_norm"])


def same_morph(w1: dict, w2: dict) -> bool:
    return w1.get("morph_key") == w2.get("morph_key")


def both_have_morph(w1: dict, w2: dict) -> bool:
    return bool(w1.get("morph_key")) and bool(w2.get("morph_key"))


def similarity_score(w1: dict | None, w2: dict | None) -> int:
    if not w1 or not w2:
        return -6
    if w1["surface"] == w2["surface"] and same_morph(w1, w2):
        return 14
    if w1["orth"] and w1["orth"] == w2["orth"]:
        return 12
    if same_lemma(w1, w2) and same_morph(w1, w2):
        return 10
    if same_lemma(w1, w2):
        return 7
    if (
        w1["phonetic"]
        and w1["phonetic"] == w2["phonetic"]
        and min(len(w1["orth"]), len(w2["orth"])) >= 3
    ):
        return 5

    sim = edit_similarity(w1["orth"], w2["orth"])
    if sim >= 0.82:
        return 4
    if sim >= 0.68:
        return 2
    return -5


def align_pair(base_list: list[dict], target_list: list[dict]) -> dict[int, dict | None]:
    """Needleman-Wunsch с запретом на явно отрицательные пары в финальной выдаче."""
    n, m = len(base_list), len(target_list)
    gap = -3
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    trace = [[""] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = i * gap
        trace[i][0] = "up"
    for j in range(1, m + 1):
        dp[0][j] = j * gap
        trace[0][j] = "left"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = [
                (dp[i - 1][j - 1] + similarity_score(base_list[i - 1], target_list[j - 1]), "diag"),
                (dp[i - 1][j] + gap, "up"),
                (dp[i][j - 1] + gap, "left"),
            ]
            dp[i][j], trace[i][j] = max(options, key=lambda item: item[0])

    matches: dict[int, dict | None] = {}
    i, j = n, m
    while i > 0 or j > 0:
        move = trace[i][j]
        if move == "diag":
            score = similarity_score(base_list[i - 1], target_list[j - 1])
            matches[i - 1] = target_list[j - 1] if score >= 0 else None
            i -= 1
            j -= 1
        elif move == "up":
            matches[i - 1] = None
            i -= 1
        else:
            j -= 1
    return matches


# -----------------------------------------------------------------------------
# 4. Контекст
# -----------------------------------------------------------------------------

def get_context(words: list[dict], index: int, context_size: int = 10) -> tuple[list[dict], list[dict]]:
    start = max(0, index - context_size)
    end = min(len(words), index + context_size + 1)
    return words[start:index], words[index + 1:end]


# -----------------------------------------------------------------------------
# 5. Экспорт
# -----------------------------------------------------------------------------

def export_aligned_xml(
    base_words: list[dict],
    aligned_words: list[dict | None],
    base_filename: str,
    target_filename: str,
) -> str:
    E = ElementMaker(
        namespace="http://www.tei-c.org/ns/1.0",
        nsmap={None: "http://www.tei-c.org/ns/1.0"},
    )
    tei = E.TEI(
        E.teiHeader(
            E.fileDesc(
                E.titleStmt(E.title(f"Выровненный корпус: {base_filename} ↔ {target_filename}")),
                E.publicationStmt(E.p("Создано Лингвистическим компаратором")),
                E.sourceDesc(E.p(f"Основано на: {base_filename} и {target_filename}")),
            ),
            E.encodingDesc(
                E.classDecl(
                    E.taxonomy(
                        E.category(E.catDesc("Лингвистический компаратор - выровненный корпус"))
                    )
                )
            ),
        ),
        E.text(E.body(E.div(E.head("Выровненные тексты"), type="aligned_corpus"))),
    )

    ab = E.ab()
    ab.append(E.note("Выравнивание выполнено алгоритмом Нидлмана-Вунша"))
    ab.append(E.note(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))

    for i, (base_word, aligned_word) in enumerate(zip(base_words, aligned_words)):
        ab.append(E.milestone(unit="alignment", n=str(i + 1)))

        base_elem = E.w(
            base_word["surface"],
            xml_id=base_word["id"],
            lemma=base_word["lemma"],
            type="base",
        )
        for morph_name, morph_values in base_word["morph"].items():
            for morph_value in morph_values:
                base_elem.append(E.fs(E.f(E.symbol(value=morph_value), name=morph_name)))
        ab.append(base_elem)

        if aligned_word:
            target_elem = E.w(
                aligned_word["surface"],
                xml_id=aligned_word["id"],
                lemma=aligned_word["lemma"],
                type="target",
            )
            for morph_name, morph_values in aligned_word["morph"].items():
                for morph_value in morph_values:
                    target_elem.append(E.fs(E.f(E.symbol(value=morph_value), name=morph_name)))
            ab.append(target_elem)
        else:
            ab.append(E.w("---", type="missing"))
        ab.append(E.pc(" "))

    tei.find('.//{http://www.tei-c.org/ns/1.0}div').append(ab)
    return etree.tostring(
        tei,
        encoding="utf-8",
        pretty_print=True,
        xml_declaration=True,
    ).decode("utf-8")


def export_all_aligned(data: dict, edited_df: pd.DataFrame) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for o_name in data["others_list"]:
            base_words = data["base_words"]
            aligned_words = []
            for i, _ in enumerate(base_words):
                matched_word = data["all_aligns"][o_name].get(i)
                aligned_words.append(matched_word)

            xml_content = export_aligned_xml(
                base_words,
                aligned_words,
                data["main_file"],
                o_name,
            )
            filename = (
                f"aligned_{data['main_file'].replace('.xml', '')}"
                f"_vs_{o_name.replace('.xml', '')}.xml"
            )
            zip_file.writestr(filename, xml_content)
    zip_buffer.seek(0)
    return zip_buffer


# -----------------------------------------------------------------------------
# 6. Отображение таблицы и совместимость символов
# -----------------------------------------------------------------------------

def compatible_text(text: str) -> str:
    if not text or text == "---":
        return text
    text = expand_combining_letters(str(text), bracketed=True)
    text = remove_combining_marks(text, expand_letters=False)
    for old, new in COMPATIBLE_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def display_text(text: str, mode: str) -> str:
    if not text or text == "---":
        return text
    if mode.startswith("Оригинал"):
        return text
    if mode.startswith("Без надстрочных"):
        return remove_combining_marks(text, expand_letters=True)
    return compatible_text(text)


def apply_display_mode(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    result = df.copy()
    for col in result.columns:
        if col.startswith(WORD_COLUMN_PREFIXES):
            result[col] = result[col].map(lambda value: display_text(value, mode))
    return result



def render_context(words: list[dict], word_index: int, selected_surface: str, source_name: str, display_mode: str) -> None:
    before, after = get_context(words, word_index)
    before_text = " ".join(display_text(w["surface"], display_mode) for w in before)
    after_text = " ".join(display_text(w["surface"], display_mode) for w in after)
    selected = display_text(selected_surface, display_mode)

    context_html = "<div class='context-box'>"
    context_html += "<b>Контекст (10 слов до и после):</b><br><br>"
    if before_text:
        context_html += html.escape("... " + before_text + " ")
    context_html += f"<mark>{html.escape(selected)}</mark>"
    if after_text:
        context_html += html.escape(" " + after_text + " ...")
    context_html += f"<br><br><small>Источник: {html.escape(source_name)}</small>"
    context_html += "</div>"
    st.markdown(context_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. Интерфейс Streamlit
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Лингвистический компаратор",
    page_icon="📜",
    layout="wide",
)

st.markdown(
    f"""
    <style>
    html, body, [class*="css"], .stMarkdown, .stDataFrame, .stDataEditor {{
        font-family: {TABLE_FONT_STACK};
    }}
    [data-testid="stDataFrame"] div, [data-testid="stDataEditor"] div {{
        font-family: {TABLE_FONT_STACK} !important;
        font-size: 15px;
    }}
    .context-box {{
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px 18px;
        background: #f8fafc;
        line-height: 1.9;
        font-size: 17px;
    }}
    .compat-note {{
        border-left: 4px solid #0ea5e9;
        padding: 10px 14px;
        background: #f0f9ff;
        border-radius: 8px;
    }}
    mark {{
        padding: 2px 6px;
        border-radius: 6px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    # Сравнительный анализ параллельных корпусов

    Загрузите XML-TEI файлы, выберите основной список и получите таблицу
    выравнивания с контекстом, статистикой совпадений и экспортом.
    """
)

with st.expander("Подробная инструкция пользователя", expanded=False):
    st.markdown(
        """
        ### Как читать таблицу

        Программа больше не проставляет автоматические типы вроде
        «морфологическое», «графическое», «фонетическое» и т. д. Таблица показывает
        только выравнивание: слово из основного списка и найденные соответствия в
        остальных XML-файлах.

        ### Старый компьютер и «квадратики» вместо символов

        В боковой панели есть режим **Отображение символов**. Если в таблице не
        видны исторические буквы или надстрочные знаки, выберите
        **Совместимый режим**. Экспорт XML при этом сохраняет оригинальные формы.
        """
    )

if "raw_data" not in st.session_state:
    st.session_state.raw_data = {}

with st.sidebar:
    st.header("Загрузка XML файлов")
    uploaded_files = st.file_uploader(
        "Выберите XML файлы",
        type="xml",
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded in uploaded_files:
            if uploaded.name not in st.session_state.raw_data:
                with st.spinner(f"Загрузка {uploaded.name}..."):
                    st.session_state.raw_data[uploaded.name] = parse_xml_tei(uploaded)

    file_names = list(st.session_state.raw_data.keys())
    if file_names:
        main_file = st.selectbox("Выберите основной список", file_names)
        st.success(f"Загружено файлов: {len(file_names)}")
        word_counts = {name: len(words) for name, words in st.session_state.raw_data.items()}
        with st.expander("Сколько слов прочитано"):
            for name, count in word_counts.items():
                st.write(f"{name}: {count}")
    else:
        main_file = None
        st.info("Загрузите минимум два XML-файла для сравнения.")

    display_mode = st.radio(
        "Отображение символов",
        options=[
            "Оригинал",
            "Без надстрочных знаков",
            "Совместимый режим",
        ],
        index=0,
        help="Совместимый режим заменяет редкие исторические символы на более обычную кириллицу только в таблице.",
    )

    if st.button("Очистить загруженные файлы", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key in {
                "raw_data",
                "comp_df",
                "others_list",
                "main_file",
                "base_words",
                "all_aligns",
            }:
                del st.session_state[key]
        st.rerun()

if st.session_state.raw_data and len(st.session_state.raw_data) >= 2:
    if st.button("Запустить сравнение", type="primary"):
        base_words = st.session_state.raw_data[main_file]
        others = [name for name in st.session_state.raw_data.keys() if name != main_file]

        with st.spinner("Синхронизация текстов..."):
            all_aligns = {
                name: align_pair(base_words, st.session_state.raw_data[name])
                for name in others
            }

            rows = []
            for i, base_word in enumerate(base_words):
                row = {
                    "№": i + 1,
                    "ID": base_word["id"],
                    "Лемма": base_word["lemma"],
                    f"Основной список ({main_file})": base_word["surface"],
                }
                for other_name in others:
                    matched_word = all_aligns[other_name].get(i)
                    row[f"Слово ({other_name})"] = matched_word["surface"] if matched_word else "---"
                rows.append(row)

            st.session_state.comp_df = pd.DataFrame(rows)
            st.session_state.others_list = others
            st.session_state.main_file = main_file
            st.session_state.base_words = base_words
            st.session_state.all_aligns = all_aligns

        st.success("Сравнение завершено.")
elif st.session_state.raw_data:
    st.warning("Загрузите хотя бы два файла для сравнения.")

if "comp_df" in st.session_state:
    df = st.session_state.comp_df.copy()
    main_file = st.session_state.main_file

    st.subheader("Таблица выравнивания")

    if display_mode == "Совместимый режим":
        st.markdown(
            "<div class='compat-note'>Включен совместимый режим: редкие буквы и надстрочные знаки заменяются только для отображения. XML и CSV экспортируют исходные формы.</div>",
            unsafe_allow_html=True,
        )

    table_df = apply_display_mode(df, display_mode)
    st.caption(f"Показано строк: {len(table_df)}")
    st.dataframe(
        table_df,
        use_container_width=True,
        height=520,
        hide_index=True,
    )

    st.divider()
    st.subheader("Контекст слова")
    context_col1, context_col2 = st.columns([1, 3])
    with context_col1:
        selected_row_number = st.number_input(
            "Номер строки:",
            min_value=1,
            max_value=len(df),
            value=1,
            step=1,
        )
        selected_row_idx = int(selected_row_number) - 1
    with context_col2:
        context_options = [f"Основной список ({main_file})"] + [f"Слово ({name})" for name in st.session_state.others_list]
        context_source = st.radio("Источник контекста:", context_options, horizontal=True)

    if context_source.startswith("Основной список"):
        words_list = st.session_state.base_words
        word_index = selected_row_idx
        selected_surface = st.session_state.base_words[selected_row_idx]["surface"]
        source_name = main_file
        render_context(words_list, word_index, selected_surface, source_name, display_mode)
    else:
        other_name = context_source.replace("Слово (", "", 1).rstrip(")")
        aligned_word = st.session_state.all_aligns.get(other_name, {}).get(selected_row_idx)
        if aligned_word:
            words_list = st.session_state.raw_data[other_name]
            word_index = aligned_word["idx"]
            render_context(words_list, word_index, aligned_word["surface"], other_name, display_mode)
        else:
            st.info("В выбранном списке для этой строки стоит пропуск.")

    st.divider()
    st.subheader("Статистика выравнивания")
    stats_cols = st.columns(min(3, max(1, len(st.session_state.others_list))))
    total = len(df)
    for idx, other_name in enumerate(st.session_state.others_list):
        with stats_cols[idx % len(stats_cols)]:
            word_col = f"Слово ({other_name})"
            matched = int((df[word_col] != "---").sum()) if word_col in df.columns else 0
            missing = total - matched
            matched_percent = round(matched / total * 100, 1) if total else 0
            st.markdown(f"### {other_name}")
            st.metric("Всего строк", total)
            st.metric("Найдено соответствий", f"{matched} ({matched_percent}%)")
            st.metric("Пропуски", missing)
            st.progress(matched_percent / 100 if total else 0, text=f"Выравнивание: {matched_percent}%")

    st.divider()
    st.subheader("Экспорт результатов")
    export_col1, export_col2, export_col3 = st.columns(3)
    with export_col1:
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Скачать CSV",
            csv_data,
            f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True,
        )
    with export_col2:
        export_data = {
            "others_list": st.session_state.others_list,
            "base_words": st.session_state.base_words,
            "all_aligns": st.session_state.all_aligns,
            "main_file": st.session_state.main_file,
        }
        zip_buffer = export_all_aligned(export_data, df)
        st.download_button(
            "Экспорт в XML-TEI ZIP",
            zip_buffer,
            f"aligned_corpora_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "application/zip",
            use_container_width=True,
        )
    with export_col3:
        if st.button("Новое сравнение", use_container_width=True):
            for key in ["comp_df", "others_list", "main_file", "base_words", "all_aligns"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
else:
    st.info("Загрузите XML-файлы в боковой панели и нажмите кнопку сравнения.")
