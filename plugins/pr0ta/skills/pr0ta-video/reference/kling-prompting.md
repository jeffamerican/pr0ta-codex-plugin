# Kling V3 / O3 Pro Prompting — Reference

**Start here:** this file is the deep dive on Kling prompting. For the triggering overview and the model-selection decision tree, see `pr0ta-video/SKILL.md`. Read this file when writing a Kling prompt, planning multi-shot coverage, or debugging a shot that didn't land.

---

## Kling O3 Pro Prompting Best Practices

Kling O3 Pro (via the FAL.ai endpoint) uses a specific prompting system built around **element references**. Understanding this syntax is critical for consistent, high-quality results.

### Element Reference Syntax

When you upload references, you can refer to some of them in the prompt text using special tokens:

| Token | What it references |
|-------|-------------------|
| `@Image1` | The **Start Image** -- the only image slot that gets a promptable token |
| `@Element1` | First added Element (character, prop, or location) |
| `@Element2` | Second added Element |
| `@Video1` | A reference video (if applicable) |

**Always reference your uploaded images/elements by token in the prompt.** Without this, the model may ignore them or treat them as loose context rather than binding them to specific subjects.

### CRITICAL: How Start Image and End Image Actually Work in PR0TA

Through testing, the following constraints have been confirmed in PR0TA's Kling O3 Pro implementation:

- **`@Image1` = Start Image only.** This is the only image slot that gets a promptable `@Image` token.
- **End Image is NOT promptable** -- there is no `@Image2` token. Using `@Image2` in the prompt causes the error: *"Invalid reference index 2 for image. Only 1 images provided."* The End Image acts as an **implicit structural target** that the model interpolates toward. You do NOT reference it in the prompt -- just describe the journey and the model handles the transition.
- **End Image requires Start Image** -- you cannot provide an End Image without a Start Image. Doing so causes the error: *"Tail image without first image is not supported."*
- **Start Image alone works fine** -- you can generate with just a Start Image and no End Image.

**Summary of what's promptable vs. structural:**

| Slot | Promptable? | Token | Notes |
|------|-------------|-------|-------|
| Start Image | Yes | `@Image1` | Required if End Image is used |
| End Image | No | *none* | Implicit target -- the model transitions toward it |
| Element 1 | Yes | `@Element1` | Character/prop/location bundle |
| Element 2 | Yes | `@Element2` | Additional subject bundle |

### What is an Element?

An Element is a **reference bundle** representing a single subject -- a character, prop, location, or object. Each Element consists of:

- **1 frontal/hero image** -- the primary, clearest view of the subject (typically front-facing)
- **1-3 additional reference images** -- different angles, poses, or views of the *same* subject

The frontal image is the anchor that tells the model "this is what this subject looks like." The additional references give the model more information about the subject's appearance from other angles, which dramatically improves consistency -- especially for characters that need to move, turn, or be seen from multiple perspectives.

**Best practices for Element bundles:**
- **Characters**: frontal face/body shot + profile view + 3/4 angle + back view (if available)
- **Props/Objects**: hero product shot + side angle + detail close-up
- **Locations/Sets**: establishing wide shot + key detail angles

All images in a single Element must depict the **same subject**. Don't mix different characters or objects into one Element -- create separate Elements for each distinct subject.

**Storing Elements for reuse:** Use `POST /api/v2/projects/{project_id}/elements` to create persistent Element bundles, then reference them with `element_ids[]` in generation requests. See the `pr0ta-consistency` skill for the full workflow.
### Using Element Tokens in Prompts

**Example prompts using tokens:**
- `"@Image1 slowly zooms out revealing the full scene. The central logo element rotates with a subtle glow."`
- `"@Element1 walks into frame from the left, looks toward camera, and smiles."`
- `"@Element1 and @Element2 face each other across a dimly lit table. @Element1 leans forward and speaks."`
- `"Put the character from @Element1 into the environment from @Image1. Maintain consistent lighting."`

### Prompt Structure Formula

Write prompts like **scene directions to a cinematographer**, not object inventories. Follow this master structure:

