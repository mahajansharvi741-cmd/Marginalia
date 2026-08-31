"""
Marginalia — a free AI study companion for school/college students.

Features:
1. Notes Expander — upload a photo of notes/book page -> OCR -> detailed AI
   explanation, WITH an auto-generated flowchart diagram shown alongside it.
2. Book Reader — paste book/story text -> listen via TTS, with AI
   "meaning/motive" side-notes for readers who want deeper context.

Uses Google's Gemini API (free tier — no credit card needed), good for
students who can't pay per-request API costs.

HOW TO RUN:
1. pip install -r requirements.txt
2. Install Tesseract OCR engine (see README.md for your OS)
3. Get a free Gemini API key at https://aistudio.google.com/apikey
4. Set it as GEMINI_API_KEY environment variable (or Streamlit secret)
5. Run: streamlit run app.py
"""

import os
import json
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import pytesseract
from google import genai
from gtts import gTTS

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Marginalia", page_icon="📚", layout="centered")

dark_mode = st.session_state.get("dark_mode", False)

if dark_mode:
    _bg_grad = "linear-gradient(180deg, #1A1625 0%, #241B36 100%)"
    _ink = "#F0EAFF"
    _ink_soft = "#B8AECF"
    _card_bg = "#2A2140"
    _card_border = "#3D2E5C"
    _hero_grad = "linear-gradient(120deg, #6B4FA0 0%, #C24868 100%)"
    _tab_bg = "#2A2140"
    _tab_selected_bg = "#3D2E5C"
    _uploader_bg = "#241B36"
    _expander_bg = "#1F3A38"
    _expander_text = "#8FE8DE"
    _sidebar_grad = "linear-gradient(180deg, #1F1730 0%, #1A1625 100%)"
    _radio_bg = "#2A2140"
else:
    _bg_grad = "linear-gradient(180deg, #FFF9F5 0%, #FDF4FF 100%)"
    _ink = "#3D3358"
    _ink_soft = "#6B6182"
    _card_bg = "#FFFFFF"
    _card_border = "#F3E8FF"
    _hero_grad = "linear-gradient(120deg, #A78BFA 0%, #FF6B81 100%)"
    _tab_bg = "#F3E8FF"
    _tab_selected_bg = "#FFFFFF"
    _uploader_bg = "#FFFDFB"
    _expander_bg = "#E8FBF9"
    _expander_text = "#2A8A82"
    _sidebar_grad = "linear-gradient(180deg, #FDF4FF 0%, #FFF9F5 100%)"
    _radio_bg = "#FFFFFF"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&family=Poppins:wght@400;500;600&display=swap');

:root {{
    --ink: {_ink};
    --ink-soft: {_ink_soft};
    --paper: {_card_bg};
    --pink: #FF6B81;
    --pink-dark: #E85570;
    --purple: #A78BFA;
    --mint: #4ECDC4;
    --yellow: #FFD93D;
    --card-bg: {_card_bg};
}}

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
}}

/* Main app background */
.stApp {{
    background: {_bg_grad};
}}

/* Headings use the bubbly rounded font */
h1, h2, h3 {{
    font-family: 'Quicksand', sans-serif !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em;
}}

h1 {{
    font-weight: 700 !important;
}}

/* Body text / markdown */
.stMarkdown, p, li, span, label {{
    color: var(--ink) !important;
}}

/* Hero banner — playful gradient */
.hero-banner {{
    background: {_hero_grad};
    color: white;
    padding: 32px 32px;
    border-radius: 24px;
    margin-bottom: 26px;
    box-shadow: 0 8px 24px rgba(167, 139, 250, 0.25);
}}
.hero-banner h1 {{
    color: white !important;
    margin: 0 0 6px 0 !important;
    font-size: 34px !important;
}}
.hero-banner p {{
    color: rgba(255,255,255,0.9) !important;
    margin: 0;
    font-size: 15px;
}}

