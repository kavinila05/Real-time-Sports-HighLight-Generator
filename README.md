#  AI Sports Highlight Generator

> **Multi-modal Agentic Pipeline** — automatically analyzes sports match videos using vision AI, speech recognition, and crowd audio analysis to detect key events, generate highlight clips, create broadcast-quality thumbnails, and answer questions about the match.

Built for the **Multimodal Agentic Track** problem statement:
> *Real-time Sports Highlight Generator — Multi-modal pipeline analyzing video frames, commentary audio, and crowd signals to detect key events and auto-generate highlights, captions, and thumbnails.*

---

##  Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│                                                         │
│  Web UI (FastAPI + Jinja2)                              │
│  localhost:8000                                         │
│  ├── / (Upload Page)                                    │
│  └── /dashboard (Report)                                │
│                                                         │
└─────────────────────┬───────────────────────────────────┘
                      │  HTTP (REST API)
┌─────────────────────▼───────────────────────────────────┐
│                  FASTAPI BACKEND                        │
│                  backend/main.py                        │
│                                                         │
│  POST /upload/        →  Intake Agent                   │
│  POST /analyze/{id}   →  Pipeline Orchestrator          │
│  GET  /progress/{id}  →  Progress Service               │
│  GET  /report/{id}    →  Storage Service                │
│  POST /copilot/ask    →  Q&A Engine                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              MULTIMODAL PIPELINE                        │
│         (runs in background thread)                     │
│                                                         │
│  Stage 1  →  Extract Frames      (OpenCV)               │
│  Stage 1b →  OCR Scoreboard      (OpenCV contours)      │
│  Stage 2  →  Audio Extraction    (MoviePy)              │
│  Stage 2  →  Crowd Energy Spikes (librosa RMS)          │
│  Stage 3  →  Commentary Analysis (Whisper + keywords)   │
│  Stage 4  →  Sport Detection     (CLIP zero-shot)       │
│  Stage 5  →  Vision Analysis     (CLIP zero-shot)       │
│  Stage 6  →  Event Processing    (rule-based scoring)   │
│  Stage 7  →  Multimodal Fusion   (confidence fusion)    │
│  Stage 8  →  Highlight Ranking   (score sort)           │
│  Stage 9  →  Clip Generation     (MoviePy subclip)      │
│  Stage 10 →  Thumbnail Gen       (Pillow + OpenCV)      │
│  Stage 11 →  Match Summary       (template NLG)         │
└─────────────────────────────────────────────────────────┘
```

---

##  AI Models Used

| Agent | Model/Libraries | Task | Library |
|---|---|---|---|
| **Sport Detection Agent** | `openai/clip-vit-base-patch32` | Zero-shot image classification to identify Cricket, Football, Basketball, or Badminton from sampled frames | HuggingFace Transformers |
| **Vision Agent** | `openai/clip-vit-base-patch32` | Zero-shot event classification per frame — detects wickets, sixes, goals, dunks, smashes, celebrations, etc. | HuggingFace Transformers |
| **Commentary Agent** | `openai/whisper-base` | Automatic Speech Recognition — transcribes the match audio, then applies sport-specific keyword matching to detect commentary events | OpenAI Whisper |
| **Audio Agent** | `librosa` RMS energy | Signal processing — computes Root Mean Square energy across the audio track to detect crowd excitement spikes above 1.5σ threshold | librosa |
| **OCR Agent** | `OpenCV` contour detection | Detects scoreboard / overlay regions in frames using brightness thresholding and contour analysis (optional `pytesseract` for text extraction) | OpenCV |
| **Fusion Agent** | Rule-based multimodal fusion | Correlates vision detections, audio spikes (±3s window), and commentary keywords to compute a fused confidence score per event | Custom |
| **Highlight Agent** | Rule-based selection | Applies sport-specific caps, minimum 10s gap between clips, and confidence thresholds to select the final highlight reel | Custom |
| **Summary Agent** | Template NLG | Generates natural-language match summaries from structured pipeline output — no external LLM required, fully offline | Custom |
| **Q&A Copilot** | Rule-based intent parsing | Answers natural-language questions about the match (events, highlights, timestamps, confidence, crowd reactions) by querying the stored report | Custom |

### Why CLIP for Sport Detection and Vision?

CLIP (Contrastive Language-Image Pretraining) by OpenAI is a zero-shot vision model — it scores how well an image matches a text description without being fine-tuned on sports data. This means the pipeline works out of the box for all four sports without any labeled training data.

For each frame it computes similarity scores against sport-specific text prompts like:
- Cricket: `"a cricket wicket"`, `"a cricket batsman hitting six"`, `"players celebrating"`
- Football: `"a football goal"`, `"football penalty kick"`, `"football goalkeeper save"`
- Basketball: `"a slam dunk"`, `"a basketball 3 pointer"`, `"basketball scoring"`
- Badminton: `"badminton smash"`, `"badminton winning point"`, `"badminton celebration"`

The label with the highest softmax probability is selected as the event for that frame.

### Why Whisper for Commentary?

Whisper (`base` model, ~74M parameters) performs robust multilingual ASR. It transcribes the audio track in one pass and the result is matched against a sport-specific keyword dictionary to identify events mentioned by commentators — completely offline, no API key needed.

---

## Supported Sports

| Sport | Detection | Key Events Detected |
|---|---|---|
| 🏏 **Cricket** | CLIP majority vote across frames | Wicket, Six (maximum), Boundary (four), Celebration |
| ⚽ **Football** | CLIP majority vote across frames | Goal, Penalty kick, Goalkeeper save, Celebration |
| 🏀 **Basketball** | CLIP majority vote across frames | Slam dunk, 3-pointer, Basket scored, Celebration |
| 🏸 **Badminton** | CLIP majority vote across frames | Smash, Winning point, Rally, Match point |

Each sport has its own:
- CLIP prompt set for event detection
- Whisper keyword dictionary for commentary matching
- Confidence threshold for highlight selection (Cricket: 0.85, Football: 0.75, Badminton: 0.70, Basketball: 0.65)
- Sport-aware accent color in thumbnails (Purple, Green, Orange, Sky-blue)
- Sport-aware minor event labels (Delivery / Possession / Play / Rally)

---

## Project Structure

```
sport-highlight-generator/
│
├── backend/                        # FastAPI server + AI pipeline
    ├── main.py                     # App entry point, routes, static files
    ├── requirements.txt
    ├── regen_thumbnails.py
    │
    ├── agents/                     # AI processing agents
    │   ├── sport_detection_agent.py   # CLIP sport classifier
    │   ├── vision_agent.py            # CLIP event detector (per frame)
    │   ├── audio_agent.py             # librosa crowd energy spikes
    │   ├── commentary_agent.py        # Whisper ASR + keyword matching
    │   ├── fusion_agent.py            # Multimodal confidence fusion
    │   ├── ranking_agent.py           # Score-sort highlight ranking
    │   ├── highlight_agent.py         # Smart highlight selection + manifest
    │   ├── summary_agent.py           # Template-based NLG match summary
    │   ├── intake_agent.py            # Upload processing coordinator
    │   ├── ocr_agent.py               # Scoreboard detection (OpenCV)
    │   └── pipeline_orchestrator.py   # 10-stage pipeline runner
    │
    ├── api/                        # FastAPI route handlers
    │   ├── upload_routes.py           # POST /upload/
    │   ├── analysis_routes.py         # POST /analyze/{id}
    │   ├── progress_routes.py         # GET  /progress/{id}
    │   ├── report_routes.py           # GET  /report/{id}, /report/latest
    │   └── copilot_routes.py          # POST /copilot/ask
    │
    ├── services/                   # Infrastructure layer
    │   ├── video_service.py           # Frame extraction, audio extraction
    │   ├── clip_service.py            # Highlight clip cutting (MoviePy)
    │   ├── thumbnail_service.py       # HD thumbnail generation (Pillow)
    │   ├── audio_service.py           # Audio analysis helpers
    │   ├── event_service.py           # Event processing + timestamp calc
    │   ├── storage_service.py         # In-memory result store
    │   ├── progress_service.py        # In-memory progress tracker
    │   └── thumbnail_service.py       # 1280×720 Pillow thumbnail generator
    │
    ├── templates/                  # Jinja2 HTML pages
    │   ├── index.html                 # Upload page
    │   └── dashboard.html             # Results dashboard
    │
    ├── static/                     # Web assets
    │   ├── css/style.css              # Full dark-theme UI stylesheet
    │   └── js/
    │       ├── upload.js              # Upload + progress polling
    │       └── dashboard.js           # Dashboard rendering + copilot
    │
    ├── highlights/                 # Generated .mp4 clip files
    ├── thumbnails/                 # Generated .jpg thumbnail files
    ├── uploads/                    # Uploaded video files
    └── temp_frames/                # Generated Sampled video frames (JPEG)

