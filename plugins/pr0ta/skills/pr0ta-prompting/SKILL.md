---
name: pr0ta-prompting
description: "PR0TA prompting guide — self-contained prompts, prompt bible, six named field-tested techniques, model-specific guidance for GPT Image 2/Kling/Seedance/Nano Banana, and anti-patterns. Read BEFORE writing any visual generation prompt — image or video. Essential for avoiding failures like negation in prose (video models silently drop 'don't'/'no'), vague composition, assumed context between shots, and camera confusion. Also covers the Line-Locked Poster pattern for title cards, the prompt-the-BEFORE-moment rule for i2v key frames, and the prompt bible pattern for multi-shot consistency."
---

# Prompting Guide for PR0TA Productions

This reference covers the art and science of writing effective generation prompts for PR0TA's **visual** AI models (Kling, Seedance, Nano Banana). The core principle: **every prompt must be completely self-contained** -- no assumed context, no pronouns referencing other shots, no "same as before."

> **For TTS and dialogue prompting** (ElevenLabs v3 audio tags, emotion control, pacing, character voices), see `pr0ta-audio` → "Audio Tags & Emotion Control."

## Why Prompting Matters for Consistency

Each PR0TA generation (image or video) is an isolated API call. The model has zero knowledge of your other shots, your cue sheet, or your story. If Shot 3's prompt says "the same probe enters the cave," the model doesn't know what "the same probe" looks like or what "the cave" refers to. It will invent something new.

Self-contained prompts + stored reference images (Elements/Characters) are how you control consistency. The prompt handles description and direction; the references handle visual identity. Both are required. Neither alone is sufficient.

## The Self-Contained Prompt Rule

Every prompt you write for a generation must pass this test: **Could someone with zero context about your project read this prompt and understand exactly what should appear on screen?**

**Bad (assumes context from other shots):**
> "The same probe enters the nebula. It glows like before."

**Good (fully self-contained):**
> "@Element1 -- a sleek silver cylindrical space probe with blue LED running lights along its fuselage and a rotating antenna array at its nose -- drifts into a dense violet-and-magenta nebula. The probe's LED lights cast faint blue reflections on nearby gas clouds. Camera tracks the probe from a 3/4 rear angle as it penetrates deeper into the swirling gas. Slow, deliberate motion. Deep space ambience, volumetric lighting through gas clouds, 4K cinematic."

The second prompt names everything, describes everything, and assumes nothing.

**Field-tested:** When using `start_image_asset_id` + a prompt, the prompt must re-describe the scene **as if the model has never seen the reference image**. Prompts like *"the same person, now smiling"* produce noticeably worse continuations than *"a man in his 40s wearing a charcoal suit, cool studio lighting, shallow depth of field, now beginning to smile."* This is not optional — it has been confirmed across multiple productions.

## Named Techniques (Field-Tested)

Two specific phrases and one pattern have been repeatedly confirmed to shift model behavior on Kling and Seedance. Memorize them.

### Technique 1: Enumerate Every Frame Value

**For countdowns, timers, tickers, score displays, or any shot where exact on-screen values must change over time, name every state with an explicit timestamp.**

**Bad (ambiguous — model will hallucinate intermediate frames):**
> "Digital timer counts down from 9 to 1 over 2.5 seconds."

**Good (one line per state — Seedance will honor this):**
> "A digital seven-segment timer on a black background. At 0.0s display `00:00:09`. At 0.3s display `00:00:08`. At 0.6s display `00:00:07`. At 0.9s display `00:00:06`. At 1.2s display `00:00:05`. At 1.5s display `00:00:04`. At 1.8s display `00:00:03`. At 2.1s display `00:00:02`. At 2.4s display `00:00:01`. Numerals are amber-gold, massive, centered, no other elements on screen."

Field case: Kling O3 Pro produced `08 → 00 → 09` on an identical-reference countdown because the prompt said "count down from 9". Seedance 2.0 Omni executed the enumerated version cleanly first try. **Always prefer Seedance for enumerated-state shots** (see `pr0ta-video` decision table).

Applies to: countdown timers, score tickers, stock tickers, UI state transitions, date changes, progress bars, dice rolls, any on-screen text/number that must move through specific values.

### Technique 2: Hold the Existing Composition

**For shots where you want minimal motion — a text pulse, slight push-in, eyes blinking, a flag rippling — explicitly instruct the model to lock the composition.**