/* Feature cards */
.feature-card {{
    background: var(--card-bg);
    border-radius: 20px;
    padding: 22px;
    box-shadow: 0 4px 16px rgba(167, 139, 250, 0.12);
    border: 2px solid {_card_border};
}}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background: {_tab_bg};
    padding: 6px;
    border-radius: 16px;
}}
.stTabs [data-baseweb="tab"] {{
    height: 42px;
    border-radius: 12px;
    font-weight: 600;
    color: var(--ink-soft);
}}
.stTabs [aria-selected="true"] {{
    background: {_tab_selected_bg} !important;
    color: var(--pink-dark) !important;
    box-shadow: 0 2px 8px rgba(167, 139, 250, 0.2);
}}

/* Buttons — rounded pill shape, playful */
.stButton button {{
    background: linear-gradient(120deg, var(--pink) 0%, var(--purple) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    font-family: 'Quicksand', sans-serif !important;
    padding: 11px 26px !important;
    transition: transform 0.15s, box-shadow 0.2s !important;
    box-shadow: 0 4px 12px rgba(255, 107, 129, 0.3) !important;
}}
.stButton button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(255, 107, 129, 0.4) !important;
}}

/* Radio buttons (marks selector, upload method) */
.stRadio [role="radiogroup"] {{
    gap: 8px;
}}
.stRadio [role="radiogroup"] label {{
    background: {_radio_bg};
    border-radius: 50px;
    padding: 6px 14px !important;
    border: 2px solid {_card_border};
    color: var(--ink) !important;
}}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {{
    background: {_uploader_bg} !important;
    border: 3px dashed var(--purple) !important;
    border-radius: 20px !important;
}}

/* Camera input */
[data-testid="stCameraInput"] {{
    border-radius: 20px !important;
    overflow: hidden;
}}

/* Expanders */
.streamlit-expanderHeader {{
    background: {_expander_bg} !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    color: {_expander_text} !important;
}}

/* Info/success/warning boxes */
div[data-testid="stAlert"] {{
    border-radius: 16px;
}}

/* Captions */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: var(--ink-soft) !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {_sidebar_grad} !important;
    border-right: none;
}}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {{
    padding: 10px 14px;
    border-radius: 14px;
    margin-bottom: 4px;
    background: {_card_bg};
}}

/* Progress bar */
.stProgress > div > div {{
    background: linear-gradient(90deg, var(--mint), var(--purple)) !important;
    border-radius: 10px;
}}

