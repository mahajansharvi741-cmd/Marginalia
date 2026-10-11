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
- **Mobile-friendly & installable** — top navigation, big tap targets,
  and an "Add to Home Screen" install on phones (see below).

## Why I built it

NCERT and textbook content is often too brief or dense for students to
actually learn from independently. Marginalia turns a photo of any page
into a properly explained, exam-ready answer — free, so cost isn't a
barrier for students.

## Tech stack

- **Python** + **Streamlit** — app framework and UI
- **Google Gemini API** (free tier) — content generation, translation, and
  vision-based text extraction from images (including handwriting)
- **Tesseract OCR** (`pytesseract`) — offline fallback for text extraction
  if no Gemini API key is set
- **Mermaid.js** — auto-generated flowchart diagrams
- **gTTS** — text-to-speech in multiple languages
- Deployed on **Streamlit Community Cloud**

## Project structure

```
study-app/
├── app.py                          # Main application (all features)
├── requirements.txt                # Python dependencies
├── packages.txt                    # System packages (Tesseract) for cloud deploy
├── .gitignore                      # Keeps secrets out of GitHub
├── .streamlit/
│   ├── config.toml                 # Theme + static file serving
│   └── secrets.toml.example        # Template for your keys (copy -> secrets.toml)
├── static/
│   ├── manifest.json               # Makes the app installable on phones
│   └── icon-192.png, icon-512.png, apple-touch-icon.png
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

## Putting it on GitHub

Streamlit Community Cloud deploys straight from a GitHub repo, so do this first.

1. Create a free account at https://github.com if you don't have one.
2. Click **New repository**, name it (e.g. `marginalia`), choose Public
   (or Private), and **don't** tick "Add a README" — you already have one.
3. In a terminal, from inside the project folder:
   ```bash
   cd study-app
   git init
   git add .
   git commit -m "Marginalia: first commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/marginalia.git
   git push -u origin main
   ```
4. Refresh the GitHub page — you should see `app.py`, `requirements.txt`,
   `packages.txt`, `static/` and `.streamlit/config.toml`.
5. **Check that `secrets.toml` is NOT in the repo.** `.gitignore` already
   blocks it, but if you ever committed a key by mistake, delete that key
   at https://aistudio.google.com/apikey and create a new one — removing the
   file isn't enough, it stays in Git history.

No terminal? On the new repo page click **uploading an existing file** and
drag in everything from `study-app/` (including the `static` and `.streamlit`
folders). Don't upload any `secrets.toml`.

Later updates: edit files, then `git add . && git commit -m "what changed" && git push`.
Streamlit Cloud redeploys automatically.

## Deploying for free (Streamlit Community Cloud)

1. Push this project to GitHub (see above).
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Click "New app", pick your repo, set main file to `app.py`, deploy.
4. Settings → Secrets, add:
   ```
   GEMINI_API_KEY = "your-key-here"
   APP_PASSWORD = "choose-any-password"
   ```
5. You'll get a live link like `yourname-marginalia.streamlit.app`.
   (Secrets format: see `.streamlit/secrets.toml.example`.)

## Installing it on a phone

Open the live link in Chrome (Android) or Safari (iPhone), then use
**Add to Home Screen** / **Install app**. It opens full-screen with the
Marginalia icon. It still needs an internet connection — it isn't an
offline app.

Heads-up: on Streamlit Community Cloud the install prompt may not appear,
because the page wrapping your app belongs to Streamlit, not you. Adding it
to the home screen as a plain shortcut still works. Full install support is
reliable when you host the app yourself at a root URL (Render, Railway, a VPS).

## Setting up Google Login (optional)

By default the app uses simple password protection (`APP_PASSWORD` above).
If you'd rather let people sign in with their Google account instead, set
this up — it's free but requires creating your own Google OAuth credentials.

1. Go to https://console.cloud.google.com/, create a new project (or use an
   existing one).
2. Go to **APIs & Services → OAuth consent screen**. Choose "External",
   fill in the basic app info (name, your email), and save. You don't need
   to submit for verification for personal/small-group use.
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth
   client ID**. Choose "Web application".
4. Under **Authorized redirect URIs**, add:
   ```
   https://YOUR-APP-NAME.streamlit.app/oauth2callback
   ```
   (use your actual live app URL — and add `http://localhost:8501/oauth2callback`
   too if you also want Google login to work locally)
5. Click Create — you'll get a **Client ID** and **Client Secret**. Copy both.
6. In Streamlit Cloud → Settings → Secrets, add:
   ```
   [auth]
   redirect_uri = "https://YOUR-APP-NAME.streamlit.app/oauth2callback"
   cookie_secret = "any-random-long-string-you-make-up"

   [auth.google]
   client_id = "your-client-id-here"
   client_secret = "your-client-secret-here"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```
7. Save — the app will now show a "Log in with Google" button instead of
   the password field. (If these secrets aren't set, the app automatically
   falls back to the password gate, so nothing breaks in the meantime.)

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
- Answers, diagrams and follow-up questions now stay on screen after you ask
  a follow-up (results are kept in the session instead of vanishing).
- On a phone, text boxes only save what you typed when you tap outside
  them — tap elsewhere before pressing "Write my answer".
- Hinglish text is generated accurately, but there's no dedicated Hinglish
  TTS voice, so its audio uses the closest available voice.
- Text extraction from images now uses Gemini's vision capability (much
  better at handwriting than the earlier Tesseract-only version), which
  means it counts as one more AI action against the session usage cap.