The magic phrase, append verbatim near the end of the prompt:

> *"Hold the existing composition. Minimal camera movement. Only [specific element] animates."*

**Example:**

> "A man in his 40s in a charcoal suit sits at a cherry-wood desk, warm tungsten key light from camera-right, cool blue fill from the window. Shallow depth of field, 85mm. **Hold the existing composition. Minimal camera movement. Only his eyes blink once and his mouth slightly parts as if about to speak.**"

Dramatically reduces unwanted scene rewrites, camera drifts, and hallucinated motion on Kling reference-to-video. Particularly valuable for title cards, talking-head B-roll, and "breathing still" shots where the rest of the frame must remain stable.

### Technique 3: Line-Locked Poster Prompt (Text-Heavy Stills)

**Use this pattern any time a still needs exact on-screen words — title cards, flash cards, quote posters, lower-thirds baked into images.** It routes around the safety/softening pass that rewrites "provocative" phrases into blander substitutes and fixes the "almost right but one word wrong" failure mode.

**The pattern:** one `EXACTLY` instruction, one line per line of text, with `Line N (style): EXACT TEXT` formatting. No prose paraphrase of the copy anywhere else in the prompt.

**Template:**

```
The poster text must read EXACTLY the following, with no other words on the image:
Line 1 ([style]): [EXACT TEXT LINE 1]
Line 2 ([style]): [EXACT TEXT LINE 2]
Line 3 ([style]): [EXACT TEXT LINE 3]
...
[Environment / background / composition description here, with NO additional text on the image.]
```

**Worked example (field-tested, Nano Banana 2, 9:16 title card):**

```
The poster text must read EXACTLY the following, with no other words on the image:
Line 1 (small white caps): MODERN MONETARY THEORY
Line 2 (HUGE bold amber-gold): THE GOVERNMENT
Line 3 (HUGE bold amber-gold): CAN'T RUN OUT
Line 4 (HUGE bold amber-gold): OF MONEY.

Flat vector poster on a deep navy background. Extreme saturation.
Massive sans-serif display type occupying 60-70% of the frame,
centered, tight letter-spacing. No other elements, no icons, no
decorative marks. 9:16 vertical composition.
```

**Why this works, and why prose fails.** Field-observed failure modes on the same copy in prose form:

- `"The government can't run out of money"` → rendered as `"CAN'T RUN OUT OF FUNDS"` (softening)
- `"Modern Monetary Theory"` → rendered as `"CONTEMPORARY ECONOMIC THEORY"` (euphemism)

Both look like model hallucination, but the root cause is an upstream softening pass that rewrites copy it considers provocative. The `EXACTLY` + line-numbered format bypasses that pass because the text is structured as a quoted specification rather than a prose paraphrase.

**Rules when using this pattern:**

1. **Never describe the copy in prose elsewhere in the prompt.** If you say "a poster about public finance that reads..." the model may re-paraphrase from the prose description instead of the quoted lines.
2. **Include `with no other words on the image`** — this suppresses hallucinated sub-headlines, URLs, and "lorem ipsum"-style filler text.
3. **Verify pixel-perfect before moving on.** If any character is wrong, regenerate the still. Do not paint over it and do not feed it through a video model to "fix" it (video models will rewrite text — see `pr0ta-consistency` and `pr0ta-video`).
4. **Animate on the timeline.** Once the still is correct, add it to the post-production timeline with a Ken Burns preset rather than `ref_to_vid` (see `pr0ta-timeline` → "Ken Burns as a Clip Property").

Text-reliable models for this pattern: **Nano Banana 2, GPT Image 1.5, Ideogram, Kling V3/O3 (for image output modes)**. If one model softens the copy on the first try, fan out to 3-5 models in parallel (see `pr0ta-image` → "Fan-Out and Pick" recipe) and pick the winner.

### Technique 4: Frame Motion and State Positively, Never Negatively

**Video models silently drop negations embedded in prose prompts.** `"Don't destroy the carving"`, `"the gate does not close"`, `"no cutting motion"` — the model reads past the `don't` / `no` / `does not` and renders the thing you forbade. This is not a Kling quirk or a Seedance quirk; it is how current video models process prompts.

**The rule:** describe the desired *end state* and the *motion toward it* in positive terms only. If you catch yourself writing a negation, rewrite it as a positive assertion.

**Bad (negation — model renders the forbidden action):**
> "The craftsman polishes the carving. Don't destroy the carving. No cutting motions."