/* Text inputs / text areas */
.stTextInput input, .stTextArea textarea {{
    background: {_uploader_bg} !important;
    color: var(--ink) !important;
    border-radius: 12px !important;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DAILY_LIMIT = 50
USAGE_FILE = Path("usage_count.json")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


def get_usage_count() -> int:
    if USAGE_FILE.exists():
        return json.loads(USAGE_FILE.read_text()).get("count", 0)
    return 0


def increment_usage_count():
    count = get_usage_count() + 1
    USAGE_FILE.write_text(json.dumps({"count": count}))
    return count


def usage_ok() -> bool:
    if get_usage_count() >= DAILY_LIMIT:
        st.error(
            "This demo has hit its usage cap for now (it's running on a free "
            "personal API key). Please try again later, or run it locally "
            "with your own key — see README.md."
        )
        return False
    return True


def ask_gemini(prompt: str, retries: int = 3) -> str:
    import time

    last_error = None
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash", contents=prompt
            )
            return response.text
        except Exception as e:
            last_error = e
            error_str = str(e)
            # 503 = Google's servers are temporarily overloaded (common on
            # the free tier during high demand) — safe to retry shortly.
            if "503" in error_str or "UNAVAILABLE" in error_str:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    raise last_error


def friendly_error(e: Exception) -> str:
    error_str = str(e)
    if "503" in error_str or "UNAVAILABLE" in error_str:
        return (
            "Gemini's servers are temporarily overloaded (common on the free "
            "tier during busy times). Please wait a few seconds and try again."
        )
    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
        return (
            "You've hit Gemini's free-tier rate limit for now. Wait a minute "
            "and try again."
        )
    return f"Something went wrong: {error_str}"


def check_password() -> bool:
    """Simple password gate. Set APP_PASSWORD as an env var or Streamlit secret."""
    correct_password = os.environ.get("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", None)

    if not correct_password:
        return True

    if st.session_state.get("password_ok", False):
        return True

    st.caption("🔒 This app is password protected.")
    pw = st.text_input("Enter password to access the app", type="password")
    if pw:
        if pw == correct_password:
            st.session_state["password_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


# ---------------- FEATURE 1: NOTES EXPANDER (+ built-in diagram) ----------------

def extract_text_from_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)


def expand_content(raw_text: str, marks, language: str = "English", style: str = "Paragraph") -> str:
    # marks can be an int (5/10/15/20) for exam-style answers, or the string
    # "Just explain" for a plain explanation with no exam formatting at all.
    just_explain = marks == "Just explain"

    if not just_explain:
        # Guidance scales roughly the way Indian university exam answers do —
        # more marks means more depth, structure, and coverage, not just
        # length for its own sake.
        guidance = {
            5: (
                "about 300-400 words. Cover the core definition/concept and "
                "2-3 key points with brief explanations. One short example "
                "is enough. Keep it focused and to the point — this is a "
                "short-answer response."
            ),
            10: (
                "about 700-900 words. Include a clear introduction, 4-6 "
                "well-explained points or sub-topics with headings, at "
                "least one real-world example, and a short conclusion."
            ),
            15: (
                "about 1200-1600 words. Include an introduction, multiple "
                "clearly labeled sections/headings covering all major "
                "aspects of the topic, definitions, detailed explanations, "
                "comparisons or classifications where relevant, 1-2 "
                "real-world examples, and a conclusion. Write like a "
                "strong, well-structured long-answer exam response."
            ),
            20: (
                "a comprehensive, exam-topper-level long answer of about "
                "2500-3200 words. Include: an introduction, a clear "
                "definition section, multiple well-labeled sections/sub-"
                "headings covering every major aspect of the topic in "
                "depth (background, working/process, types or "
                "classification, advantages/disadvantages or comparisons "
                "where relevant, applications, and limitations), 2-3 "
                "real-world examples spread through the answer, and a "
                "strong conclusion. This should read like a complete, "
                "thorough answer a student could write across roughly 6-7 "
                "pages of a full-size sheet."
            ),
        }[marks]
        length_instruction = f"Length and depth required: {guidance}"
        task_instruction = (
            f"Write a complete, well-structured exam answer based on this "
            f"content, as if answering a {marks}-mark question on this topic."
        )
    else:
        length_instruction = (
            "Length: whatever length genuinely and naturally explains the "
            "content well — not padded, not artificially shortened. No "
            "exam mark-scheme formatting at all."
        )
        task_instruction = (
            "Simply explain this content clearly and thoroughly, the way a "
            "good tutor would — NOT as an exam answer, no mark-weightage "
            "structure, no 'introduction/conclusion' exam scaffolding. Just "
            "genuinely useful, well-organized explanation."
        )

    if language == "Hinglish":
        language_instruction = (
            "Write the entire answer in Hinglish — informal, natural "
            "Hindi-English mixed language, written in Roman/English script "
            "(the way Indian students actually text and speak), while still "
            "keeping it clear. Keep technical terms in English where that's "
            "how students normally use them."
        )
    else:
        language_instruction = "Write the entire answer in clear, simple English."

    if style == "Brainstorm/Points":
        style_instruction = (
            "Structure this as a BRAINSTORM-STYLE answer, not full flowing "
            "paragraphs: use short bullet points and sub-points organized "
            "around key concepts, almost like a mind-map written as text. "
            "**Bold every important keyword or term** so they stand out at a "
            "glance. Group related points under short headings. Keep each "
            "bullet concise (1-2 lines) rather than long sentences."
        )
    else:
        style_instruction = (
            "Structure this as flowing paragraphs organized under clear "
            "headings, using **bold** only for key terms and definitions."
        )

    prompt = f"""You are an expert tutor for Indian school/college students.
Below is either raw text extracted (via OCR) from a photo of a student's
notes/textbook page, or a question/topic the student typed directly. If it
looks like OCR text, correct obvious errors by inferring intended meaning.

{task_instruction}

{length_instruction}

Language: {language_instruction}

Format/style: {style_instruction}

Special content handling — apply whichever is relevant:
- If this is a MATHEMATICS problem (equation, calculation, formula-based
  question), solve it step-by-step showing full working, not just the final
  answer. Use LaTeX notation for all math: wrap inline math in single
  dollar signs like $x^2 + 5$ and standalone equations in double dollar
  signs like $$ax^2 + bx + c = 0$$.
- If this is a CASE-STUDY / scenario-based question, structure the answer
  as: brief restatement of the situation, analysis applying the relevant
  concept(s) to the specific scenario, and a clear conclusion/recommendation
  — not a generic textbook definition disconnected from the case.
- Otherwise, treat it as a normal theory/concept question.

Additional formatting rules:
- Use clear markdown headings and sub-headings to organize the answer.
- Where a diagram would help (a process, cycle, architecture, or
  classification), add a line like "*(Diagram: short description of what
  it should show)*" at that point — a real diagram will be generated
  separately and shown alongside this answer.

Content / question:
---
{raw_text}
---

Now write the full answer."""
    return ask_gemini(prompt)


def answer_followup_question(context_text: str, question: str, language: str = "English") -> str:
    """Answer a specific follow-up question grounded in previously extracted notes."""
    language_instruction = (
        "Answer in Hinglish (informal Hindi-English mix, Roman script)."
        if language == "Hinglish"
        else "Answer in clear, simple English."
    )
    prompt = f"""A student uploaded/typed the notes below, and now has a
specific follow-up question about them. Answer the question using the
notes as context — if it's a math problem, solve it step-by-step with
LaTeX (single $ for inline math, double $$ for standalone equations). If
it's a case-based question, analyze the specific scenario rather than
giving a generic definition. {language_instruction}

Notes/content (context):
---
{context_text}
---

Student's question:
---
{question}
---

Answer clearly and directly."""
    return ask_gemini(prompt)


MERMAID_HTML_TEMPLATE = """
<div class="mermaid">
{diagram}
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
</script>
"""


def generate_flowchart(raw_text: str, focus_hint: str = "") -> str:
    prompt = f"""Based on the following notes, create a Mermaid.js flowchart
diagram (use "flowchart TD" syntax) that visually summarizes the key
process, sequence, or relationship described. Keep it to 5-10 nodes with
short, clear labels. If the content has no clear process/sequence to
diagram, create a simple concept map of the main ideas instead.
{f"Focus specifically on: {focus_hint}" if focus_hint else ""}

Return ONLY the raw Mermaid code, nothing else — no markdown fences, no
explanation text.

Notes:
---
{raw_text}
---
"""
    result = ask_gemini(prompt)
    result = result.replace("```mermaid", "").replace("```", "").strip()
    return result


def render_notes_expander():
    st.subheader("📝 Notes Expander")
    st.caption(
        "Upload a photo, snap one, or type a question directly — get a "
        "clear explanation or a full exam-style answer, with diagrams "
        "included. Works for theory, case-study, and math questions."
    )

    marks = st.radio(
        "Answer style",
        options=["Just explain (no exam format)", 5, 10, 15, 20],
        index=0,
        horizontal=True,
        format_func=lambda x: x if x == "Just explain (no exam format)" else f"{x} marks",
        help="'Just explain' gives a plain, clear explanation with no exam mark-scheme structure. Pick marks if you specifically want an exam-style answer.",
    )
    if marks != "Just explain (no exam format)":
        marks = int(marks)
    else:
        marks = "Just explain"

    answer_language = st.radio(
        "Answer language",
        ["English", "Hinglish"],
        horizontal=True,
        help="Hinglish = informal Hindi-English mix, written in Roman script.",
    )

    answer_style = st.radio(
        "Answer format",
        ["Paragraph", "Brainstorm/Points"],
        horizontal=True,
        help="Brainstorm/Points = short bulleted, mind-map style answer with bolded keywords, instead of full paragraphs.",
    )

    input_method = st.radio(
        "How do you want to add your content?",
        ["📁 Upload from gallery", "📷 Take a photo", "⌨️ Type a question"],
        horizontal=True,
        key="notes_input_method",
    )

    raw_text = None
    image = None

    if input_method == "⌨️ Type a question":
        typed_question = st.text_area(
            "Type your question or topic",
            placeholder="e.g. Explain the process of photosynthesis, or solve: 2x + 5 = 15",
            height=120,
        )
        if typed_question.strip():
            raw_text = typed_question.strip()
    else:
        if input_method == "📁 Upload from gallery":
            uploaded_file = st.file_uploader(
                "Upload an image", type=["png", "jpg", "jpeg"], key="notes_upload"
            )
        else:
            uploaded_file = st.camera_input("Take a photo of your notes", key="notes_camera")

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your notes (click to enlarge)", width=220)

    ready = raw_text is not None or image is not None

    if ready and usage_ok() and st.button("✨ Write my answer", key="expand_btn"):
        if image is not None:
            with st.spinner("Reading text from image..."):
                raw_text = extract_text_from_image(image)
            if not raw_text.strip():
                st.error("Couldn't detect any text in this image. Try a clearer photo.")
                raw_text = None
            else:
                with st.expander("Raw extracted text (OCR output)"):
                    st.write(raw_text)

        if raw_text:
            # Save this content so the follow-up question box below can use
            # it as context, even after the page re-runs.
            st.session_state["notes_context"] = raw_text

            expanded = None
            if client is not None:
                label = "Just explain" if marks == "Just explain" else f"{marks}-mark answer"
                with st.spinner(f"Writing your {label}..."):
                    try:
                        expanded = expand_content(raw_text, marks, answer_language, answer_style)
                        increment_usage_count()
                        st.subheader("📖 Answer" if marks == "Just explain" else f"📖 {marks}-Mark Answer")
                        st.markdown(expanded)
                    except Exception as e:
                        st.error(friendly_error(e))

                if expanded:
                    # More marks -> more diagrams, since a 20-mark answer
                    # typically covers several distinct sub-topics.
                    num_diagrams = 1 if (marks == "Just explain" or marks <= 10) else 2
                    for i in range(num_diagrams):
                        with st.spinner(f"Drawing diagram {i + 1} of {num_diagrams}..."):
                            try:
                                focus = (
                                    "the main process/cycle described"
                                    if i == 0
                                    else "a secondary concept, classification, or comparison from the notes"
                                )
                                diagram_code = generate_flowchart(raw_text, focus_hint=focus)
                                increment_usage_count()
                                st.subheader(f"📊 Diagram {i + 1}")
                                components.html(
                                    MERMAID_HTML_TEMPLATE.format(diagram=diagram_code),
                                    height=420,
                                    scrolling=True,
                                )
                                with st.expander(f"View diagram {i + 1} code (Mermaid syntax)"):
                                    st.code(diagram_code, language="text")
                            except Exception as e:
                                st.error(f"Diagram generation failed. {friendly_error(e)}")
            else:
                st.info("Add your Gemini API key to see the AI-written answer.")

    # ---- Follow-up question, grounded in the last uploaded/typed content ----
    if st.session_state.get("notes_context"):
        st.divider()
        st.markdown("**🤔 Ask a specific question about this**")
        st.caption(
            "Ask anything based on the notes above — including case-based "
            "questions or math problems to solve step-by-step."
        )
        followup_q = st.text_input(
            "Your question",
            placeholder="e.g. What would happen in this case if... / Solve for x in the second equation",
            key="followup_question",
        )
        if usage_ok() and st.button("Answer my question", key="followup_btn"):
            if not followup_q.strip():
                st.error("Type a question first.")
            elif client is not None:
                with st.spinner("Thinking..."):
                    try:
                        answer = answer_followup_question(
                            st.session_state["notes_context"], followup_q, answer_language
                        )
                        increment_usage_count()
                        st.markdown(answer)
                    except Exception as e:
                        st.error(friendly_error(e))
            else:
                st.info("Add your Gemini API key to use this feature.")


# ---------------- FEATURE 2: BOOK READER (image -> TTS + MEANING NOTES) ----------------

LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Punjabi": "pa",
    "Hinglish (Hindi-English mix)": "hi",  # closest available TTS voice
}