```

---

##  Pipeline — Step by Step

When a video is uploaded and analyzed, the following 10 stages run in sequence in a background thread. Progress is reported as 0–100% and polled by the UI every second.

| % | Stage | What Happens |
|---|---|---|
| 10% | **Frame Extraction** | OpenCV samples 10 evenly-spaced frames from the video. Frame filenames encode the frame number (e.g. `frame_450.jpg`) which is used to compute accurate timestamps via `frame_number / fps`. |
| 10% | **OCR Detection** | Each frame is analyzed for bright rectangular regions at the top/bottom 15% (where scoreboards live). Optional Tesseract OCR extracts any score text found. |
| 25% | **Audio Extraction + Spike Detection** | MoviePy extracts the audio track as a WAV file. librosa computes RMS energy in short windows and flags any frame exceeding `mean + 1.5σ` as a crowd excitement spike. Top 20 spikes are returned. |
| 40% | **Commentary Analysis** | Whisper `base` transcribes the full audio. The transcript is matched against a sport-specific keyword dictionary — e.g. "bowled", "caught", "gone" → `wicket`; "dunk", "three" → `dunk/three_pointer`. |
| 55% | **Vision Analysis** | CLIP processes each sampled frame against sport-specific text prompts. The label with the highest softmax score is assigned to that frame with a confidence value. |
| 70% | **Event Processing** | Normal-play frames are filtered out. Remaining detections are scored for importance (high: wickets, goals, dunks; medium: saves, rallies, penalties). Timestamps are computed from frame numbers. |
| 80% | **Multimodal Fusion** | Each candidate event's confidence is boosted: +0.2 if a crowd spike occurs within 3 seconds, +0.25 if commentary keywords were detected. Events above the sport-specific threshold are marked as highlights. Sport-aware minor labels replace the generic `minor_play` string. Duplicate timestamps are de-duplicated. |
| 85% | **Highlight Ranking + Selection** | Events are sorted by score (confidence + audio_match bonus). `highlight_agent` applies a sport-specific cap (e.g. max 6 for Cricket), enforces a minimum 10s gap between clips, and builds a manifest with human-readable captions. |
| 90% | **Clip + Thumbnail Generation** | For each selected highlight, MoviePy cuts a ±5–8s clip around the timestamp. Pillow generates a 1280×720 JPEG thumbnail with: sharpness/contrast enhancement, gradient top ribbon (rank pill + sport name), gradient footer (event title + timestamp badge + confidence bar). |
| 95% | **Match Summary** | `summary_agent` produces a structured report: headline sentence, body paragraph, key stats dict, and per-event-type breakdown counts. |
| 100% | **Report Saved** | The full result dict is stored in memory and served at `GET /report/{video_id}`. |

---

##  Web Dashboard Sections

| Section | What It Shows |
|---|---|
| **Match Overview** | Sport · Duration · Highlights count · Total Events · FPS · Resolution. Event breakdown tiles (Wicket: 4, Six: 2 …) |
| **AI Summary Bar** | One-paragraph natural-language summary generated by `summary_agent` |
| **Event Timeline** | All events sorted by timestamp with colored badges (WICKET! = red, SIX! = green, DUNK! = orange, etc.), crowd audio tags |
| **Top Moments** | Top 5 highlight events ranked by confidence. Click any to open the video clip in a modal player |
| **Highlight Gallery** | Grid of highlight tiles showing thumbnail image, event name, timestamp, confidence bar. Click → plays MP4 clip |
| **Highlight Thumbnails** | Dedicated section of 1280×720 HD thumbnail images (pure image viewer, click to enlarge in lightbox) |
| **Crowd Energy Chart** | Chart.js bar chart of all crowd energy spikes — x-axis = timestamp, y-axis = RMS energy level |
| **Q&A Copilot** | Chat interface — type any question about the match and get a structured answer pulled from the report |

---

##  Setup & Running

### Prerequisites

- Python 3.10+
- FFmpeg installed and on PATH (required by MoviePy / Whisper)
- ~4 GB disk space for PyTorch + model weights

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Start the Server

```bash
# Must run from inside the backend/ folder
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.


