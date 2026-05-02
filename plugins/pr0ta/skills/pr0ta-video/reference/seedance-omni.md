## Seedance 2.0 Omni (ByteDance Lynx)

Seedance 2.0 Omni is a quad-modal video generation model supporting text + up to 9 images + 3 videos + 3 audio as inputs (12 reference files total). It appears in the model list as "ByteDance Lynx (Image-to-Video)" at 63.00 credits/second.

**API model string:** `muapi/seedance-2.0-omni-reference`

### Key Capabilities

- **Quad-modal input:** Combine text prompts with image, video, and audio references in a single generation
- **Character ID workflow:** Create persistent character identities from frontal image + character sheet + optionally 1-2 additional images
- **Native multi-shot:** Generate multiple continuous shots with character consistency maintained
- **Motion/rhythm matching:** Use video references for camera trajectory and audio references for rhythm-synced motion
- **Duration:** integer; no strict enum published in PR0TA's local schema for Omni. Treat as provider-defined and use the longest practical clip for consistency. Note this differs from Seedance **T2V/I2V**, which are discrete `5|10|15`.
- **Aspect ratios:** `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` per bundled provider spec. The unified `/generate` layer passes values through and does not enforce a whitelist itself — stick to the published list to avoid provider-side rejection.
- **Resolution:** 480p or 720p (default 720p)

### Seedance Reference Token System

Seedance uses `@` tokens to bind uploaded references to specific roles in the prompt. **Always use explicit @ references — don't rely on the model to auto-interpret which asset is which.**

| Token | References | Max Count |
|-------|-----------|-----------|
| `@image1` – `@image9` | Uploaded images (character, scene, style, composition) | 9 |
| `@video1` – `@video3` | Uploaded video clips (camera motion, pacing, choreography) | 3 |
| `@audio1` – `@audio3` | Uploaded audio files (rhythm, voiceover, music) | 3 |
| `@character:<id>` | Pre-registered MuAPI character identity | 1 per request |

**What the model extracts from each reference type:**
- **Images:** Character identity, composition structure, lighting setup, color palette, pose, environment details
- **Videos:** Camera motion paths, movement speed, pacing, choreography, scene transition style
- **Audio:** Rhythm/beat patterns, tonal mood, voice characteristics, timing and synchronization cues

**Landscape reference images work for portrait output.** You can use a landscape reference image and request `9:16` output — Seedance handles the reframing. Center important content in the reference image to avoid cropping surprises.

### Seedance Prompting Best Practices

Seedance prompting is more reference-driven than Kling. The model excels when you give it explicit references and describe how they relate.

**Core prompt structure:**
```
Subject (@image/character ref) + Scene/Atmosphere + Action/Performance + Camera Movement + Style/Lighting
```

**Example prompts:**

Simple character animation:
```
@image1 walks slowly through a rain-soaked Tokyo street at night. Neon signs reflect in puddles.
Camera follows from behind at medium distance. Cinematic, shallow depth of field, warm sodium lighting.
```

Multi-reference production shot:
```
@image1 as the character performing a slow dance in @image2 environment.
Match @video1 camera movement speed and pacing. Sync character motion to @audio1 beat pattern.
Cinematic color grading with blue-purple neon tones, film grain.
```

Director-style with role assignment:
```
Use @image1 for character identity, @image2 for scene composition.
Character enters frame from the left, pauses, looks directly at camera.
Tracking shot from left to right, 3 meters. Shallow depth of field.
Inspired by Wong Kar-wai cinematography.
```

**Timeline prompting (advanced):** For longer durations, break the video into timed segments:
```
[00:00-00:04] @image1 character enters frame walking, tracking camera follows
[00:04-00:08] Character stops, close-up on face with dramatic side lighting
[00:08-00:12] Slow zoom out to reveal @image2 environment in background
```

**Key prompting rules for Seedance:**

1. **Explicitly assign every reference** — "Use @image1 for the character and @image2 for the environment" is much better than just uploading two images
2. **Don't jam conflicting instructions** — Reference @video1 for camera/pacing OR describe camera movement in text, not both in conflicting ways
3. **Longer, more detailed prompts yield better results** — Seedance rewards specificity more than Kling does
4. **Use cinematic language** — "tracking shot", "dolly in", "crane up", "slow zoom", "rack focus" all work well
5. **Include physics/style anchors** — "inspired by Terrence Malick cinematography", "shot in 24fps with film grain", "match Dune (2021) color grading"
6. **Never use pronouns** — always reference the character by @token or name. "She walks" is ambiguous; "@image1 walks" is precise.
7. **Audio-synced motion** — when using @audio1, describe how motion should relate to the rhythm: "sync steps to @audio1 beat", "character movement follows @audio1 rhythm"