**Good (positive assertion of the preserved state):**
> "The craftsman runs a soft cloth in slow circular polishing motions over the already-completed carving. The carving's surface remains fully intact throughout; the finished form is preserved from start to end."

**Translation table for common cases:**

| Negation (avoid) | Positive rewrite (use) |
|---|---|
| "don't break the glass" | "the glass remains whole and upright throughout" |
| "the door does not close" | "the door stays open at the same angle throughout" |
| "no cutting / chipping / damaging" | "performs [finishing action] on the already-completed surface" |
| "not facing the camera" | "back of head toward camera; fronts facing the horizon line" |
| "doesn't change clothes" | "wearing the same [described garment] throughout the shot" |
| "no extra fingers" | "exactly one thumb and four fingers per hand, five digits total" (use alongside a negative prompt; positive framing is the stronger signal) |

**Field-tested** across Seedance 2.0 Omni and Kling V3/O3. The positive form works on the first try in cases where every negation variant failed repeatedly.

### Technique 5: Self-Contained Prompts on Every Reference Shot

The most common failure mode in multi-shot productions. Restating the Self-Contained Prompt Rule above as a named technique: **every prompt with a reference image must fully re-describe subject, environment, lighting, and camera** as if the reference didn't exist.

### Technique 6: Prompt the BEFORE Moment for Image-to-Video

**When generating a key frame (still image) that will be animated via image-to-video, prompt the state BEFORE the action, not the action itself.**

The natural tendency is to prompt the storyboard moment — the peak of the action. This works for storyboards but fails for i2v. The reason: the video model will start from whatever the image shows and then animate forward. If the image already shows the peak action, the video either shows the action floating (already mid-event) or awkwardly continues past the interesting moment.

**Bad — prompts the action itself:**
> "A glass of milk falling to the ground, shattering, milk splashing everywhere"
→ Result: a glass frozen mid-air, then hitting the ground. Looks wrong.

**Good — prompts the BEFORE state:**
> "A full glass of milk sitting on the edge of a wooden kitchen table, morning light, slightly precarious position"
→ Then the video prompt says: "The glass gets bumped and falls off the table, shattering on the tile floor, milk splashing outward."

**Another example — a candle going out:**
- Bad key frame: "A candle sputtering, smoke wisps, dim light" → video starts with it already dying
- Good key frame: "A tall beeswax candle burning brightly, steady warm flame, wax dripping down the side" → video shows it flickering, sputtering, and going dark

**The principle:** shots that express a transformation or arc (A→B→C) require the key frame to show state A. Prompt the beginning, then let the video prompt describe the journey to B and C. This is counterintuitive — your instinct is to visualize the dramatic moment, but for i2v you need the setup, not the payoff.

## Prompt Structure Formula

Write prompts like scene directions to a cinematographer. Follow this master structure:

**`[Scene/Environment] + [Subject & Appearance] + [Action/Motion] + [Camera Movement] + [Lighting & Atmosphere] + [Technical Style]`**

### 1. Scene/Environment (Ground the Space)

Always start with the environment. This gives the model spatial and lighting context before introducing motion. Without spatial anchoring, subjects float in ambiguous space -- a telltale AI artifact.

- Name the location specifically: "a glass-walled corner office on the 40th floor" not "an office"
- Include ground plane references: floors, surfaces, terrain
- Specify time of day and weather if relevant
- Use architectural terms: "Art Deco lobby," "Brutalist concrete corridor," "Victorian conservatory"

### 2. Subject & Appearance (Anchor Identity)

Every time a character, prop, or object appears, describe it fully. Use proper nouns as stability anchors.

**Characters:**
- Name them: "Sarah" not "the woman" or "she"
- List defining features: "Sarah, a tall woman with olive skin, shoulder-length black hair with a natural wave, wearing a fitted navy blazer over a cream linen shirt"
- Include distinctive marks: "slight scar above left eyebrow," "gold wedding ring on left hand"
- Never use pronouns when referring to characters -- always use their name or label (`@Element1`)

**Props:**
- Be specific about materials and colors: "a matte black leather briefcase with brass latches" not "a briefcase"
- Name recurring props consistently -- use the exact same words every time

**Locations:**
- Name them: "The Garden Study" not just "the room"
- Lock architectural elements: "mahogany bookshelves, Persian rug with geometric pattern, tall east-facing windows"

### 3. Action/Motion (Choreograph Clearly)

