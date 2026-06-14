from PIL import Image
import torch

from transformers import (
    CLIPProcessor,
    CLIPModel
)


model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
)

processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)


def analyze_frames(
    frames,
    sport
):

    detections = []

    sport = sport.lower()

    for frame_path in frames:

        image = Image.open(
            frame_path
        )

        # ==================================
        # SPORT LABELS
        # ==================================

        if "cricket" in sport:

            labels = [

                "a cricket wicket",

                "a cricket batsman hitting six",

                "a cricket boundary",

                "players celebrating",

                "normal cricket play"
            ]

        elif "football" in sport:

            labels = [

                "a football goal",

                "football players celebrating",

                "football penalty kick",

                "football goalkeeper save",

                "normal football play"
            ]

        elif "basketball" in sport:

            labels = [

                "a slam dunk",

                "a basketball 3 pointer",

                "basketball scoring",

                "players celebrating",

                "normal basketball play"
            ]

        elif "badminton" in sport:

            labels = [

                "badminton smash",

                "badminton rally",

                "badminton celebration",

                "badminton winning point",

                "normal badminton play"
            ]

        else:

            labels = [

                "sports action",

                "normal play"
            ]

        inputs = processor(

            text=labels,

            images=image,

            return_tensors="pt",

            padding=True
        )

        with torch.no_grad():

            outputs = model(
                **inputs
            )

        logits = (
            outputs
            .logits_per_image
        )

        probs = (
            logits.softmax(
                dim=1
            )[0]
        )

        best_idx = (
            probs.argmax()
            .item()
        )

        confidence = (
            probs[
                best_idx
            ].item()
        )

        detections.append({

            "frame":
                frame_path,

            "event":
                labels[
                    best_idx
                ],

            "confidence":
                round(
                    confidence,
                    2
                )
        })

    return detections