### Character ID Workflow

A Seedance character is constructed from:
- **1 frontal image** — clear, front-facing, the identity anchor
- **1 character sheet** — multi-panel reference (front, back, side, poses, expressions) at 4K 21:9 resolution
- **Optionally 1-2 additional images** — supplementary angles or detail shots

Generate the character sheet with Nano Banana 2 first (see `pr0ta-consistency` for the prompt template and best practices), then **train an Omni token** through one of the two MuAPI training paths before registering it.

**Two training paths — pick by reference material:**

- **Single clean portrait →** `muapi/seedance-2-omni-reference-train` (needs `image_url` + `character_name`)
- **Character sheet or 1-3 approved stills →** `muapi/seedance-2-character` (needs `images_list[]` + `character_name` + `outfit_description`)

Both run through the unified `/generate` endpoint, are async, and return the Omni token in `result_refs.character_id` on completion. Full payloads, decision framework, and persistence flow: see `pr0ta-consistency` → "Creating a Seedance Character Token — Two Paths".

**Persist the trained token to the project character store:**
```json
POST /api/v2/projects/{project_id}/characters
{
  "name": "Sarah",
  "provider": "muapi",
  "provider_resource_id": "omni-sarah-token"
}
```
`provider_resource_id` is the token returned from training in `result_refs.character_id`.

**Use in generation:**
```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "sound": "off",
  "prompt": "@image1 — Sarah walks through a bustling Tokyo market at golden hour. Camera tracks slowly from behind. Warm lighting, shallow depth of field, cinematic color grading.",
  "character_ids": ["project-character-uuid-sarah"],
  "duration": 10
}
```

**Current limitation:** The unified generation route currently resolves exactly one stored character per request.

### Multi-Modal References

Pass image, video, and audio references using the `references` array:

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 as the character, moving with @video1 camera style, rhythm synced to @audio1.",
  "references": [
    { "type": "image", "image_url": "https://example.com/hero.png" },
    { "type": "image", "image_url": "https://example.com/environment.png" },
    { "type": "video", "video_url": "https://example.com/camera-motion.mov" },
    { "type": "audio", "audio_url": "https://example.com/music-track.wav" }
  ],
  "reference_image_urls": ["https://example.com/hero.png", "https://example.com/environment.png"],
  "reference_video_urls": ["https://example.com/camera-motion.mov"],
  "reference_audio_urls": ["https://example.com/music-track.wav"],
  "character_ids": ["project-character-uuid"],
  "duration": 12,
  "aspect_ratio": "16:9",
  "sound": "off"
}
```

**Reference strategy by production type:**

| Production Type | Image Refs | Video Refs | Audio Refs | Notes |
|----------------|-----------|-----------|-----------|-------|
| **Dialogue with visible speaker** | Character frontal + character sheet | — | Pre-recorded dialogue (Gemini Flash TTS) | **Best workflow for lip sync.** Generate TTS first, feed as @audio1. Phoneme-level lip sync in 8+ languages. |
| **Character-driven narrative** | Character frontal + character sheet | — | — | Use stored character_id for identity lock. Narrate in post. |
| **Music video / rhythm piece** | Character + style reference | Dance/motion reference | Music track | Sync motion to @audio1 beat pattern |
| **Cinematic B-roll** | Location/mood reference | Camera motion reference | — | Focus on environment and camera work |
| **Product/commercial** | Product shots (multiple angles) | Smooth motion reference | Brand music | Center product in all refs |
| **Documentary reenactment** | Character + period location | — | Narration audio | Use narration rhythm for pacing |

### Audio-Driven Video Generation (Dialogue-to-Video / Lip Sync)

Seedance 2.0 Omni can generate video driven by audio input — this is one of its most powerful capabilities. When you pass audio as `@audio1`, the model performs:

- **Phoneme-level lip sync** — character mouth movements are synchronized to the exact speech in the audio, supporting 8+ languages (English, Chinese, Japanese, Korean, Spanish, French, German, Portuguese)
- **Rhythm-matched motion** — body movement, camera cuts, and visual pacing sync to the audio's beat pattern and tempo

**Dialogue-to-Video workflow (pre-recorded speech → talking character video):**

1. Generate the character's dialogue audio first using Gemini Flash TTS (see `pr0ta-audio`) — this gives you precise language and voice control. Use ElevenLabs v3 only for specific ElevenLabs voices or legacy tag workflows.
2. Upload the dialogue audio as `@audio1` and the character reference as `@image1`
3. Prompt Seedance to animate the character speaking the dialogue:

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "@image1 as the character, speaking the dialogue from @audio1. Medium close-up, soft office lighting, subtle head movements while speaking.",
  "references": [
    { "type": "image", "image_url": "https://example.com/character.png" },
    { "type": "audio", "audio_url": "https://example.com/dialogue.mp3" }
  ],
  "reference_image_urls": ["https://example.com/character.png"],
  "reference_audio_urls": ["https://example.com/dialogue.mp3"],
  "character_ids": ["project-character-uuid"],
  "duration": 8,
  "aspect_ratio": "16:9",
  "sound": "on"
}
```