Describe what happens in sequential, unambiguous terms.

- Use timeline language: "First [A], then [B], finally [C]"
- One clear action per 5-second segment
- Describe physics when relevant: "the tires smoke as the car drifts 90 degrees" not "car turns"
- For character motion, specify body mechanics: "Sarah pivots on her heel and strides toward the door" not "she turns and walks away"

### 4. Camera Movement (Direct the Lens)

Specify camera behavior precisely. Both Kling and Seedance respond well to professional cinematography terms.

**Reliable camera terms:**
- **Dolly in/out** -- smooth forward/backward on rails
- **Truck left/right** -- lateral camera movement
- **Tracking shot** -- camera follows the subject
- **Orbit** -- camera circles subject
- **Pan** / **Whip pan** -- horizontal rotation
- **Tilt up/down** -- vertical rotation
- **Rack focus** -- shift focus between foreground/background
- **Low-angle / high-angle** -- perspective
- **POV / FPV** -- point-of-view
- **Static wide shot** -- camera doesn't move
- **Slow push-in** -- subtle forward creep

**Match camera to shot type:**
- Establishing shot: static wide or slow pan to reveal
- Dialogue: medium shot, minimal movement
- Action: tracking or handheld
- Emotional beat: slow push-in to close-up
- Transition: dolly or crane

**Avoid:** Vague camera language like "move camera around" or "cinematic camera." Say exactly how the camera behaves over time.

### 5. Lighting & Atmosphere (Paint with Light)

Use specific light source descriptions, not abstract mood words.

**Instead of abstract mood words, describe the actual light:**

| Abstract (avoid) | Specific (use) |
|-------------------|----------------|
| "dramatic lighting" | "single overhead fluorescent tube casting hard shadows" |
| "moody atmosphere" | "fog at ground level, harsh overhead light cutting through" |
| "warm feeling" | "golden hour sunlight through office windows, long warm shadows" |
| "dark and mysterious" | "single blue LED panel from below, deep shadows on upper face" |

**Time-of-day lighting:**
- Golden hour: warm directional light, long shadows, orange tones
- Blue hour: cool twilight, soft and diffuse
- Harsh midday: contrasty, bright, short shadows
- Overcast: soft and even, no harsh shadows

**Pro tip:** AI excels at backlighting, low-key scenes, and hazy atmospheric light. These often look more convincing than perfectly lit scenes.

### 6. Technical Style (Lock the Look)

End every prompt with consistent style anchors. Use the same style sentence across all prompts in a project:

> "Cinematic lighting, 35mm film grain, shallow depth of field, slightly desaturated with cool blue shadows, high production value."

This creates visual continuity even when scenes change. Pin these details in your prompt bible and copy them verbatim.

**Effective style anchors include:**
- Lens reference: "85mm portrait lens," "wide-angle 24mm"
- Film stock: "Kodak Portra 400 aesthetic," "Fuji Velvia saturation"
- Color grade: "teal and orange color grade," "desaturated noir palette"
- Texture: "subtle film grain," "clean digital," "anamorphic lens flares"

## The Prompt Bible

For any multi-shot production, create a **prompt bible** before writing any prompts. This is your single source of truth for all visual descriptions.

### What Goes in the Prompt Bible

**Characters:**
```
SARAH (Protagonist):
  Physical: tall, athletic build, olive skin, dark brown eyes, shoulder-length black
  hair with natural wave
  Wardrobe: fitted navy blazer, cream linen shirt, tailored grey trousers, brown
  leather belt
  Distinctive: slight scar above left eyebrow, gold wedding ring, minimal jewelry
  Element ID: element-uuid-sarah
  Style anchor: "Sarah, a tall athletic woman with olive skin and shoulder-length
  black hair, wearing a navy blazer over cream linen, gold wedding ring visible"
```

**Locations:**
```
THE GARDEN STUDY:
  Architecture: Victorian study with 12-foot ceilings, crown molding, east-facing
  bay windows
  Furnishings: mahogany desk, leather wingback chair, Persian rug (geometric
  pattern, deep red and navy), floor-to-ceiling bookshelves
  Lighting default: morning light through east windows, warm dappled shadows through
  glass panes
  Palette: warm earth tones (ochre, taupe, deep green, leather brown)
  Style anchor: "a Victorian study with crown molding and east-facing bay windows,
  morning light casting dappled shadows across a mahogany desk and Persian rug"
```