**`[Scene/Context] + [Subject & Appearance] + [Action Timeline] + [Camera Movement] + [Atmosphere/Mood] + [Technical Specs]`**

**Good prompt:**
> `"@Image1 -- cinematic logo reveal. The logo emerges from darkness as the camera slowly dollies forward. Glowing particles drift through the frame. The spiral element rotates with magenta light casting soft lens flares. Smooth, elegant motion. Shallow depth of field, professional broadcast quality."`

**Bad prompt (word salad):**
> `"logo purple glowing particles spinning cool cinematic awesome professional"`

### Action Timeline

Use sequential language to choreograph motion clearly:
- "First [Action A], then [Action B], finally [Action C]"
- "The camera begins on a close-up of X, pulls back to reveal Y, then settles on a wide shot of Z"

This is especially important for 10-second and 15-second generations where multiple beats need to land.

### Camera Language

Kling O3 responds well to professional cinematography terms:
- **Dolly in/out** -- smooth forward/backward movement
- **Truck left/right** -- lateral camera movement
- **Tracking shot** -- camera follows the subject
- **Low-angle** / **high-angle** -- perspective
- **POV** -- point-of-view
- **Macro close-up** -- extreme detail
- **Rack focus** -- shift focus between foreground/background
- **FPV** -- first-person view
- **Profile shot** -- side view

### Character Consistency with Elements

For consistent characters across multiple generations:
1. **Build proper Element bundles** -- 1 frontal/hero image + 1-3 additional angles of the same character. The more views you provide, the better the model understands the character's full appearance.
2. **Store Elements in the project** -- Use `POST /api/v2/projects/{project_id}/elements` to persist bundles, then reference via `element_ids[]` in all generations.
3. **Define key features early** in the prompt (e.g., "scar on left cheek," "red leather jacket")
4. **Never use pronouns** -- always refer to the character by label (`@Element1`, "the woman", "the soldier") every time. Pronouns cause the model to lose track of which subject is which.
5. Use the **Refs slider** at 140% (default) or higher for strong visual fidelity to references
6. **Reuse the same Element bundles** across multiple generations to maintain continuity throughout a sequence or project

### Multi-Shot Mode (Kling V3 / O3 Pro) — The Continuity Workhorse

**Kling multi-shot is the cheapest path to character and scene continuity you can buy.** A single Kling multi-shot generation produces up to 5 (V3) or 6 (O3) camera cuts inside **one visual context** — same lighting, same character identity, same environment, same color grade. Three separate 5-second generations will drift between takes; one 15-second multi-shot generation with three shots will not.

**When to reach for multi-shot:**

- You have 2–6 shots that need to land in the same scene or continuous space.
- You need character identity to stay locked across cuts (dialogue scene, chase, emotional arc).
- You want camera grammar — establishing shot → close-up → reverse, or push-in → hold → pull-back — without paying the drift tax of multiple generations.
- You're making a montage where adjacent shots should feel like one piece of coverage.

**Shot limits and duration:**

- **Kling V3 Pro:** up to **5 shots** per generation.
- **Kling O3 Pro:** up to **6 camera cuts** per generation.
- **Total duration across all shots: up to 15 seconds.** Sum of per-shot durations cannot exceed 15s.
- Individual shot durations are explicitly set per shot. A two-shot generation might be 5s + 5s or 3s + 7s — you choose.
- **Main prompt box must be empty** in the UI when multi-prompt mode is active. All narrative lives in the shot array.

**API shape (the contract):**

```json
{
  "generator": "video",
  "mode": "ref_to_vid",
  "model": "kling_o3_pro",
  "prompt_mode": "multi_prompt",
  "start_image_asset_id": "uuid-of-uploaded-image",
  "element_ids": ["element-uuid-1", "element-uuid-2"],
  "aspect_ratio": "16:9",
  "cfg": 0.5,
  "multi_prompt": [
    {
      "prompt": "Wide establishing shot. @Element1 stands at the edge of a rain-soaked rooftop at dusk, backlit by neon signs. Camera holds steady. Shallow depth of field, cinematic.",
      "duration": 3
    },
    {
      "prompt": "Medium close-up. @Element1 turns slowly toward camera, rain dripping from her hood. Camera dollies in two feet. Rack focus from the skyline to her face.",
      "duration": 4
    },
    {
      "prompt": "Tight close-up. @Element1 exhales, breath visible in the cold air. Her eyes track something off-frame left. Camera holds. Subtle shimmer of neon reflection in her iris.",
      "duration": 3
    }
  ]
}
```

