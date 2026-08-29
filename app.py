"""
StudyBoost — a free AI study companion for school/college students.

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
st.set_page_config(page_title="StudyBoost", page_icon="📚", layout="centered")

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


def expand_content(raw_text: str, marks: int) -> str:
    # Guidance scales roughly the way Indian university exam answers do —
    # more marks means more depth, structure, and coverage, not just length
    # for its own sake.
    guidance = {
        5: (
            "about 300-400 words. Cover the core definition/concept and 2-3 "
            "key points with brief explanations. One short example is enough. "
            "Keep it focused and to the point — this is a short-answer response."
        ),
        10: (
            "about 700-900 words. Include a clear introduction, 4-6 well-"
            "explained points or sub-topics with headings, at least one "
            "real-world example, and a short conclusion."
        ),
        15: (
            "about 1200-1600 words. Include an introduction, multiple clearly "
            "labeled sections/headings covering all major aspects of the "
            "topic, definitions, detailed explanations, comparisons or "
            "classifications where relevant, 1-2 real-world examples, and a "
            "conclusion. Write like a strong, well-structured long-answer "
            "exam response."
        ),
        20: (
            "a comprehensive, exam-topper-level long answer of about 2500-3200 "
            "words. Include: an introduction, a clear definition section, "
            "multiple well-labeled sections/sub-headings covering every major "
            "aspect of the topic in depth (background, working/process, types "
            "or classification, advantages/disadvantages or comparisons where "
            "relevant, applications, and limitations), 2-3 real-world examples "
            "spread through the answer, and a strong conclusion. This should "
            "read like a complete, thorough answer a student could write "
            "across roughly 6-7 pages of a full-size sheet."
        ),
    }[marks]

    prompt = f"""You are an expert exam-answer writing tutor for Indian
school/college students. Below is raw text extracted (via OCR) from a
photo of a student's notes or textbook page. It may contain OCR errors —
correct them by inferring the intended meaning.

Write a complete, well-structured exam answer based on this content, as if
answering a {marks}-mark question on this topic.

Length and depth required: {guidance}

Formatting rules:
- Use clear markdown headings and sub-headings to organize the answer.
- Use bullet points or numbered lists where it improves clarity.
- Use **bold** for key terms and definitions.
- Write in simple, clear language a student can actually understand and
  reuse in their own words — avoid overly complex jargon without explaining
  it first.
- Where a diagram would help (a process, cycle, architecture, or
  classification), add a line like "*(Diagram: short description of what
  it should show)*" at that point — a real diagram will be generated
  separately and shown alongside this answer.

Raw extracted text:
---
{raw_text}
---

Now write the full {marks}-mark answer."""
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
        "Upload a photo of your notes or textbook page — get a full exam-"
        "style answer written for you, with diagrams included."
    )

    marks = st.radio(
        "Answer length (marks)",
        options=[5, 10, 15, 20],
        index=1,
        horizontal=True,
        help="Choose how long/detailed the answer should be, matching typical exam mark weightage.",
    )

    uploaded_file = st.file_uploader(
        "Upload an image", type=["png", "jpg", "jpeg"], key="notes_upload"
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded image (click to enlarge)", width=220)

        if usage_ok() and st.button("✨ Write my answer", key="expand_btn"):
            with st.spinner("Reading text from image..."):
                raw_text = extract_text_from_image(image)

            if not raw_text.strip():
                st.error("Couldn't detect any text in this image. Try a clearer photo.")
            else:
                with st.expander("Raw extracted text (OCR output)"):
                    st.write(raw_text)

                expanded = None
                if client is not None:
                    with st.spinner(f"Writing your {marks}-mark answer..."):
                        try:
                            expanded = expand_content(raw_text, marks)
                            increment_usage_count()
                            st.subheader(f"📖 {marks}-Mark Answer")
                            st.markdown(expanded)
                        except Exception as e:
                            st.error(friendly_error(e))

                    if expanded:
                        # More marks -> more diagrams, since a 20-mark answer
                        # typically covers several distinct sub-topics.
                        num_diagrams = 1 if marks <= 10 else 2
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

    uploaded_file = st.file_uploader(
        "Upload an image of a book/story page", type=["png", "jpg", "jpeg"], key="book_upload"
    )
    include_notes = st.checkbox("Also explain the meaning/motive behind it", value=True)

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded page (click to enlarge)", width=220)

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

st.title("📚 StudyBoost")
st.caption("Free AI study companion — notes explained with diagrams, books narrated.")

if not check_password():
    st.stop()

if client is None:
    st.warning(
        "No GEMINI_API_KEY found. Set it as an environment variable before "
        "running this app (see README.md). Get a free key at "
        "https://aistudio.google.com/apikey"
    )

tab1, tab2 = st.tabs(["📝 Expand Notes", "🎧 Book Reader"])

with tab1:
    render_notes_expander()

with tab2:
    render_book_reader()

st.divider()
st.caption("Made by a BCA student, for students. Free to use.")