---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Upload page (HTML) |
| `GET` | `/dashboard` | Results dashboard (HTML) |
| `POST` | `/upload/` | Upload a video file. Returns `video_id`, detected sport, metadata |
| `POST` | `/analyze/{video_id}` | Start the analysis pipeline in a background thread |
| `GET` | `/progress/{video_id}` | Poll analysis progress — returns `{stage, progress}` (0–100) |
| `GET` | `/report/{video_id}` | Full JSON analysis report |
| `GET` | `/report/latest` | Latest stored report (no ID needed) |
| `POST` | `/copilot/ask` | `{question, video_id}` → `{answer}` |
| `GET` | `/health` | Server health check |
| `GET` | `/thumbnails/{file}` | Serve generated thumbnail JPEG |
| `GET` | `/highlights/{file}` | Serve generated highlight MP4 |
| `GET` | `/docs` | Auto-generated Swagger UI |

For UI Reference Open **http://localhost:8000/docs** in your browser.

### Example: Upload + Analyze

```bash
# 1. Upload
curl -X POST http://localhost:8000/upload/ \
  -F "file=@match.mp4"
# → {"video_id": "abc123", "sport": "Cricket", ...}

# 2. Start analysis
curl -X POST http://localhost:8000/analyze/abc123

# 3. Poll progress
curl http://localhost:8000/progress/abc123
# → {"stage": "Running vision analysis", "progress": 55}

# 4. Get report
curl http://localhost:8000/report/abc123

# 5. Ask a question
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many wickets?", "video_id": "abc123"}'
# → {"answer": "3 wicket(s) detected at: 00:12, 00:45, 01:23."}
```

