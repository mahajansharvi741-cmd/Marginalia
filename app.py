"""
StudyBoost — a free AI study companion for school/college students.

Features:
1. Notes Expander  — upload a photo of notes/book page -> OCR -> detailed AI explanation
2. Diagram Generator — turn any topic/process into a visual flowchart
3. Book Reader — paste book/story text -> listen via TTS, with AI "meaning/motive"
                  side-notes for readers who want to understand deeper context

HOW TO RUN:
1. pip install -r requirements.txt
2. Install Tesseract OCR engine (see README.md for your OS)
3. Set your ANTHROPIC_API_KEY as an environment variable
4. Run: streamlit run app.py
"""

import os
import json
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import pytesseract
from gtts import gTTS

# ---------------- CONFIG ----------------
st.set_page_config(page_title="StudyBoost", page_icon="📚", layout="centered")

DAILY_LIMIT = 50
USAGE_FILE = Path("usage_count.json")

try:
    from google import genai

    client = genai.Client(
        api_key=st.secrets["API_key"]
    )
except Exception:
    client = None


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


def check_password() -> bool:
    """Simple password gate. Set APP_PASSWORD as an env var or Streamlit secret."""
    correct_password = os.environ.get("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", None)

    if not correct_password:
        # No password configured -> app is open to everyone.
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

def ask_gemini(prompt: str, max_tokens: int = 1500) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={
            "max_output_tokens": max_tokens
        }
    )
    return response.text



# ---------------- FEATURE 1: NOTES EXPANDER ----------------

def extract_text_from_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)


def expand_content(raw_text: str) -> str:
    prompt = f"""You are a helpful tutor for school/college students.
Below is raw text extracted (via OCR) from a photo of a student's notes or
textbook page. It may contain OCR errors — do your best to infer the
intended meaning.

Your job:
1. Correct obvious OCR mistakes.
2. Expand each point into a clear, detailed explanation a student can
   actually learn from (not just a longer version of the same words).
3. Add a simple real-world example where it helps understanding.
4. Keep the structure organized with headings/bullet points.

Raw extracted text:
---
{raw_text}
---

Write the expanded, detailed explanation now (markdown format)."""
    return ask_gemini(prompt, max_tokens=2000)


def render_notes_expander():
    st.subheader("📝 Notes Expander")
    st.caption("Upload a photo of your notes or textbook page — get it explained in detail.")

    uploaded_file = st.file_uploader(
        "Upload an image", type=["png", "jpg", "jpeg"], key="notes_upload"
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded image", use_container_width=True)

        if usage_ok() and st.button("✨ Expand this content", key="expand_btn"):
            with st.spinner("Reading text from image..."):
                raw_text = extract_text_from_image(image)

            if not raw_text.strip():
                st.error("Couldn't detect any text in this image. Try a clearer photo.")
            else:
                with st.expander("Raw extracted text (OCR output)"):
                    st.write(raw_text)

                if client is not None:
                    with st.spinner("Generating detailed explanation..."):
                        try:
                            expanded = expand_content(raw_text)
                            increment_usage_count()
                            st.subheader("📖 Detailed Explanation")
                            st.markdown(expanded)
                        except Exception as e:
                            st.error(f"Something went wrong calling the AI API: {e}")
                else:
                    st.info("Add your API key to see the AI-expanded explanation.")


# ---------------- FEATURE 2: DIAGRAM GENERATOR ----------------

MERMAID_HTML_TEMPLATE = """
<div class="mermaid">
{diagram}
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
</script>
"""


def generate_flowchart(topic_or_text: str) -> str:
    prompt = f"""Convert the following topic or explanation into a Mermaid.js
flowchart diagram (use "flowchart TD" syntax). Keep it to 5-10 nodes,
using short, clear labels. Return ONLY the raw Mermaid code, nothing else —
no markdown fences, no explanation text.

Topic/content:
---
{topic_or_text}
---
"""
    result = ask_gemini(prompt, max_tokens=600)
    # strip accidental code fences
    result = result.replace("```mermaid", "").replace("```", "").strip()
    return result


def render_diagram_generator():
    st.subheader("📊 Diagram Generator")
    st.caption("Describe a process, cycle, or concept — get a visual flowchart.")

    topic = st.text_area(
        "Describe the topic or paste the explanation",
        placeholder="e.g. The water cycle: evaporation, condensation, precipitation, collection",
        height=120,
    )

    if usage_ok() and st.button("🧭 Generate diagram"):
        if not topic.strip():
            st.error("Please enter a topic or some text first.")
        elif client is not None:
            with st.spinner("Designing the flowchart..."):
                try:
                    diagram_code = generate_flowchart(topic)
                    increment_usage_count()
                    components.html(
                        MERMAID_HTML_TEMPLATE.format(diagram=diagram_code),
                        height=420,
                        scrolling=True,
                    )
                    with st.expander("View diagram code (Mermaid syntax)"):
                        st.code(diagram_code, language="text")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
        else:
            st.info("Add your API key to generate diagrams.")


# ---------------- FEATURE 3: BOOK READER (TTS + MEANING NOTES) ----------------

def generate_meaning_notes(text: str) -> str:
    prompt = f"""You are a thoughtful literature companion. Below is a passage
from a book/story. Write 2-4 short side-notes explaining the deeper meaning,
emotion, or motive behind key lines — the kind of insight a good teacher
would point out. Keep each note to 1-2 sentences. Format as a bullet list.

Passage:
---
{text}
---
"""
    return ask_gemini(prompt, max_tokens=500)


def text_to_speech(text: str) -> str:
    """Generate an mp3 file from text and return its path."""
    tts = gTTS(text=text, lang="en", slow=False)
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts.save(tmp_path)
    return tmp_path


def render_book_reader():
    st.subheader("🎧 Book Reader")
    st.caption(
        "Paste a passage — listen to it read aloud, with optional notes on "
        "the meaning or emotion behind it."
    )

    passage = st.text_area(
        "Paste a passage from your book",
        placeholder="Paste a paragraph or a few paragraphs here...",
        height=180,
    )

    include_notes = st.checkbox("Also explain the meaning/motive behind it", value=True)

    if usage_ok() and st.button("🔊 Read this passage"):
        if not passage.strip():
            st.error("Please paste some text first.")
        else:
            with st.spinner("Generating audio..."):
                try:
                    # Keep TTS input reasonable in length for a demo
                    audio_text = passage[:2000]
                    audio_path = text_to_speech(audio_text)
                    st.audio(audio_path, format="audio/mp3")
                except Exception as e:
                    st.error(f"Text-to-speech failed: {e}")

            if include_notes and client is not None:
                with st.spinner("Thinking about what it means..."):
                    try:
                        notes = generate_meaning_notes(passage)
                        increment_usage_count()
                        st.markdown("**💭 Meaning & motive notes**")
                        st.markdown(notes)
                    except Exception as e:
                        st.error(f"Something went wrong generating notes: {e}")
            elif include_notes:
                st.info("Add your API key to see meaning notes.")


# ---------------- MAIN APP ----------------

st.title("📚 StudyBoost")
st.caption("Free AI study companion — notes explained, diagrams drawn, books narrated.")

if not check_password():
    st.stop()

if client is None:
  st.warning(
    "No GEMINI_API_KEY found. Add it to Streamlit Secrets."
   )

tab1, tab2, tab3 = st.tabs(["📝 Expand Notes", "📊 Generate Diagram", "🎧 Book Reader"])

with tab1:
    render_notes_expander()

with tab2:
    render_diagram_generator()

with tab3:
    render_book_reader()

st.divider()
st.caption("Made by a BCA student, for students. Free to use.")
