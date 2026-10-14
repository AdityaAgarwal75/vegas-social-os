#!/usr/bin/env python3
"""Extract the last retained video frame for segment chaining."""
import argparse
import json
import math
import sys
from pathlib import Path


def extract_frame(input_file, output_file, duration=None):
    from moviepy import VideoFileClip
    with VideoFileClip(str(input_file), audio=False) as clip:
        end = clip.duration if duration is None else float(duration)
        if not math.isfinite(end) or end <= 0 or end > clip.duration + 1e-6:
            raise ValueError('Duration must be positive and no longer than the source')
        # Last frame strictly before the retained interval ends, including fractional targets.
        frame_index = max(0, math.ceil(end * clip.fps - 1e-6) - 1)
        output = Path(output_file)
        if output.resolve() == Path(input_file).resolve():
            raise ValueError('Frame output must not overwrite source video')
        output.parent.mkdir(parents=True, exist_ok=True)
        clip.save_frame(str(output), t=frame_index / clip.fps)
        return {'status': 'success', 'output_path': str(output), 'time': frame_index / clip.fps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('--duration', type=float, help='Retained segment duration before assembly')
    args = parser.parse_args()
    try:
        result = extract_frame(args.input, args.output, args.duration)
    except Exception as exc:
        result = {'status': 'error', 'message': str(exc)}
    print(json.dumps(result))
    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
