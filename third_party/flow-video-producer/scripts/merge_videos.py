#!/usr/bin/env python3
"""Merge clips or assemble a pipeline, preserving audio and applying scene transitions."""
import argparse
import json
import math
import sys
from pathlib import Path


def positive(value, label):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{label} must be a finite positive number')
    return value


def join_clips(clips, transitions, transition_duration=0.5, method='compose'):
    import numpy as np
    from moviepy import CompositeVideoClip, VideoClip, afx, concatenate_videoclips, vfx

    if len(transitions) != len(clips) - 1:
        raise ValueError('Provide exactly one transition per clip boundary')
    transition_duration = positive(transition_duration, 'Transition duration')
    edited = list(clips)
    starts = [0.0]
    for i, transition in enumerate(transitions):
        if transition not in ('cut', 'fade', 'dissolve', 'wipe'):
            raise ValueError(f'Unsupported transition: {transition}')
        overlap = 0.0
        if transition != 'cut':
            # Half-length bound prevents adjacent transitions from overlapping each other.
            d = min(transition_duration, clips[i].duration / 2, clips[i + 1].duration / 2)
            if transition == 'fade':
                edited[i] = edited[i].with_effects([vfx.FadeOut(d)])
                edited[i + 1] = edited[i + 1].with_effects([vfx.FadeIn(d)])
            elif transition == 'dissolve':
                edited[i + 1] = edited[i + 1].with_effects([vfx.CrossFadeIn(d)])
                overlap = d
            else:
                w, h = clips[i + 1].size
                def wipe_mask(t, width=w, height=h, duration=d):
                    return np.broadcast_to(
                        (np.arange(width) < width * min(1.0, t / duration)).astype(float),
                        (height, width),
                    ).copy()
                mask = VideoClip(wipe_mask, is_mask=True, duration=clips[i + 1].duration)
                if edited[i + 1].mask is not None:
                    mask = mask.with_effects([vfx.MasksAnd(edited[i + 1].mask)])
                edited[i + 1] = edited[i + 1].with_mask(mask)
                overlap = d
            if edited[i].audio is not None:
                edited[i] = edited[i].with_audio(edited[i].audio.with_effects([afx.AudioFadeOut(d)]))
            if edited[i + 1].audio is not None:
                edited[i + 1] = edited[i + 1].with_audio(edited[i + 1].audio.with_effects([afx.AudioFadeIn(d)]))
        starts.append(starts[-1] + clips[i].duration - overlap)
    if all(t in ('cut', 'fade') for t in transitions):
        return concatenate_videoclips(edited, method=method)
    size = (max(c.w for c in clips), max(c.h for c in clips))
    layers = [c.with_start(start).with_position('center') for c, start in zip(edited, starts)]
    return CompositeVideoClip(layers, size=size).with_duration(starts[-1] + clips[-1].duration)


def merge_videos(input_files, output_file, method='compose', codec='libx264',
                 fps=None, resize=True, audio=True, durations=None,
                 transitions=None, transition_duration=0.5):
    sources = []
    final = None
    try:
        from moviepy import VideoFileClip
        if not input_files:
            raise ValueError('Need at least one input video')
        if method not in ('compose', 'chain'):
            raise ValueError('Method must be compose or chain')
        output = Path(output_file).resolve()
        if any(Path(f).resolve() == output for f in input_files):
            raise ValueError('Output must not overwrite an input video')
        if fps is not None:
            fps = positive(fps, 'FPS')
        if durations is not None and len(durations) != len(input_files):
            raise ValueError('Provide one duration per input video')
        clips = []
        for i, filename in enumerate(input_files):
            source = VideoFileClip(str(filename))
            sources.append(source)
            clip = source
            if durations is not None and durations[i] is not None:
                duration = positive(durations[i], 'Clip duration')
                if duration > source.duration + 1e-6:
                    raise ValueError(f'{filename}: requested {duration}s exceeds source {source.duration}s')
                clip = clip.subclipped(0, duration)
            if resize and i and clip.size != clips[0].size:
                clip = clip.resized(clips[0].size)
            clips.append(clip)
        if method == 'chain' and any(c.size != clips[0].size for c in clips):
            raise ValueError('chain requires matching resolutions; use compose or enable resize')
        final = join_clips(clips, transitions if transitions is not None else ['cut'] * (len(clips) - 1),
                           transition_duration, method)
        output.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(str(output), codec=codec, fps=fps or clips[0].fps,
                              audio=audio, audio_codec='aac', logger=None)
        with VideoFileClip(str(output), audio=False) as encoded:
            return {'status': 'success', 'output_path': str(output), 'duration': encoded.duration,
                    'resolution': f'{encoded.w}x{encoded.h}', 'fps': encoded.fps,
                    'input_count': len(clips)}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}
    finally:
        if final is not None:
            final.close()
        for source in sources:
            source.close()