---

##  Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.136.3 | Web framework + API server |
| `uvicorn` | 0.49.0 | ASGI server |
| `torch` | 2.12.0 | PyTorch — required by CLIP and Whisper |
| `transformers` | 4.52.4 | HuggingFace — CLIP model loading |
| `openai-whisper` | 20240930 | Speech recognition for commentary |
| `librosa` | 0.10.2 | Audio signal processing (crowd energy) |
| `opencv-python` | 4.13.0 | Frame extraction, OCR, thumbnail seek |
| `pillow` | 11.3.0 | HD thumbnail rendering with Pillow |
| `moviepy` | 2.2.1 | Audio extraction + clip cutting |
| `jinja2` | 3.1.6 | HTML template rendering |
| `aiofiles` | 24.1.0 | Async static file serving |
| `customtkinter` | 5.2.2 | Desktop app UI (frontend only) |

---

##  How It All Connects

```
User uploads video
       │
       ▼
intake_agent.py
  ├── save_uploaded_video()     → uploads/
  ├── extract_video_metadata()  → fps, resolution, duration
  ├── extract_sample_frames()   → temp_frames/frame_N.jpg
  └── detect_sport()            → "Cricket" / "Football" / ...
       │
       ▼
pipeline_orchestrator.py  (background thread)
  │
  ├── [OCR]        ocr_agent.analyze_frames_for_scores()
  │                  └── OpenCV contour detection on top/bottom strips
  │
  ├── [AUDIO]      audio_agent.detect_audio_spikes()
  │                  └── librosa RMS → spikes above mean + 1.5σ
  │
  ├── [COMMENTARY] commentary_agent.detect_commentary_events()
  │                  └── whisper.transcribe() → keyword dict match
  │
  ├── [VISION]     vision_agent.analyze_frames()
  │                  └── CLIP(image, sport_labels) → event + confidence
  │
  ├── [EVENTS]     event_service.process_events()
  │                  └── filter normals, score importance, compute timestamps
  │
  ├── [FUSION]     fusion_agent.fuse_multimodal_events()
  │                  └── audio boost + commentary boost → highlight decision
  │
  ├── [RANKING]    ranking_agent.rank_highlights()
  │                  └── sort by score, tag top_highlight
  │
  ├── [SELECTION]  highlight_agent.select_highlights()
  │                  └── sport cap + min gap filter + manifest
  │
  ├── [CLIPS]      clip_service.generate_highlight_clip()
  │                  └── moviepy.subclipped(ts-5, ts+8)
  │
  ├── [THUMBNAILS] thumbnail_service.generate_thumbnail()
  │                  └── OpenCV seek → Pillow enhance + overlay → 1280×720 JPEG
  │
  └── [SUMMARY]    summary_agent.generate_match_summary()
                     └── template NLG → headline + body + stats
       │
       ▼
storage_service.save_analysis_result()  → in-memory dict

       │
       ▼
Web Dashboard (GET /dashboard)
  ├── Match Overview tiles
  ├── Event Timeline (colored badges)
  ├── Top Moments (click → video modal)
  ├── Highlight Gallery (thumbnail + clip)
  ├── Highlight Thumbnails (pure image lightbox)
  ├── Crowd Energy Bar Chart (Chart.js)
  └── Q&A Copilot (copilot_routes.answer_question)
```

