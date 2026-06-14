def detect_badminton_events(
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
                    "badminton_action",

                "frame":
                    detection["frame"],

                "confidence":
                    0.68
            })

    return events