**This is the recommended workflow for non-English dialogue.** Generate the speech in ElevenLabs (which handles any language reliably), then feed that audio to Seedance for lip-synced video. This gives you the best of both worlds: precise language/voice control from ElevenLabs + automatic lip sync from Seedance.

**Music-driven video (beat-synced visuals):**

Pass a music track as `@audio1` with visual references. The model syncs cuts, motion, and rhythm to the music:

```
@image1 as the dancer, performing choreography synced to @audio1 beat pattern.
Dynamic camera movement matching the tempo. Neon nightclub environment from @image2.
```

**Audio-driven best practices:**
- Audio format: MP3, max 15MB, duration ≤15 seconds
- Optimal dialogue length: 3-8 seconds for best lip sync accuracy. Longer clips may drift.
- Match `duration` parameter to the audio length — if audio is 8 seconds, set `duration: 8`
- Keep speech pace natural — unnaturally fast dialogue degrades sync quality
- For longer dialogue, split into multiple clips at sentence boundaries
- Include camera/expression cues in the prompt alongside the audio reference — the model needs both

### When to Choose Seedance vs Kling

**The single most important lesson from field production: Seedance Omni follows explicit numeric/textual instructions in prompts far more reliably than Kling O3 Pro.** Treat these models as complementary, not interchangeable — they have fundamentally different strengths.

### Task-Type Decision Table (READ THIS FIRST)

Select the model by **what the shot needs to do**, not just by modality:

| If the shot needs… | Prefer | Why |
|---|---|---|
| Literal text/number/UI state transitions (countdown timers, score tickers, on-screen value changes) | **Seedance 2.0 Omni** | Seedance honors enumerated frame values; Kling will hallucinate intermediate frames |
| A stock ticker going 09→08→07 or a display changing exact values | **Seedance 2.0 Omni** | Field-tested: Kling O3 Pro produced `08 → 00 → 09` garbled sequence; Seedance executed cleanly first try |
| Character continuity across many shots | **Seedance + Characters** | Character sheet references are more stable shot-to-shot than Kling Elements |
| Rhythm-synced or audio-driven motion | **Seedance 2.0 Omni** | Only Seedance accepts audio references |
| Multi-prompt scene progression within a single clip | **Seedance 2.0 Omni** | Native multi-prompt handles beat timing more predictably |
| Cinematic atmospheric continuation of a still image (wind, smoke, clouds, camera drift, mood) | **Kling O3 Pro** | Kling excels at "vibe" extrapolation from a single frame |
| Structured camera-control API parameters (specific pan/tilt/dolly values) | **Kling V3** | Only Kling V3 exposes `camera_control` as a typed API field |
| Motion Brush (selective region animation) | **Kling** | Seedance has no equivalent |
| Tight budget on long clips | **Kling** | Kling at 14.70 credits/s vs Seedance at 63.00 credits/s |

**Rule of thumb:** If the shot has a deterministic on-screen state (specific number, specific text, specific UI), **use Seedance**. If the shot is an atmospheric/cinematic continuation, Kling O3 Pro is often better. When in doubt, default to Seedance.

### Capability Matrix