---

##  Known Limitations

- **In-memory storage** — analysis results are lost when the server restarts. A production version would use a database (SQLite/PostgreSQL).
- **CPU inference** — CLIP and Whisper run on CPU by default. On a modern CPU expect 2–5 minutes per video. GPU support can be enabled by modifying `device` in the model loading calls.
- **10 sampled frames** — the pipeline samples only 10 frames from the full video for speed. Very long matches may miss events between sample points.
- **Whisper `base` model** — the base model (~74M params) gives reasonable transcription but may miss commentary in noisy crowd environments. Upgrade to `small` or `medium` for better accuracy at the cost of speed.
- **No authentication** — the API has no auth layer. Do not expose to the public internet as-is.

---

##  Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request

---

##  Acknowledgements

- [OpenAI CLIP](https://github.com/openai/CLIP) — zero-shot vision model
- [OpenAI Whisper](https://github.com/openai/whisper) — speech recognition
- [HuggingFace Transformers](https://huggingface.co/transformers) — model hosting
- [librosa](https://librosa.org) — audio analysis
- [FastAPI](https://fastapi.tiangolo.com) — web framework
- [MoviePy](https://zulko.github.io/moviepy/) — video processing
- [Pillow](https://pillow.readthedocs.io) — image processing
- [Chart.js](https://www.chartjs.org) — crowd energy visualization
