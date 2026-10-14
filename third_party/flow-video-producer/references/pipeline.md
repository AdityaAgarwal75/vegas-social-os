# Execution manifest

`pipeline.json` is both the plan and generation status record. All media paths are
relative to its project directory; role tasks receive resolved absolute paths.
The main agent updates generation status only after validating the returned file.

```json
{
  "version": "3.1",
  "project_name": "example",
  "status": "pending",
  "config": {
    "segment_duration": 8,
    "transition_duration": 0.5,
    "image_model": "Nano Banana Pro",
    "video_model": "Veo 3.1 Quality",
    "aspect_ratio": "16:9",
    "outputs_per_prompt": 1
  },
  "metadata": {
    "philosophy_file": "philosophy.md",
    "style_file": "style.json",
    "scene_breakdown_file": "scene-breakdown.md"
  },
  "assets": {
    "characters": {
      "hero": {
        "prompt": "Approved character prompt",
        "output": "assets/characters/hero.png",
        "status": "pending"
      }
    },
    "backgrounds": {}
  },
  "scenes": [
    {
      "id": "scene-01",
      "title": "Opening",
      "duration_target": 12,
      "transition_to_next": "dissolve",
      "first_keyframe": {
        "prompt": "Approved opening composition",
        "reference_paths": ["assets/characters/hero.png"],
        "output": "keyframes/scene-01-start.png",
        "status": "pending"
      },
      "segments": [
        {
          "id": "seg-01-A",
          "duration_target": 8,
          "motion_prompt": "Approved first action",
          "output_video": "scene-01/seg-A.mp4",
          "status": "pending"
        },
        {
          "id": "seg-01-B",
          "duration_target": 4,
          "motion_prompt": "Approved continuation",
          "output_video": "scene-01/seg-B.mp4",
          "status": "pending"
        }
      ]
    },
    {
      "id": "scene-02",
      "title": "Closing",
      "duration_target": 8,
      "transition_to_next": null,
      "first_keyframe": {
        "prompt": "Approved closing composition",
        "reference_paths": ["assets/characters/hero.png"],
        "output": "keyframes/scene-02-start.png",
        "status": "pending"
      },
      "segments": [
        {
          "id": "seg-02-A",
          "duration_target": 8,
          "motion_prompt": "Approved closing action",
          "output_video": "scene-02/seg-A.mp4",
          "status": "pending"
        }
      ]
    }
  ]
}
```

Only `completed` segments can be assembled. Retained durations must be positive,
no larger than `config.segment_duration`, and sum to each scene target. Source clips
must cover those durations. Legacy v3.0 segments without a duration are allocated
`min(segment_duration, remaining scene duration)` in order.

The last scene's transition is ignored; use null. Supported boundary types are cut,
fade (through black, no overlap), dissolve, and wipe (left-to-right reveal). For dissolve
and wipe, overlap is `min(transition_duration, outgoing duration / 2, incoming duration / 2)`.
Final duration is the sum of scene targets minus those overlaps: this example yields
19.5 seconds. Record the actual generation model and settings in config.

Project output:

```text
output/example/
  philosophy.md
  style.json
  scene-breakdown.md
  pipeline.json
  output.mp4
  assets/characters/hero.png
  keyframes/scene-01-start.png
  keyframes/scene-02-start.png
  scene-01/seg-A.mp4
  scene-01/seg-B.mp4
  scene-01/extracted/after-seg-A.png
  scene-02/seg-A.mp4
  .assembly/scene-01.mp4
  .assembly/scene-02.mp4
```

On assembly success, `status` becomes `completed` and `final_output` records actual
output metadata. Generation errors should retain an `error` message alongside the
item status. Intermediate scene files may be removed during the main skill's optional
cleanup step.
