# Troubleshooting

## Browser generation

- **Missing tools:** configure the current host's browser automation. Claude Code's
  MCP installation command is host-specific; no Google API key is used here.
- **Login or account access:** let the user sign in to Flow. Inspect access in the UI.
- **Unavailable model or rejected generation:** report the displayed service error.
- **Wrong mode:** inspect the mode selector and uploaded previews before submission.
- **Stale element reference:** obtain a fresh snapshot before interacting again.
- **Stuck generation:** poll the existing job, return its reference after the bounded
  wait, and check it again before retrying to avoid duplicate generations.
- **Wrong/missing download:** track the submitted gallery item and the tool-reported
  download path. Do not assume a fixed download folder.
- **Concurrent UI interference:** serialize work sharing a tab/session. Parallel tasks
  need isolated sessions or projects.

## Visual quality

- **Character or style drift:** use the same approved reference images, subject details,
  and style passage in prompts. Inspect all scene keyframes together before video.
- **Poor motion:** focus on one main action with a clear trajectory, speed, weight,
  and camera movement. Match it to the supplied starting frame.
- **Rotation distortion:** reduce the turn per segment or supply approved references
  showing needed angles. Frame chaining cannot guarantee identity from unseen angles.
- **Jarring joins:** check that extraction uses the retained duration, not discarded
  footage. Review motion direction/velocity and choose a deliberate scene transition.
- **Wrong audio:** inspect generated audio and revise audio cues or use an authorized
  separate soundtrack. Local assembly preserves audio unless --no-audio is selected.

## Local processing

- **MoviePy missing:** install `scripts/requirements.txt` from the skill folder. Helpers
  use MoviePy 2.x; MoviePy 1.x is not supported.
- **Unreadable media:** inspect file size and completion, re-download the correct item,
  and validate it opens before updating generation status.
- **Source shorter than target:** regenerate or revise the approved plan. Assembly
  returns an error rather than silently stretching or freezing footage.
- **Wrong final runtime:** retained segment durations must sum to scene targets.
  Dissolve/wipe subtract their overlaps; cut/fade preserve the scene total. Output is
  quantized to frames, so allow roughly one frame of measurement tolerance.
- **Manifest out of sync:** re-read pipeline.json and verify artifact paths and generation
  statuses. Assembly requires completed segments; it does not mark failed sources done.
- **Different resolutions:** default assembly resizes to the first input. Use --no-resize
  with compose to center clips on a canvas, or choose matching source dimensions.
- **Output path collision:** choose a destination distinct from source videos and assembly
  intermediates. The helpers reject overwriting an active video source.

Keep generated sources after failures so individual tasks can be retried without
repeating successful generation.
