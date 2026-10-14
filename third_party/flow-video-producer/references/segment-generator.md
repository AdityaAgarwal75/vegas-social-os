# Segment generator

Generate one video segment from its supplied starting frame in Flow.
Read [browser-generation.md](browser-generation.md) for browser interaction and downloads.

Inputs: `segment_id`, `scene_id`, `motion_prompt`, `start_frame_path`, `output_video_path`,
`project_dir`, `extract_end_frame`, and `end_frame_path`. Optional: `settings`,
`duration_target`, and absolute `skill_dir`. Use the main skill's video settings and
8-second segment duration when omitted. Resolve `skill_dir` from this reference's
parent skill folder. The motion prompt is the browser prompt.

1. Verify the starting frame exists and is readable. Upload it in video-from-frames mode
   and generate one video with the approved settings. Do not independently create a new
   starting image or use text-only mode as a fallback.
2. Download and validate the video with MoviePy. Its duration must cover `duration_target`;
   otherwise return an error. Keep the original source, including its audio.
3. If another segment follows (`extract_end_frame` is true), run:

   ```bash
   python <skill_dir>/scripts/extract_frame.py <output_video_path> -o <end_frame_path> --duration <duration_target>
   ```

   This extracts the last frame of the interval retained in assembly, not the end of
   discarded footage. Validate the resulting image. If extraction fails, return an error
   with the downloaded video path; do not claim that the segment chain is ready.
4. Return JSON: `status` (`completed` or `error`), `segment_id`, `scene_id`,
   `output_video_path`, `end_frame_path` (null if not extracted), actual source duration,
   retained duration, and `message`. The main agent passes this frame to the next task.