def translate_for_narration(text: str, language_name: str) -> str:
    """Rewrite the passage in the target language/style for narration."""
    if language_name == "English":
        return text

    if language_name == "Hinglish (Hindi-English mix)":
        instruction = (
            "Rewrite this passage in Hinglish — informal, spoken-style "
            "Hindi-English mixed together, written in Roman/English script "
            "(the way Indian students naturally text each other), keeping "
            "the full meaning intact."
        )
    else:
        instruction = (
            f"Translate this passage into natural, fluent {language_name}, "
            f"in {language_name}'s native script, keeping the full meaning "
            "and tone intact."
        )

    prompt = f"""{instruction}

Passage:
---
{text}
---

Return ONLY the rewritten/translated passage, nothing else."""
    return ask_gemini(prompt)


def generate_meaning_notes(text: str, language_name: str) -> str:
    lang_instruction = (
        "Write your response in English."
        if language_name == "English"
        else f"Write your response in {language_name}."
    )
    prompt = f"""You are a thoughtful literature companion. Below is a passage
from a book/story. Write 2-4 short side-notes explaining the deeper meaning,
emotion, or motive behind key lines — the kind of insight a good teacher
would point out. Keep each note to 1-2 sentences. Format as a bullet list.
{lang_instruction}

Passage:
---
{text}
---
"""
    return ask_gemini(prompt)