| Criterion | Seedance 2.0 Omni | Kling O3/V3 |
|-----------|-------------------|-------------|
| **Instruction-following fidelity** | **Strong** (enumerate values, it honors them) | Variable (hallucinates intermediate states) |
| **Character system** | Frontal + character sheet + optional extras | Multi-angle Element bundles (1 frontal + 1-3 angles) |
| **Reference capacity** | 12 files (9 img, 3 vid, 3 audio) | Images + text only |
| **Motion control** | Video reference for camera trajectory | Structured camera_control API parameter + Motion Brush |
| **Audio sync** | Native audio references — rhythm-synced motion | No audio input (audio generated separately) |
| **Multi-shot** | Native multi-shot with character consistency | Multi-prompt mode (V3: 5 shots, O3: 6 cuts) |
| **Prompting style** | Reference-heavy with explicit @token assignment | Scene-direction with @Element/@Image tokens |

**Default to Seedance.** You can use both in the same production — Seedance for any shot with deterministic on-screen state, falling back to Kling O3 Pro for cinematic atmospheric shots or Kling V3 for structured camera control.

### Kling V3 Pro vs O3 Pro — Reference Field Differences

**Status (April 2026):** The earlier Kling V3 Pro `start_image_asset_id` failure is **resolved**. PR0TA's unified layer now translates `start_image_asset_id` → provider-native `start_image_url` end-to-end for `fal-ai/kling-video/v3/pro/image-to-video`, with regression test coverage. Agents may use `start_image_asset_id` on Kling V3 Pro directly. If you see a V3 Pro failure today, the asset-id translation is **not** the likely cause — investigate the prompt, the reference asset itself, or a different runtime issue.

Kling variants still have different **provider-native** primary image fields at the provider layer, but PR0TA's unified layer now translates correctly for both. The material difference is which unified field is clearest for agents to use:

**Kling V3 Pro image-to-video:**
```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "fal-ai/kling-video/v3/pro/image-to-video",
  "prompt": "...self-contained scene description...",
  "start_image_asset_id": "a73b9aad-...",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```
Optional `end_image_asset_id` for first-frame-last-frame composition.

**Kling O3 Pro image-to-video:**
```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "fal-ai/kling-video/o3/pro/image-to-video",
  "prompt": "...self-contained scene description...",
  "image_asset_id": "a73b9aad-..."
}
```
On O3 Pro, `image_asset_id` is the clearest unified field (the provider-native required field is `image_url`, and PR0TA promotes `image_asset_id` into it). `start_image_asset_id` also works — the unified mapper duplicates a normalized start image into `image_url` — but `image_asset_id` is more self-documenting for O3 Pro.

**Kling O3 Pro reference-to-video** (richer reference composition with multiple image refs):
```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "fal-ai/kling-video/o3/pro/reference-to-video",
  "prompt": "...self-contained scene description...",
  "start_image_asset_id": "a73b9aad-...",
  "reference_image_asset_ids": ["b82c40de-...", "c93d5e0f-..."]
}
```
Use this endpoint — **not** Kling O3 Pro I2V — when you need richer reference composition (multiple reference images, elements, first-and-last frames together).

**Seedance 2.0 Omni is the strongest choice for reference-heavy shots** because it has the broadest multimodal reference surface (images + video + audio + character refs) and the cleanest end-to-end translation. For shots that need structured camera control or Kling-specific features, use Kling instead — they are co-equal defaults (see `pr0ta-video` → "Model Selection").

**Seedance 2.0 Omni (reference-to-video):**
```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "seedance_2_omni",
  "reference_asset_ids": ["a73b9aad-..."],
  "prompt": "...self-contained scene description enumerating every state change...",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```

**Rule:** If you need a specific starting frame, default to Seedance unless you have a reason to reach for Kling O3 Pro.

---

### Seamless Video Extension (Text with Reference Chaining)

Seedance 2.0 Omni's most powerful long-form technique: **seamless video extension** via iterative "Text with Reference" chaining. Instead of generating discrete shots and cutting between them, you extend a single continuous sequence segment by segment. The model uses the last frame of the previous clip as the first frame of the next, producing a seamless continuation with consistent characters, environment, and audio.

**This is the preferred workflow when you need:**
- Long continuous sequences (30s+) that exceed single-generation duration limits
- Character, environment, and audio consistency maintained automatically over extended durations
- The ability to inject new characters, actions, or environment changes into a continuous shot mid-sequence
- Seamless background audio, music, and ambient sound continuity without manual sound design

#### Core Workflow

**Step 1 — Generate or obtain a base clip.** Start with any initial video — generated from Seedance, Kling, or any other model. This becomes your first segment.

