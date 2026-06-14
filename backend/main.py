import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from api.upload_routes   import router as upload_router
from api.progress_routes import router as progress_router
from api.report_routes   import router as report_router
from api.copilot_routes  import router as copilot_router
from api.analysis_routes import router as analysis_router

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sports Highlight AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ─────────────────────────────────────────────────────
# Serve /static/** from the static/ folder
app.mount("/static",     StaticFiles(directory="static"),     name="static")

# Serve generated thumbnails and highlight clips directly
os.makedirs("thumbnails", exist_ok=True)
os.makedirs("highlights",  exist_ok=True)
os.makedirs("temp_frames", exist_ok=True)

app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")
app.mount("/highlights",  StaticFiles(directory="highlights"),  name="highlights")
app.mount("/frames",      StaticFiles(directory="temp_frames"), name="frames")

# ── Templates ────────────────────────────────────────────────────────
templates = Jinja2Templates(directory="templates")

# ── HTML Page Routes ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Upload page."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Results dashboard page."""
    return templates.TemplateResponse(request=request, name="dashboard.html")

# ── API Routes ───────────────────────────────────────────────────────
app.include_router(upload_router)
app.include_router(progress_router)
app.include_router(report_router)
app.include_router(copilot_router)
app.include_router(analysis_router)


@app.get("/health")
def health_check():
    return {
        "status": "running",
        "pipeline": "Multimodal Agentic Sports AI v2"
    }