**Prompting each shot — the rules that make multi-shot work:**

1. **Label every shot with its framing** in the first few words: `Wide establishing shot.`, `Medium close-up.`, `Tight POV.`, `Over-the-shoulder reverse.`, `Low-angle tracking shot.` Kling understands cinematic shot language and will frame accordingly.
2. **Anchor subjects by Element token in every shot** — `@Element1`, `@Element2`, etc. The same Element token resolves to the same subject across all shots, which is how continuity locks. **Never use pronouns between shots.** "She turns" in shot 2 will read as a new character; `@Element1 turns` will read as the same character.
3. **Describe camera motion per shot explicitly**: "Camera holds steady", "Camera dollies in", "Camera tracks left", "Camera rack-focuses from A to B". Kling honors camera language precisely.
4. **Respect cinematic conventions.** Kling applies 180-degree rule, eyeline matching, and continuity editing automatically — but only if your shot descriptions don't contradict each other. If shot 1 has `@Element1` on screen-left and shot 2 says `@Element1 on the right side of frame` with no motion description, you'll get a jump-cut artifact.
5. **Plan shot durations against action density.** Establishing shots get 3–4s. Reaction close-ups get 2–3s. Long takes get 5–7s. Sum under 15.
6. **Anchor subjects early in each shot's prompt.** The first few words should identify the subject. Don't bury `@Element1` in the middle of a sentence.
7. **One clear action per shot.** Multi-shot is not a license to cram three beats into one shot. Keep each shot to a single continuous intent.

**Element binding across shots:**

All Elements attached to the generation are shared across every shot. This is the secret to continuity: build your Element bundle once (frontal + profile + 3/4 + back for characters; hero + detail for props) via `POST /api/v2/projects/{project_id}/elements`, attach it to the multi-shot generation via `element_ids[]`, and reference `@Element1` in every shot prompt. The model now has a strong anchor for the subject across all 2–6 shots.

See `pr0ta-consistency` for the full Element bundle workflow.

**Start Image in multi-shot mode:**

`@Image1` (Start Image) still works in multi-shot mode — it anchors the **visual context** of shot 1 (lighting, color grade, composition). Subsequent shots inherit the visual style from shot 1's anchor. **End Image is NOT supported in multi-shot mode** — it's single-scene only. If you need to land on a specific final frame, use a single-shot generation with Start + End Image instead.

**Multi-shot vs three separate generations — the honest comparison:**

| Technique | Continuity | Control | Cost | When to use |
|-----------|-----------|---------|------|-------------|
| Kling multi-shot (1 gen, 3 shots) | **High** — same visual context, locked characters | Good — per-shot prompt + duration | 1 generation | Shots in same scene or continuous action |
| 3 separate Kling generations | Lower — visible drift in lighting, grade, character | Higher — full control per clip | 3 generations | Shots in different locations, different characters, different styles |
| Seedance Omni + `character_id` | High — character identity locked by ID | Good for single continuous shot | 1 generation per shot | Character needs to appear across many non-contiguous shots |

**Test pair recipe for continuity-critical work:**

1. Storyboard the sequence as 3–6 shots.
2. Generate the full sequence as **one Kling O3 multi-shot generation** (6 cuts).
3. Generate the same sequence as **one Seedance Omni `character_id` generation** (if it fits in one call) or as parallel shots with shared character ID.
4. Compare. Pick the better take. Sometimes it's Kling; sometimes it's Seedance. Budget the second generation — it's worth it.

**Multi-shot in the browser UI:**

Toggle **Multi-Prompt** mode on the Ref-to-Vid tab. The main Prompt box will grey out. Add shots via the Multi-Prompt section; each shot gets its own prompt text area and duration field. Sum of durations is capped at 15s. Elements and Start Image are attached once to the generation and shared across all shots.

