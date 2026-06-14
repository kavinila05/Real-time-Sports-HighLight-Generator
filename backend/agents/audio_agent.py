import librosa
import numpy as np


def detect_audio_spikes(
    audio_path
):

    if audio_path is None:
        return []

    try:

        y, sr = librosa.load(
            audio_path,
            sr=16000,
            duration=30
        )

        rms = librosa.feature.rms(
            y=y
        )[0]

        threshold = (
            np.mean(rms)
            +
            1.5 * np.std(rms)
        )

        spikes = []

        for i, value in enumerate(rms):

            if value > threshold:

                timestamp = float(
                    librosa.frames_to_time(
                        i,
                        sr=sr
                    )
                )

                spikes.append({

                    "timestamp":
                        float(
                            round(
                                timestamp,
                                2
                            )
                        ),

                    "energy":
                        float(
                            round(
                                float(value),
                                3
                            )
                        )
                })

        return spikes[:20]

    except Exception as e:

        print(
            "Audio Error:",
            str(e)
        )

        return []
