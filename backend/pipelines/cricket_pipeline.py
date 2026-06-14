def detect_cricket_events(
    detections
):

    events = []

    for detection in detections:

        labels = [

            obj["label"].lower()

            for obj in
            detection["objects"]
        ]

        if "person" in labels:

            events.append({

                "event":
                    "possible_cricket_play",

                "frame":
                    detection["frame"],

                "confidence":
                    0.70
            })

    return events
