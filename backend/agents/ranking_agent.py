def rank_highlights(
    events
):

    scored_events = []

    for event in events:

        score = (
            event[
                "confidence"
            ]
        )

        if event.get(
            "audio_match"
        ):

            score += 0.1

        scored_events.append({

            **event,

            "score":
                round(
                    score,
                    2
                )
        })

    ranked = sorted(

        scored_events,

        key=lambda x:
        x["score"],

        reverse=True
    )

    for idx, event in enumerate(
        ranked
    ):

        event["rank"] = (
            idx + 1
        )

        if idx == 0:

            event[
                "importance"
            ] = (
                "top_highlight"
            )

        else:

            event[
                "importance"
            ] = (
                "secondary"
            )

    return ranked