def text_to_speech(text: str, lang_code: str) -> str:
    """Generate an mp3 file from text and return its path."""
    tts = gTTS(text=text, lang=lang_code, slow=False)
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts.save(tmp_path)
    return tmp_path


def render_book_reader():
    st.subheader("🎧 Book Reader")
    st.caption(
        "Upload a photo of a book page — hear it read aloud, with notes on "
        "the meaning or emotion behind it."
    )

    language_name = st.selectbox(
        "Language",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=0,
    )
    if language_name == "Hinglish (Hindi-English mix)":
        st.caption(
            "⚠️ Note: Hinglish text will be accurate, but there's no true "
            "Hinglish voice — the audio uses the closest available voice, "
            "so pronunciation may sound slightly off."
        )

    input_method = st.radio(
        "How do you want to add the page?",
        ["📁 Upload from gallery", "📷 Take a photo"],
        horizontal=True,
        key="book_input_method",
    )

    if input_method == "📁 Upload from gallery":
        uploaded_file = st.file_uploader(
            "Upload an image of a book/story page", type=["png", "jpg", "jpeg"], key="book_upload"
        )
    else:
        uploaded_file = st.camera_input("Take a photo of the page", key="book_camera")

    include_notes = st.checkbox("Also explain the meaning/motive behind it", value=True)

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Your page (click to enlarge)", width=220)

        if usage_ok() and st.button("🔊 Read this page"):
            with st.spinner("Reading text from image..."):
                raw_text = extract_text_from_image(image)

            if not raw_text.strip():
                st.error("Couldn't detect any text in this image. Try a clearer photo.")
            elif client is None:
                st.info("Add your Gemini API key to use this feature.")
            else:
                with st.expander("Raw extracted text (OCR output)"):
                    st.write(raw_text)

                passage = raw_text[:2000]

                narration_text = passage
                if language_name != "English":
                    with st.spinner(f"Preparing {language_name} narration..."):
                        try:
                            narration_text = translate_for_narration(passage, language_name)
                            increment_usage_count()
                            with st.expander(f"{language_name} text"):
                                st.write(narration_text)
                        except Exception as e:
                            st.error(f"Translation failed. {friendly_error(e)}")
                            narration_text = passage

                with st.spinner("Generating audio..."):
                    try:
                        lang_code = LANGUAGE_OPTIONS[language_name]
                        audio_path = text_to_speech(narration_text, lang_code)
                        st.audio(audio_path, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Text-to-speech failed: {e}")

                if include_notes:
                    with st.spinner("Thinking about what it means..."):
                        try:
                            notes = generate_meaning_notes(passage, language_name)
                            increment_usage_count()
                            st.markdown("**💭 Meaning & motive notes**")
                            st.markdown(notes)
                        except Exception as e:
                            st.error(friendly_error(e))


# ---------------- MAIN APP ----------------

if not check_password():
    st.stop()

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 4px 0 18px 0;">
            <div style="font-family:'Quicksand',sans-serif; font-weight:700; font-size:22px; color:{_ink};">
                📚 Marginalia
            </div>
            <div style="font-size:12.5px; color:{_ink_soft}; margin-top:2px;">
                Free AI study companion
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["🏠 Home", "📝 Expand Notes", "🎧 Book Reader"],
        label_visibility="collapsed",
    )

    st.divider()
    st.toggle("🌙 Dark mode", key="dark_mode")
    st.caption(f"Usage today: {get_usage_count()}/{DAILY_LIMIT}")
    st.progress(min(get_usage_count() / DAILY_LIMIT, 1.0))

