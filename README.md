# StudyBoost

A free AI study companion for school/college students, with two features:

1. **📝 Notes Expander** — upload a photo of notes/a textbook page, choose a
   mark weightage (5/10/15/20), and get a full exam-style answer written in
   easy language, with 1-2 diagrams generated to match.
2. **🎧 Book Reader** — upload a photo of a book/story page → hear it read
   aloud (text-to-speech) in English, Hindi, Punjabi, or Hinglish, with
   optional AI notes on the deeper meaning/motive behind key lines, in the
   same language.

Runs on Google's **Gemini API free tier** — no credit card needed, good for
students. (~1,500 free requests/day on the model used here, as of 2026 —
plenty for personal/small-group use.)

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

## 3. Get a free Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Sign in with a Google account
3. Click "Create API key" — no credit card required

Then set it as an environment variable:

**Mac/Linux:**
```bash
export GEMINI_API_KEY="your-key-here"
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-key-here"
```

(Do this in the same terminal you'll run the app from, or add it to your
system environment variables so it persists.)

## 4. Run the app

```bash
streamlit run app.py
```

It'll open in your browser automatically, usually at http://localhost:8501

## What's built

- [x] Image upload → OCR → AI-written exam answer (choose 5/10/15/20 marks),
      with 1-2 diagrams generated to match the answer's depth
- [x] Text-to-speech from photos of book pages (English/Hindi/Punjabi/
      Hinglish), with "meaning/motive" side-notes in the same language
- [x] Daily usage cap to protect your API key from being drained
- [x] Optional password protection (see below)
- [ ] Full-book upload (currently works on pasted passages, not entire PDFs)

Note: a 20-mark answer uses more AI calls (1 for the answer + 2 for
diagrams) than a 5-mark one, so it counts more against your daily usage cap
and Gemini's free-tier rate limits. If you or friends hit a rate-limit
error on heavy use, just wait a minute and try again.

## Password protection

If you deploy this publicly and only want people with the password to use
it, set an `APP_PASSWORD` secret (see deployment steps below). If you skip
it, the app is open to anyone with the link.

## Deploying for free (Streamlit Community Cloud)

1. Push this project to a public GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app", pick your repo, set the main file to `app.py`, deploy.
   `requirements.txt` and `packages.txt` are read automatically — Tesseract
   installs itself from `packages.txt`.
4. In the app's Settings → Secrets, add:
   ```
   GEMINI_API_KEY = "your-key-here"
   APP_PASSWORD = "choose-any-password"
   ```
   Never commit your real key to GitHub — secrets keep it private.
5. You'll get a live link like `yourname-studyboost.streamlit.app` — share
   that with friends and put it on your resume next to the GitHub link.

## Notes for you as a beginner

- All the "AI" logic lives in `ask_gemini()` and the prompt functions in
  `app.py` — tweak the wording there to change how explanations or diagrams
  are generated, without touching anything else.
- `extract_text_from_image()` is where OCR happens. If OCR quality is poor
  on handwritten notes, that's a known Tesseract limitation — it's much
  better at printed text. Handwriting OCR is a good "phase 2" upgrade.
- Gemini's free tier has rate limits (requests per minute/day) — if you or
  friends hit a rate-limit error, just wait a minute and try again.