**Props:**
```
THE ARTIFACT:
  Description: ancient bronze compass, palm-sized, with jade-green patina and
  inscribed symbols on the outer ring
  Style anchor: "an ancient palm-sized bronze compass with jade-green patina and
  inscribed symbols"
```

**Global style:**
```
VISUAL STYLE:
  "Cinematic, 35mm Kodak Portra film aesthetic, shallow depth of field, slightly
  warm color grade with cool blue shadows, professional broadcast quality."
```

### Using the Prompt Bible

When writing each shot's prompt, copy the relevant anchors verbatim from the bible. Don't paraphrase. Don't abbreviate. The exact same words every time create the strongest consistency signal.

## Model-Specific Prompting

### Kling O3 Pro / V3

Kling's reasoning architecture understands cinematic intent -- it interprets prompts like film directions rather than keyword lists.

**Optimal prompt length:** 80-150 words. Below 80 often lacks sufficient detail. Above 200, the model starts averaging conflicting instructions.

**Element token usage:**
- `@Image1` = Start Image (the only promptable image token)
- `@Element1`, `@Element2` = uploaded Element bundles
- `@Video1` = reference video (if applicable)
- Never use `@Image2` -- End Image is an implicit target, not promptable
- Reference every element by token in the prompt -- without this, the model may ignore references

**Multi-prompt (Kling V3: 5 shots, O3: 6 cuts):**
- Each segment: one clear action + one camera move
- Reference Elements by token in every segment -- don't assume carry-over
- Segments share Elements and references, so consistency is maintained within one generation

**Camera control:**
- Kling V3 supports structured `camera_control` parameter in addition to prompt text
- Kling O3 responds strongly to professional camera terms in the prompt

**Negative prompts (Kling):**
Keep to 4-8 targeted terms. Focus on actual failure modes you're seeing:
- Stability: "no facial warping, no morphing faces, no flickering textures, no objects drifting"
- Motion: "no camera drift, no jittery camera, no sudden zooms"
- Quality: "blurry, distorted, low quality, watermark, text overlay"
- Physics: "no extra fingers, no floating objects, no distorted proportions"

**Common Kling failure modes:**
- Subjects floating in space -> always include a ground plane reference
- Temporal flickering -> avoid highly textured starting images, use negative prompts for flickering
- Character drift between shots -> use stored Elements with Refs slider at 140%+

### Seedance 2.0 Omni

Seedance is quad-modal -- it synthesizes text, image, video, and audio references simultaneously. Its power comes from the `@tag` reference system.

**Reference syntax:**
- `@Image1`, `@Image2`, etc. = uploaded image references
- `@Video1` = video reference for motion/camera work
- `@Audio1` = audio reference for rhythm/pacing
- `@character:<id>` = persistent character identity

**Optimal prompt length:** 50-100 words produces more controlled results than shorter prompts.

**Key differences from Kling:**
- Place the subject block first -- Seedance weights early tokens heavier
- Add "same person across frames" as an explicit stability anchor
- Describe physics when specifying motion: "tires smoke as car drifts" not just "car turns"
- Seedance understands audio-visual synchronization natively

**Character consistency in Seedance:**
- Even with a reference image, reiterate key traits in text: "short silver hair," "mole under left eye"
- For multi-shot content, use the same character description verbatim in every prompt
- One strong reference is better than five weak ones
- Clear face, good lighting, minimal distortion in reference images is critical

**Multi-modal reference strategy:**
- `@Image1` for character appearance
- `@Video1` for camera movement and pacing
- `@Audio1` for rhythm and beat timing
- Text prompt for narrative action and environment
- Specify each reference's purpose: "Using @Image1 for character, @Video1 for camera movement"

**Audio references:**
- MP3 format only -- other formats will fail lip-sync
- Use audio for beat-driven motion, voiceover pacing, or ambient rhythm
- Seedance ensures natural lip-sync when audio is provided

### Nano Banana 2

Nano Banana 2's reasoning architecture handles complex, detailed prompts better than traditional diffusion models. It plans scenes before rendering, calculating how light interacts with surfaces.

**Prompt structure:**
1. Core subject (most important -- model weights early tokens)
2. Environment/setting
3. Lighting details (use photographic language: "85mm portrait lens," "shallow depth of field")
4. Style/artistic direction
5. Constraints/exclusions

**Thinking Level parameter:**
- Low/minimal: simple images, saves 20-30% generation time
- High/dynamic: complex compositions, precise text, detailed character sheets, intricate spatial relationships

