# 📚 Marginalia

**A free AI study companion for school/college students** — turns photos of
notes into exam-ready answers with auto-generated diagrams, and reads book
passages aloud in English, Hindi, Punjabi, or Hinglish with meaning notes.

🔗 **Live demo:** _add your Streamlit link here_

## What it does

- **Notes Expander** — upload a photo, take one, or type a question/topic
  directly. Choose "Just explain" for a plain explanation, or pick exam
  marks (5/10/15/20) for a formatted exam answer. Supports English or
  Hinglish, paragraph or brainstorm/points style, math problems (solved
  step-by-step with proper equations), and case-study questions — with
  1-2 auto-generated flowchart diagrams to match. After generating an
  answer, you can ask follow-up questions grounded in the same notes.
- **Book Reader** — upload a photo of a book/story page and hear it read
  aloud in English, Hindi, Punjabi, or Hinglish, with AI notes on the
  meaning or motive behind key lines, in the same language.
- **Dark mode** — toggle in the sidebar, applies across the whole app.

## Why I built it

NCERT and textbook content is often too brief or dense for students to
actually learn from independently. Marginalia turns a photo of any page
into a properly explained, exam-ready answer — free, so cost isn't a
barrier for students.

## Tech stack

- **Python** + **Streamlit** — app framework and UI
- **Google Gemini API** (free tier) — content generation, translation
- **Tesseract OCR** (`pytesseract`) — text extraction from images
- **Mermaid.js** — auto-generated flowchart diagrams
- **gTTS** — text-to-speech in multiple languages
- Deployed on **Streamlit Community Cloud**

## Project structure

```
study-app/
├── app.py              # Main application (all features)
├── requirements.txt    # Python dependencies
├── packages.txt         # System packages (Tesseract) for cloud deploy
└── README.md
```

---

## Running it locally

### 1. Install Python packages
```bash
cd study-app
pip install -r requirements.txt
```

### 2. Install the Tesseract OCR engine
`pytesseract` is a wrapper — it needs the actual Tesseract program too.

- **Windows**: install from https://github.com/UB-Mannheim/tesseract/wiki,
  then add the install folder to your PATH.
- **Mac**: `brew install tesseract`
- **Linux (Ubuntu/Debian)**: `sudo apt install tesseract-ocr`

### 3. Get a free Gemini API key
Go to https://aistudio.google.com/apikey, sign in, click "Create API key"
— no credit card required.

Then set it as an environment variable:
```bash
# Mac/Linux
export GEMINI_API_KEY="your-key-here"

# Windows PowerShell
$env:GEMINI_API_KEY="your-key-here"
```

### 4. Run it
```bash
streamlit run app.py
```
Opens at http://localhost:8501

---

## Deploying for free (Streamlit Community Cloud)

1. Push this project to a public GitHub repo.
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Click "New app", pick your repo, set main file to `app.py`, deploy.
4. Settings → Secrets, add:
   ```
   GEMINI_API_KEY = "your-key-here"
   APP_PASSWORD = "choose-any-password"
   ```
5. You'll get a live link like `yourname-studyboost.streamlit.app`.

## Roadmap

- [ ] Full-book upload (currently works page-by-page)
- [ ] More Indian regional languages for Book Reader
- [ ] Answer history / saved answers per user

## Notes

- Each visitor gets their own usage cap (15 AI actions per browser session)
  instead of one shared counter across everyone — so one heavy user can't
  use up someone else's quota. This resets if a person reloads the page,
  since there's no login system tracking individual people persistently.
  A real, unresetable per-person limit would need actual user accounts —
  a bigger feature for later if this ever needs it.
- A 20-mark answer uses more AI calls (1 for the answer + 2 for diagrams)
  than a 5-mark one, so it counts more against Gemini's free-tier rate
  limits — a brief wait usually resolves any rate-limit error.
- Hinglish text is generated accurately, but there's no dedicated Hinglish
  TTS voice, so its audio uses the closest available voice.