**Full cinematic example — three-shot dialogue moment:**

```json
{
  "prompt_mode": "multi_prompt",
  "multi_prompt": [
    {
      "prompt": "Over-the-shoulder shot from behind @Element2. @Element1 sits across a candlelit table, her face lit warm from below. She looks up from a letter in her hands. Camera holds. Shallow focus on @Element1, @Element2's shoulder soft in foreground.",
      "duration": 4
    },
    {
      "prompt": "Reverse over-the-shoulder from behind @Element1. @Element2's face now in focus, expression guarded. Candlelight flickers across his features. Camera dollies in two inches. Eyeline matches @Element1's gaze from the previous shot.",
      "duration": 4
    },
    {
      "prompt": "Two-shot medium. Both @Element1 and @Element2 visible across the table. @Element1 sets the letter down between them. Camera holds steady. The candle between them flickers. Silence before the next beat.",
      "duration": 3
    }
  ]
}
```

This is eleven seconds of continuous dialogue coverage in a single generation, with locked character identity, matched eyelines, consistent lighting, and deliberate camera grammar. That is what Kling multi-shot is for.

### Kling V3 Single-Prompt Multi-Prompt (Legacy Simple Form)

For simple two-segment shots, the minimum multi-prompt payload is:

```json
{
  "prompt_mode": "multi_prompt",
  "multi_prompt": [
    { "prompt": "@Element1 steps into the room. Camera follows." },
    { "prompt": "@Element1 turns to face the window. Camera holds." }
  ]
}
```

Each segment inherits the default per-shot duration if `duration` is omitted. Use the full schema with explicit durations for serious work.

### Negative Prompts

Use the **Negative Prompt** field to combat unwanted defaults:
- Common negatives: `"blurry, distorted, low quality, cartoonish, disfigured, watermark, text overlay, jittery motion"`
- For logo animations: `"morphing, melting, face generation, human figures"`

### Common Workflow: "Resolve Into" Animations (Logo Reveals, Transitions)

When the user wants a video that **ends on** a specific image (e.g., a logo reveal, a character emerging from abstract forms):

1. **Generate the starting frame** -- Use Nano Banana 2 (Image Generator, Txt to Img) to create an abstract or symbolic starting image that thematically connects to the target. Match the aspect ratio (e.g., 1:1).
2. **Set up Ref to Vid** -- Put the generated abstract image as **Start Image** and the target (logo, character, etc.) as **End Image**.
3. **Write the prompt using `@Image1` only** -- Describe the journey FROM the start image. Do NOT reference the End Image with any token. Just describe the transformation: `"@Image1 -- swirling cosmic energy tightens and crystallizes into sharp geometric letterforms. The spiral locks into an emblem shape..."` The model will handle the visual transition to the End Image automatically.

**Example prompt for a logo reveal:**
> `"@Image1 -- a swirling cosmic spiral of violet and magenta plasma energy on a dark void. Camera holds steady. The spiral tightens and accelerates, pulling inward toward center frame. Light intensifies at the core. The chaotic energy crystallizes and snaps into sharp geometric letterforms -- a sleek modern logo emerges. Letters materialize with a metallic shimmer, settling into final position with a pulse of light. Deep navy background, shallow depth of field, soft bokeh particles drift and settle. Professional broadcast logo sting."`

### Key Tips

- **Think in shots, not clips** -- describe a single continuous camera move per generation
- **Anchor subjects early** -- mention the main subject in the first few words
- **Simpler is better** -- one clear action per 5-second segment beats cramming in complexity
- **Iterate** -- generate 2-3 variations with slightly different prompts to find the best take
- **Duration matters** -- 5s for tight, punchy animations; 10s for narrative beats; 15s for fuller sequences. All major models (Kling O3/V3, Seedance) support up to 15s.
- **Prefer longer clips** -- A single 15s generation is more visually consistent than three 5s clips. Use multi-prompt mode for complex sequences rather than generating many short clips.
- **End Image is implicit** -- never try to reference it with `@Image2`. Just describe the transition and the model handles the landing.
