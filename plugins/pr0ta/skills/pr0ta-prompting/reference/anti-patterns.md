# Prompt Anti-Patterns (Full Reference)

The following anti-patterns break visual consistency and cause generation failures. Avoid all of them.

### 1. Pronouns and Assumed Context
**Bad:** "She picks up the device and examines it."
**Good:** "Sarah picks up the bronze compass with jade-green patina and holds it at eye level, turning it slowly."

### 2. Shifting Descriptors
**Bad:** Shot 1 says "brown trench coat," Shot 2 says "coat," Shot 3 says "jacket"
**Good:** Every shot says "brown canvas trench coat with brass buttons"

### 3. Abstract Mood Words Without Specifics
**Bad:** "Dramatic, cinematic, beautiful, stunning, awesome"
**Good:** "Single hard key light from camera-left, deep shadows, cool blue fill, 35mm film grain"

### 4. Conflicting Instructions
**Bad:** "Wide establishing shot showing the full room AND close-up of her expression"
**Good:** Two separate prompts -- one for the wide, one for the close-up

### 5. Missing Ground Plane
**Bad:** "Sarah walks through the scene"
**Good:** "Sarah walks across the polished marble floor of the glass-walled lobby"

### 6. Keyword Soup
**Bad:** "portrait beautiful woman elegant lighting studio professional quality amazing"
**Good:** "Three-quarter portrait of Sarah, navy blazer, soft key light from camera-left, grey seamless background, 85mm lens, shallow depth of field"

### 7. Over-Complex Single Prompts
**Bad:** A 300-word prompt trying to choreograph an entire scene
**Good:** Multi-prompt segments (for video) or sequential image generations, each with focused 80-150 word prompts

### 8. Pattern-Heavy Descriptions
**Bad:** "Wearing a striped floral pattern dress" (patterns cause variance across frames)
**Good:** "Wearing a solid charcoal dress with clean lines" (solid colors are more stable)

### 9. Ambiguous Numeric Progressions
**Bad:** "Count down from 9 to 1 over 2.5 seconds" (model will hallucinate intermediate values)
**Good:** Enumerate every state with an explicit timestamp -- see Technique 1. Use Seedance 2.0 Omni for any enumerated-state shot.

### 10. Relying on Reference Context in Prose
**Bad:** "The same scene, now at sunset." (prompt is not self-contained -- reference may be ignored)
**Good:** Fully re-describe every element of the scene (subject, environment, lighting, camera) and add the change as an additive clause at the end.

### 11. Negations Embedded in Prose
**Bad:** "The craftsman polishes the statue. Don't break it. No cutting."
**Good:** Rewrite as a positive assertion of the preserved state -- see Technique 4. Video models drop `don't` / `no` / `does not` from prose prompts and render the forbidden action. Keep negations in the dedicated `negative_prompt` field; never in the main prompt body.
