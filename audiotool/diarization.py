from pyannote.audio import Pipeline
from audiotool.segment import Segment


def diarization(input_file):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=True)
    diarization = pipeline(input_file)

    result = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        result.append(Segment(turn.start, turn.end, speaker=speaker))
    return result


if __name__ == "__main__":
    segments = diarization("input/audio.wav")
    for segment in segments:
        print(segment)
