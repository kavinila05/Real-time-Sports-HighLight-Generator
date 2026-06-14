def detect_basketball_events(
    detections
):

    events = []

    for detection in detections:

        labels = [

            obj["label"].lower()

            for obj in
            detection["objects"]
        ]

        confidence_scores = [

            obj["confidence"]

            for obj in
            detection["objects"]
        ]

        person_count = (
            labels.count(
                "person"
            )
        )

        has_ball = (
            "sports ball"
            in labels
        )

        avg_confidence = (

            sum(
                confidence_scores
            )

            /

            len(
                confidence_scores
            )

            if confidence_scores
            else 0
        )

        # stricter logic
        # multiple players
        # ball visible
        # decent confidence

        if (

            person_count >= 2

            and has_ball

            and avg_confidence >= 0.6
        ):

            events.append({

                "event":
                    "basketball_action",

                "frame":
                    detection[
                        "frame"
                    ],

                "confidence":
                    round(
                        avg_confidence,
                        2
                    )
            })

    return events