**For character reference sheets:**
- Request specific views: "front-facing portrait, full body, arms at sides, clean white background"
- Generate separate images for each angle (front, profile, 3/4, back)
- Maintain identical character descriptions across all angle prompts
- Include: "professional character reference sheet, even studio lighting, no background elements"

**Negative prompts (Nano Banana 2):**
Keep modular and targeted:
- Baseline: "low quality, blurry, jpeg artifacts, oversaturated, watermark, logo, text"
- Anatomy: "extra fingers, extra limbs, deformed hands, asymmetrical face, bad anatomy"
- Composition: "cropped, out of frame, cut off, cluttered background"

**Text in images:**
- Wrap text in double quotes: `"Happy Birthday" in bold white sans-serif`
- Keep under 25 characters per text element
- ALL CAPS generates more reliably than mixed case
- Use high Thinking Level for text-heavy images

**Tolerance parameter:** Controls content safety filtering (1-6, default 4). Adjust upward if legitimate creative prompts are being blocked.

### OpenAI GPT Image 2 (Escalation Model)

GPT Image 2 (`openai/gpt-image-2`) is the escalation model — use it when Nano Banana 2 (the default) can't meet prompt adherence requirements, or for character consistency image edits where identity preservation matters. Its prompting behavior differs from Nano Banana 2:

- **No `width`/`height` — use `image_size`, `quality`, `num_images`, `output_format`.** Check `GET /api/crew/model_defaults?model_id=openai/gpt-image-2` for the authoritative parameter list.
- **Strong instruction following.** GPT Image 2 follows detailed prose prompts well without needing the structured prompt hierarchy that Nano Banana 2 benefits from. Write naturally.
- **Far superior character consistency** in image editing (`openai/gpt-image-2/edit`) — use it for `img_to_img` and `ref_to_img` operations where preserving identity across edits is critical.
- **Text rendering** is generally strong, but the Line-Locked Poster pattern (Technique 3 above) and post-gen glyph QC remain the safe practice for any shot with critical on-screen text.
- **Fan-out still applies.** For hard shots (exact text, complex composition), include GPT Image 2 in your fan-out model list alongside Nano Banana 2 and others — see `pr0ta-image` → "Fan-Out and Pick."

## Prompt Anti-Patterns (What Breaks Consistency)

The three most critical anti-patterns: **(1) Pronouns and assumed context** -- never use "she/it/the same"; name everything. **(2) Negations in prose** -- video models drop `don't`/`no`/`does not` and render the forbidden action; rewrite as positive assertions (see Technique 4). **(3) Shifting descriptors** -- use the exact same words from the prompt bible every time, never abbreviate.

For the full list of 11 anti-patterns with bad/good examples, see `reference/anti-patterns.md`.

## Shot-Type Prompt Templates

All templates follow the structure formula (Scene -> Subject -> Action -> Camera -> Lighting -> Style). End every template with `[GLOBAL STYLE ANCHOR]`.

- **Establishing:** `[Wide/Aerial] of [LOCATION + architecture]. [Time of day] light. [Atmosphere]. [Camera: static wide / slow pan / drone descent]. No characters visible.`
- **Medium (Dialogue):** `[Medium shot] of [CHARACTER NAME, full appearance] in [LOCATION]. [Action with body mechanics]. [Lighting matching location]. Camera: [subtle movement or static].`
- **Close-Up:** `[Close-up] of [specific detail]. [CHARACTER/OBJECT, key features]. [Minimal background]. [Lighting on subject]. Shallow depth of field.`
- **Action:** `[Shot type] of [CHARACTER, appearance] in [LOCATION]. [Sequential action: "First A, then B, finally C"]. [Physics details]. Camera: [tracking / handheld / dynamic].`

## The Complete Prompt Writing Workflow

1. **Before any prompts:** Create the prompt bible (characters, locations, props, global style)
2. **For each shot:** Copy relevant anchors from the bible verbatim
3. **Write the prompt** following the structure formula: Scene -> Subject -> Action -> Camera -> Lighting -> Style
4. **Self-containment check:** Can someone with zero context understand this prompt?
5. **Consistency check:** Are all character/location/prop descriptions identical to the bible?
6. **Length check:** 80-150 words for video, flexible for image
7. **Anti-pattern check:** No pronouns? No abstract mood words? No conflicting instructions? Ground plane present?
