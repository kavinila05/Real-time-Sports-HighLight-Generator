def detect_football_events(
    detections
):

    events = []

    for detection in detections:

        labels = [

            obj["label"].lower()

            for obj in
            detection["objects"]
        ]

        if (
            "sports ball" in labels
            or "person" in labels
        ):

            events.append({

                "event":
                    "football_action",

                "frame":
                    detection["frame"],

                "confidence":
                    0.72
            })

    return events
