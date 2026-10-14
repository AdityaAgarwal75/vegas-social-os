# Asset generator

Generate one approved character, background, or object reference image in Flow.
Read [browser-generation.md](browser-generation.md) for browser interaction and downloads.

Inputs: `asset_id`, `prompt`, `output_path`, and `project_dir`. Optional: `settings`
and `reference_paths` (absolute image paths). Use the main skill's image settings
when settings are omitted. Upload references if supplied. Use image mode.
Validate the downloaded image with Pillow, retaining its actual file format/extension.
Report to the main agent if the manifest extension does not match; do not merely rename
JPEG bytes to PNG. Return the image for visual review.

Return JSON: `status` (`completed` or `error`), `asset_id`, `output_path`, `message`.
