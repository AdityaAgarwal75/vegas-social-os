---
name: flow-production
description: Plan and review Google Flow scenes, references, clip continuity and frame chaining inside Vegas Social OS using the bundled licensed production skills and current account controls.
---

# Flow production through Vegas Social OS

Use this adapter with `vegas-social-master`. The pinned third-party materials are craft references; this adapter maps them to the installed Vegas tools and operator preferences. Read `../../docs/FLOW-SKILL-INTEGRATION.md` first.

1. Read `../../third_party/flow-scripting/core/flow-orchestrator.md` for the production profile and `core/flow-asset-manager.md` for subject/room/product locks. For ads read `formats/flow-ads.md`; for long scenes read `../../third_party/flow-video-producer/references/pipeline.md` and `references/segment-generator.md`.
2. Take known account, model, mode, clip length, aspect, runtime, audio and text policy from the brief. Inspect actual `flow_model_catalog`/`flow_models_refresh` choices before final timing. Current official documentation and actual controls supersede stale upstream matrices. Never default to Quality, force eight seconds or add a paid API subscription without the owner's choice.
3. Save two concepts with `plan_save` or weekly drafts with `content_plan_save`. Keep every prompt self-contained; lock identity, wardrobe, product details, room geography, screen direction and ending state. Use separate host-native scene images and actual transferred bytes. Contact sheets and Flow-generated keyframes in upstream examples do not override this project's native-image policy.
4. Use the selected model's supported Frames OR Ingredients input. Explicitly label start/end roles; Quality rejects ingredients. This adapter currently accepts at most three ingredients even when a platform might allow more. No implicit fallback to text-only or a different model/duration.
5. Submit one clip under its approved cap/stable ID through `video_request` or `flow_video_request`. Serialize all work using a shared browser. Poll the original job; a timeout is not permission to regenerate. Do not start another Chrome on imported profiles or call uninstalled gflow/Claude commands.
6. Review the downloaded clip, including movement, product/face consistency, joins, spoken delivery and sound. For continuation call `continuity_frame` on that exact imported clip and retained interval, inspect the returned PNG, then explicitly choose it as the next start frame. Frame extraction is local and does not generate another clip. A returned frame does not prove a seamless transition.
7. Respect existing creative/spending/publishing authorization rather than asking again at every upstream phase. Additional generation still needs an approved account/model/cap. Use human review before publishing. Only claim advanced Extend, Edit, upscaling, voice or project-entity controls after their own implementation and actual verification; the included references are not runtime support.

The complete producer skill snapshot includes optional MoviePy helpers for research. Vegas uses FFmpeg/ffprobe for its adapted last-frame operation and requires no new paid service. The scripting bundle is a selected documentation snapshot, not its standalone installer. Never execute third-party update/install scripts as part of ordinary production. The upstream scripting validator is not bundled; perform its continuity checks manually with the actual script, and use reel_review for labeled timing/readability heuristics. Exact one-second beats are a creative option, not a Flow requirement.
