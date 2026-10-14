# Keyframe generator

Generate one scene's starting keyframe in Flow image mode.
Read [browser-generation.md](browser-generation.md) for browser interaction and downloads.

Inputs: `scene_id`, `prompt`, `output_path`, `project_dir`, and `style_context`.
Optional: `settings` and `reference_paths` (absolute paths of approved
character/background/style images). Use the main skill's image settings when omitted.
Upload the relevant references and reinforce the approved visual style in the prompt.
Ensure the initial pose and framing allow the first segment's planned action. Validate
image readability and format, and return it for review; visual approval belongs to the
main agent/user. This keyframe starts a new scene, not every segment.

Return JSON: `status` (`completed` or `error`), `scene_id`, `output_path`, `message`.
