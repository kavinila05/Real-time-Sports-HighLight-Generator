progress_tracker = {}


def update_progress(video_id, stage, progress):

    progress_tracker[video_id] = {
        "stage": stage,
        "progress": progress
    }


def get_progress(video_id):

    return progress_tracker.get(
        video_id,
        {
            "stage": "waiting",
            "progress": 0
        }
    )
