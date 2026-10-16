# Complete video recipes

The replacement gallery contains 35 original versioned recipes and 65 separate shot prompts. Cards are text-first and have no misleading repeated thumbnails. The old IDs resolve only for compatibility; existing selections remain immutable history.

1. Call `template_catalog(query, category)`, inspect the full `video_prompt`, `reference_requirements`, `shots`, pitfalls and source URLs. These are authored model-agnostic recipes informed by licensed/public craft, not exported proprietary Higgsfield presets. Effects are generation intentions, not guaranteed controls.
2. Reuse the video's project and saved selections. `template_compile(template_id, subject, settings, continuity)` returns `shots`, all `scenes`, per-shot image/video prompts and the first `scene` for legacy clients. Never send a whole multi-shot format as one render.
3. Settings accept aspect_ratio, duration_seconds, optional approved dialogue and legacy lens/lighting/motion choices. Verify the actual model's duration and reference support separately. A camera word is descriptive guidance, not a native optical parameter. For exact edits, pass `settings.video_prompts`, one nonblank prompt per shot.
4. `template_select` saves the exact compiled prompts and locks without any provider call. Include all scenes in the two-concept production workflow. Review real reference/keyframe images; preserve subject identity, product count and geometry, garment pattern, room and light.
5. Create native ChatGPT keyframes, review them, then use approved Flow job settings and credit ceilings. Template selection is never generation, image, publishing or spending approval. Save revised selections as new immutable versions.

Read pinned craft on demand with `skill_reference`: `higgsfield-generate` → `references/prompt-engineering.md`, `instagram/ig-reel` → `SKILL.md`, `instagram/ig-plan` → `SKILL.md`, `instagram/ig-audit` → `SKILL.md`, `marketing/content-strategy` → `SKILL.md`. Call the exact listed document paths, never guess filesystem paths. Licensed text is guidance; do not run bundled upstream scripts.

`higgsfield_status` checks installation/configuration without authentication. Optional `higgsfield_discover` performs read-only catalog discovery under an isolated private CLI home. It cannot render or spend. Flow remains default. Source presets, account eligibility, live quotes and thumbnail redistribution rights are separate contracts; do not promise access to private preset prompts.