**Step 2 — Set up the extension.** Use **Text with Reference** mode (`mode: "txt_to_vid"` with a video reference via `@video1`), **not** Image to Video. The video reference tells Seedance to continue from the last frame of the existing clip.

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "Extend this video by 5 seconds. @video1 continues — the character turns to face the camera, revealing a surprised expression. The neon signs behind them flicker. Camera slowly dollies in.",
  "references": [
    { "type": "video", "video_url": "https://..." }
  ],
  "reference_video_urls": ["https://..."],
  "duration": 5,
  "aspect_ratio": "16:9",
  "sound": "on"
}
```

**Step 3 — Chain extensions iteratively.** Once the first extension renders, use its output as the new `@video1` reference for the next segment. Repeat to build sequences of any length.

**Step 4 — Fortify with static references.** Upload character reference images alongside the video reference to prevent visual drift:

```json
{
  "generator": "video",
  "mode": "txt_to_vid",
  "model": "muapi/seedance-2.0-omni-reference",
  "prompt": "Extend this video by 5 seconds. @video1 continues — @image1 character walks toward the doorway. A new figure (@image2) appears from the right side of frame, carrying a briefcase. Camera pans to follow.",
  "references": [
    { "type": "video", "video_url": "https://..." },
    { "type": "image", "image_url": "https://hero-ref.png" },
    { "type": "image", "image_url": "https://new-character-ref.png" }
  ],
  "reference_video_urls": ["https://..."],
  "reference_image_urls": ["https://hero-ref.png", "https://new-character-ref.png"],
  "duration": 5,
  "aspect_ratio": "16:9",
  "sound": "on"
}
```

#### Consistency Techniques

**Visual fortification (critical for long chains):**
- Always upload static character reference images alongside the video reference — don't rely on the video alone to maintain character appearance
- Upload screenshots of character clothing from previous clips if wardrobe drift appears — the model will match the clothing reference
- For new characters introduced mid-sequence, provide their reference images with explicit `@imageN` assignment in the prompt

**Audio continuity (automatic):**
- Background audio, sound effects, voice characteristics, and music carry over automatically between extensions when using `sound: "on"`
- The model understands it is continuing a sequence and intrinsically maintains audio consistency
- This eliminates manual sound design for ambient beds and background music across chained clips

**Environment consistency:**
- The video reference anchors the environment — the model continues the same setting from the last frame
- To shift environments, describe the transition explicitly in the prompt (e.g., "the character walks through the doorway into a dimly lit corridor")

#### Post-Production Assembly

After generating all extension segments, assemble them on the post-production timeline:

1. **Add clips sequentially** — place each segment in order on the timeline via `POST /timeline/clips`
2. **Trim overlap frames** — Seedance may output a duplicate frame at the junction (last frame of clip N = first frame of clip N+1). Trim 1 frame from the tail of the first clip or head of the second to eliminate the stutter. On the PR0TA timeline, use a ripple trim: `POST /timeline/edits/{clip_id}/trim` with `mode: "ripple"`, `edge: "tail"`, `delta: -0.033` (one frame at 30fps)
3. **Fix slow-motion segments** — Seedance occasionally renders a segment in slow motion. If pacing doesn't match the rest of the sequence, apply a speed adjustment (e.g., 2x–3x) to that specific clip in post. On the PR0TA timeline, adjust the clip's effective duration
4. **Link A/V pairs** — if your extensions have separate audio handling, link the video and audio clips together (see editorial primitives → clip link groups)

#### When to Use Extension vs Multi-Shot

| Scenario | Use Extension Chaining | Use Multi-Shot / Discrete Cuts |
|----------|----------------------|-------------------------------|
| Long continuous sequence (same camera, same scene) | ✓ | |
| Story with hard cuts between different angles/scenes | | ✓ |
| Maximum audio continuity without editing | ✓ | |
| Injecting new characters into an existing shot | ✓ | |
| Parallel-generation for speed | | ✓ (each shot independent) |
| Budget-sensitive (minimize total seconds generated) | | ✓ (no overlap frames) |

**Cost note:** Extension chaining generates some redundant content (the model re-renders the transition area), so the total generated seconds will be slightly higher than the final output. This overhead is minor compared to the consistency benefit.

#### Prompting Tips for Extensions

- **Always say "Extend this video"** or "Continue this video" in the prompt — this primes the model for continuation rather than reinterpretation
- **Describe only what changes** — don't re-describe the existing scene in full; focus on the new action, new character, or new camera movement
- **One new major element per extension** — introducing too many changes at once can break continuity. Add one new character, one environment shift, or one major action per segment
- **Match duration to action** — request only enough duration to cover the new action (3–5 seconds per segment is a good default). Overly long extensions risk drift