def assemble_pipeline(pipeline_file, output_file=None, **options):
    """Resolve project paths relative to pipeline.json; update completion only after success."""
    path = Path(pipeline_file).resolve()
    data = json.loads(path.read_text())
    root = path.parent
    scenes = data['scenes']
    if not scenes:
        raise ValueError('Pipeline must contain at least one scene')
    max_duration = positive(data.get('config', {}).get('segment_duration', 8), 'Segment duration')
    plans = []
    for scene in scenes:
        remaining = positive(scene['duration_target'], 'Scene duration')
        files, durations = [], []
        for segment in scene['segments']:
            if segment['status'] != 'completed':
                raise ValueError(f"Segment {segment['id']} is not completed")
            duration = positive(segment.get('duration_target', min(max_duration, remaining)), 'Segment duration')
            if duration > max_duration or duration > remaining + 1e-6:
                raise ValueError(f"Invalid duration for {segment['id']}")
            files.append(root / segment['output_video'])
            durations.append(duration)
            remaining -= duration
        if abs(remaining) > 1e-6:
            raise ValueError(f"Segment durations do not sum to target for {scene['id']}")
        plans.append((files, durations))
    transitions = [s.get('transition_to_next') or 'cut' for s in scenes[:-1]]
    if any(t not in ('cut', 'fade', 'dissolve', 'wipe') for t in transitions):
        raise ValueError('Unsupported scene transition')
    scene_files = []
    all_inputs = [f.resolve() for files, _ in plans for f in files]
    for index, scene in enumerate(scenes):
        # Use scene order for filenames; scene IDs never become filesystem paths.
        scene_file = root / '.assembly' / f'scene-{index + 1:02d}.mp4'
        if scene_file.resolve() in all_inputs:
            raise ValueError('Intermediate scene output would overwrite a segment')
        scene_files.append(scene_file)
    destination = Path(output_file).resolve() if output_file else root / 'output.mp4'
    if destination.resolve() in all_inputs + [f.resolve() for f in scene_files] + [path]:
        raise ValueError('Final output would overwrite a source or manifest')
    for (files, durations), scene_file in zip(plans, scene_files):
        result = merge_videos(files, scene_file, durations=durations, **options)
        if result['status'] != 'success':
            return result
    result = merge_videos(scene_files, destination, transitions=transitions,
                          transition_duration=data.get('config', {}).get('transition_duration', 0.5), **options)
    if result['status'] == 'success':
        data['status'] = 'completed'
        data['final_output'] = result
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(data, indent=2) + '\n')
        temporary.replace(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='*')
    parser.add_argument('-i', '--input-files', nargs='+', default=[])
    parser.add_argument('-o', '--output')
    parser.add_argument('--pipeline', help='Assemble scenes from pipeline.json')
    parser.add_argument('--method', choices=['compose', 'chain'], default='compose')
    parser.add_argument('--codec', default='libx264')
    parser.add_argument('--fps', type=float)
    parser.add_argument('--no-resize', action='store_true')
    parser.add_argument('--no-audio', action='store_true')
    parser.add_argument('--durations', nargs='+', type=float, help='Trim each input to this duration')
    parser.add_argument('--transitions', nargs='+', choices=['cut', 'fade', 'dissolve', 'wipe'])
    parser.add_argument('--transition-duration', type=float, default=0.5)
    args = parser.parse_args()
    options = dict(method=args.method, codec=args.codec, fps=args.fps,
                   resize=not args.no_resize, audio=not args.no_audio)
    if args.pipeline and (args.inputs or args.input_files or args.durations or args.transitions
                          or args.transition_duration != 0.5):
        parser.error('Pipeline mode takes durations and transitions from pipeline.json')
    if not args.pipeline and (not args.output or not (args.inputs or args.input_files)):
        parser.error('Provide --pipeline, or --output and at least one input')
    try:
        if args.pipeline:
            result = assemble_pipeline(args.pipeline, args.output, **options)
        else:
            result = merge_videos(args.inputs + args.input_files, args.output,
                                  durations=args.durations, transitions=args.transitions,
                                  transition_duration=args.transition_duration, **options)
    except Exception as exc:
        result = {'status': 'error', 'message': str(exc)}
    print(json.dumps(result))
    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
