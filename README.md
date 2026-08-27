# StudyBoost

A free AI study companion for school/college students, with three features:

1. **📝 Notes Expander** — upload a photo of notes/a textbook page → get it
   OCR'd and expanded into a detailed, easy-to-understand explanation.
2. **📊 Diagram Generator** — describe any topic, process, or cycle → get an
   auto-generated visual flowchart (via Mermaid.js).
3. **🎧 Book Reader** — paste a passage from a book → listen to it read aloud
   (text-to-speech), with optional AI notes on the deeper meaning/motive
   behind key lines.

## 1. Install Python packages

```bash
cd study-app
pip install -r requirements.txt
```

## 2. Install the Tesseract OCR engine

`pytesseract` is just a Python wrapper — it needs the actual Tesseract
program installed on your machine too.

- **Windows**: download the installer from
  https://github.com/UB-Mannheim/tesseract/wiki and install it. Then add
  the install folder (e.g. `C:\Program Files\Tesseract-OCR`) to your PATH.
- **Mac**: `brew install tesseract`
- **Linux (Ubuntu/Debian)**: `sudo apt install tesseract-ocr`

## 3. Get an API key

This app uses Claude (Anthropic) to expand the text. Get a free-tier key at
https://console.anthropic.com/ (sign up → API Keys → Create Key).

Then set it as an environment variable:

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

(Do this in the same terminal you'll run the app from, or add it to your
system environment variables so it persists.)

## 4. Run the app

```bash
streamlit run app.py
```

It'll open in your browser automatically, usually at http://localhost:8501

## What's built

- [x] Image upload → OCR → AI-expanded content
- [x] Auto-generate flowcharts/diagrams (Mermaid syntax + mermaid.js)
- [x] Text-to-speech for passages, with "meaning/motive" side-notes
- [x] Daily usage cap to protect your API key from being drained
- [ ] Full-book upload (currently works on pasted passages, not entire PDFs)
- [ ] Deploy for free (see deployment steps below)
- [ ] Longer-term sustainable free-for-students cost model

## Deploying for free (Streamlit Community Cloud)

1. Push this project to a public GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app", pick your repo, set the main file to `app.py`, deploy.
   `requirements.txt` and `packages.txt` are read automatically — Tesseract
   installs itself from `packages.txt`.
4. In the app's Settings → Secrets, add:
   ```
   ANTHROPIC_API_KEY = "your-key-here"
   APP_PASSWORD = "choose-any-password"
   ```
   Never commit your real key to GitHub — secrets keep it private. If you
   skip `APP_PASSWORD`, the app is open to anyone with the link.
5. You'll get a live link like `yourname-studyboost.streamlit.app` — share
   that with friends and put it on your resume next to the GitHub link.

## Notes for you as a beginner

- All the "AI" logic lives in the `expand_content()` function in `app.py` —
  that's the prompt sent to Claude. Tweak the wording there to change how
  explanations are written (more examples, simpler language, exam-focused,
  etc.) without touching any other code.
- `extract_text_from_image()` is where OCR happens. If OCR quality is poor
  on handwritten notes, that's a known Tesseract limitation — it's much
  better at printed text. Handwriting OCR is a good "phase 2" upgrade.
