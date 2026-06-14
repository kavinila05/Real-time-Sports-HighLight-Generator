"""
Sport Detection Agent
---------------------
Uses CLIP zero-shot classification to identify which of the
four supported sports appears in a set of sampled video frames.

Returns a clean, normalized sport name string:
  "Cricket" | "Football" | "Basketball" | "Badminton"

The CLIP prompt labels are intentionally descriptive ("a cricket
match in progress") to improve zero-shot accuracy, but the
returned value is always the clean display name so that every
downstream component — UI tiles, event labels, copilot, badge
logic — receives a consistent, human-readable string.
"""

from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
from collections import Counter


# ── Load CLIP once at module level ──────────────────────────────────
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# ── Sport label map ─────────────────────────────────────────────────
# Each entry: (clip_prompt, clean_display_name, internal_key)
SPORT_MAP = [
    ("a cricket match in progress with batsman and bowler",  "Cricket",    "cricket"),
    ("a football match with players kicking a soccer ball",  "Football",   "football"),
    ("a basketball game with players dunking or shooting",   "Basketball", "basketball"),
    ("a badminton match with players holding rackets",       "Badminton",  "badminton"),
]

CLIP_PROMPTS   = [s[0] for s in SPORT_MAP]
DISPLAY_NAMES  = [s[1] for s in SPORT_MAP]   # "Cricket", "Football" …
INTERNAL_KEYS  = [s[2] for s in SPORT_MAP]   # "cricket", "football" …


def detect_sport(frame_paths: list) -> str:
    """
    Classify the sport from a list of sampled video frame paths.

    Parameters
    ----------
    frame_paths : list[str]
        Paths to JPEG frames extracted from the video.

    Returns
    -------
    str
        Clean display name, e.g. "Cricket", "Basketball".
        Falls back to "Unknown" if no frames are provided.
    """

    if not frame_paths:
        return "Unknown"

    predictions = []

    for frame_path in frame_paths:

        try:
            image = Image.open(frame_path).convert("RGB")
        except Exception as e:
            print(f"Sport detection: could not open {frame_path}: {e}")
            continue

        inputs = processor(
            text=CLIP_PROMPTS,
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():
            outputs = model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0]
        predicted_idx = probs.argmax().item()
        predictions.append(predicted_idx)

    if not predictions:
        return "Unknown"

    # Majority vote across all frames
    majority_idx = Counter(predictions).most_common(1)[0][0]

    return DISPLAY_NAMES[majority_idx]


def get_sport_internal_key(display_name: str) -> str:
    """
    Convert a clean display name back to its lowercase internal key.

    e.g. "Basketball" -> "basketball"
    Used by pipeline stages that still do string matching.
    """
    name_lower = display_name.lower()
    for key in INTERNAL_KEYS:
        if key in name_lower:
            return key
    return name_lower
