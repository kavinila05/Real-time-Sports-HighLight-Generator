"""
Copilot Routes
--------------
GET  /copilot/          — health check
POST /copilot/ask       — answer a question about the match

The Q&A is fully rule-based (no external LLM required) so it
works offline.  It reads the stored analysis report and produces
natural-language answers to common match questions.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from services.storage_service import get_analysis_result

router = APIRouter(
    prefix="/copilot",
    tags=["Copilot"]
)


# ── Request model ──────────────────────────────────────────────────
class CopilotRequest(BaseModel):
    question: str
    video_id: Optional[str] = None


# ── Health ─────────────────────────────────────────────────────────
@router.get("/")
def copilot_status():
    return {"message": "Copilot Ready"}


# ── Ask ────────────────────────────────────────────────────────────
@router.post("/ask")
def ask_copilot(req: CopilotRequest):
    """
    Answer a natural-language question about a specific match report.
    Falls back to a generic answer if no report is found.
    """

    report = {}
    if req.video_id:
        report = get_analysis_result(req.video_id) or {}

    answer = answer_question(req.question.strip(), report)
    return {"answer": answer}


# ── Answer Engine ──────────────────────────────────────────────────

def _fmt_time(sec):
    try:
        s = float(sec)
        m = int(s // 60)
        r = int(s % 60)
        return f"{m:02d}:{r:02d}"
    except Exception:
        return "00:00"


def _fmt_pct(val):
    try:
        return f"{round(float(val) * 100)}%"
    except Exception:
        return "N/A"


def _clean_event(name):
    return (name or "event") \
        .replace("_", " ") \
        .replace("a ", "") \
        .replace("an ", "") \
        .strip() \
        .title()


def answer_question(question: str, report: dict) -> str:
    """
    Rule-based Q&A engine.

    Parses the question for known intents and extracts answers
    directly from the report dict.
    """

    q = question.lower()

    # ── No report ──────────────────────────────────────────────────
    if not report:
        return (
            "I don't have a match report loaded yet. "
            "Please upload and analyze a video first."
        )

    metadata   = report.get("metadata") or {}
    events     = report.get("events") or []
    clips      = report.get("highlight_clips") or []
    spikes     = report.get("audio_spikes") or []
    commentary = report.get("commentary_events") or []
    summary    = report.get("match_summary") or {}
    sport_raw  = report.get("sport", "Unknown")
    sport      = sport_raw.replace("a ","").replace("an ","").strip().title()
    top_moment = report.get("top_moment") or {}

    highlights = [e for e in events if e.get("highlight")]

    # ── Sport ──────────────────────────────────────────────────────
    if any(w in q for w in ["what sport","which sport","sport is","sport detected"]):
        return f"The detected sport is **{sport}**."

    # ── Duration ───────────────────────────────────────────────────
    if any(w in q for w in ["how long","duration","length","time"]):
        dur = float(metadata.get("duration_seconds", 0))
        return (
            f"The video is **{_fmt_time(dur)}** long "
            f"({round(dur, 1)} seconds, "
            f"{metadata.get('frame_count', 'N/A')} frames at "
            f"{metadata.get('fps', 'N/A')} FPS)."
        )

    # ── Highlight count ────────────────────────────────────────────
    if any(w in q for w in ["how many highlight","number of highlight","total highlight"]):
        return (
            f"**{len(highlights)}** highlight-level events were detected "
            f"out of {len(events)} total events analysed."
        )

    # ── Total events ───────────────────────────────────────────────
    if any(w in q for w in ["how many event","total event","events detected","number of event"]):
        return (
            f"A total of **{len(events)}** events were detected. "
            f"{len(highlights)} were classified as highlights."
        )

    # ── Clips ──────────────────────────────────────────────────────
    if any(w in q for w in ["clip","video clip","highlight clip","generated"]):
        if not clips:
            return "No highlight clips were generated for this match."
        names = ", ".join(
            f"#{c.get('rank',i+1)} {_clean_event(c.get('event',''))}"
            for i, c in enumerate(clips[:5])
        )
        return (
            f"**{len(clips)}** highlight clip(s) were generated: {names}."
        )

    # ── Top moment ─────────────────────────────────────────────────
    if any(w in q for w in ["top moment","best moment","top highlight","best highlight","top event"]):
        if not top_moment:
            return "No top moment was identified."
        name = _clean_event(top_moment.get("event", ""))
        ts   = _fmt_time(top_moment.get("timestamp", 0))
        conf = _fmt_pct(top_moment.get("confidence", 0))
        return (
            f"The top highlight is **{name}** at **{ts}** "
            f"with {conf} confidence."
        )

    # ── Audio / Crowd ──────────────────────────────────────────────
    if any(w in q for w in ["audio","crowd","energy","spike","cheer","reaction"]):
        if not spikes:
            return "No significant crowd energy spikes were detected in this video."
        peak = max(spikes, key=lambda s: s.get("energy", 0))
        return (
            f"**{len(spikes)}** crowd energy spikes were detected. "
            f"The loudest moment was at **{_fmt_time(peak['timestamp'])}** "
            f"(energy: {round(peak.get('energy', 0), 4)})."
        )

    # ── Commentary ─────────────────────────────────────────────────
    if any(w in q for w in ["commentary","transcript","comment","whisper","spoken"]):
        if not commentary:
            return "No commentary keywords were matched in this video."
        joined = ", ".join(commentary)
        return (
            f"The commentary agent matched **{len(commentary)}** keyword(s): {joined}."
        )

    # ── Wickets ────────────────────────────────────────────────────
    if "wicket" in q:
        wk = [e for e in events if "wicket" in e.get("event","").lower()]
        if not wk:
            return "No wickets were detected in this match."
        times = ", ".join(_fmt_time(e["timestamp"]) for e in wk[:5])
        return f"**{len(wk)}** wicket(s) detected at: {times}."

    # ── Sixes ──────────────────────────────────────────────────────
    if any(w in q for w in ["six","sixes","maximum"]):
        sixes = [e for e in events if "six" in e.get("event","").lower()]
        if not sixes:
            return "No sixes were detected in this match."
        times = ", ".join(_fmt_time(e["timestamp"]) for e in sixes[:5])
        return f"**{len(sixes)}** six(es) detected at: {times}."

    # ── Goals ──────────────────────────────────────────────────────
    if "goal" in q:
        goals = [e for e in events if "goal" in e.get("event","").lower()]
        if not goals:
            return "No goals were detected in this match."
        times = ", ".join(_fmt_time(e["timestamp"]) for e in goals[:5])
        return f"**{len(goals)}** goal(s) detected at: {times}."

    # ── Dunks / Basketball ─────────────────────────────────────────
    if any(w in q for w in ["dunk","slam","three","3 pointer"]):
        dunks = [e for e in events
                 if any(k in e.get("event","").lower()
                        for k in ["dunk","slam","three","3 point"])]
        if not dunks:
            return "No dunks or three-pointers were detected."
        times = ", ".join(_fmt_time(e["timestamp"]) for e in dunks[:5])
        return f"**{len(dunks)}** basketball highlight(s) detected at: {times}."

    # ── Confidence ─────────────────────────────────────────────────
    if any(w in q for w in ["confidence","accuracy","certain","how sure"]):
        if not events:
            return "No confidence data available."
        avg = sum(float(e.get("confidence",0)) for e in events) / len(events)
        top_e = max(events, key=lambda e: float(e.get("confidence",0)))
        return (
            f"Average confidence across all events: **{round(avg*100)}%**. "
            f"Highest confidence event: **{_clean_event(top_e.get('event',''))}** "
            f"at {_fmt_time(top_e.get('timestamp',0))} "
            f"({_fmt_pct(top_e.get('confidence',0))})."
        )

    # ── Timeline / all events ──────────────────────────────────────
    if any(w in q for w in ["timeline","list","all event","show event","what happened"]):
        if not events:
            return "No events were recorded for this match."
        sorted_ev = sorted(events, key=lambda e: e.get("timestamp", 0))
        lines = [
            f"• {_fmt_time(e['timestamp'])} — {_clean_event(e.get('event',''))} "
            f"({'highlight' if e.get('highlight') else 'minor play'})"
            for e in sorted_ev[:10]
        ]
        suffix = f" (showing first 10 of {len(events)})" if len(events) > 10 else ""
        return "Event timeline" + suffix + ":\n" + "\n".join(lines)

    # ── Summary ────────────────────────────────────────────────────
    if any(w in q for w in ["summary","summar","overview","describe","tell me about"]):
        if isinstance(summary, dict):
            body = summary.get("body") or summary.get("headline") or ""
        else:
            body = str(summary)
        if body:
            return body
        return (
            f"{sport} video analysed. "
            f"{len(events)} events detected, "
            f"{len(highlights)} highlights, "
            f"{len(clips)} clip(s) generated."
        )

    # ── Resolution / FPS / quality ─────────────────────────────────
    if any(w in q for w in ["resolution","fps","quality","frame rate","pixel"]):
        return (
            f"Video quality: **{metadata.get('resolution','N/A')}** resolution, "
            f"**{metadata.get('fps','N/A')} FPS**, "
            f"{metadata.get('frame_count','N/A')} total frames."
        )

    # ── Fallback ───────────────────────────────────────────────────
    return (
        f"I analyzed this **{sport}** match ({_fmt_time(metadata.get('duration_seconds',0))}) "
        f"and found {len(events)} events with {len(highlights)} highlights. "
        f"Try asking: 'What was the top moment?', 'How many wickets?', "
        f"'List all events', or 'Describe the match'."
    )