if client is None:
    st.warning(
        "No GEMINI_API_KEY found. Set it as an environment variable before "
        "running this app (see README.md). Get a free key at "
        "https://aistudio.google.com/apikey"
    )

if page == "🏠 Home":
    st.markdown(
        """
        <div class="hero-banner">
            <h1>📚 Marginalia</h1>
            <p>Free AI study companion — notes explained with diagrams, books narrated.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="feature-card" style="height:210px;">
                <div style="font-size:28px;">📝</div>
                <div style="font-family:'Quicksand',sans-serif; font-weight:700; font-size:18px; margin:8px 0 6px; color:var(--ink);">Notes Expander</div>
                <div style="font-size:13.5px; color:var(--ink-soft); line-height:1.5;">
                    Upload, snap, or type a question. Choose exam-style marks
                    or a plain explanation, with diagrams included.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Notes Expander →", use_container_width=True):
            st.session_state["nav_override"] = "📝 Expand Notes"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="feature-card" style="height:210px;">
                <div style="font-size:28px;">🎧</div>
                <div style="font-family:'Quicksand',sans-serif; font-weight:700; font-size:18px; margin:8px 0 6px; color:var(--ink);">Book Reader</div>
                <div style="font-size:13.5px; color:var(--ink-soft); line-height:1.5;">
                    Upload or snap a photo of a book/story page. Hear it read
                    aloud in English, Hindi, Punjabi, or Hinglish, with notes
                    on the meaning behind it.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Book Reader →", use_container_width=True):
            st.session_state["nav_override"] = "🎧 Book Reader"
            st.rerun()

    st.divider()
    st.caption("Made by a BCA student, for students. Free to use.")

elif page == "📝 Expand Notes":
    render_notes_expander()

elif page == "🎧 Book Reader":
    render_book_reader()
