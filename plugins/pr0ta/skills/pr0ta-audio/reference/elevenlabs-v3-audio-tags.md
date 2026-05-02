# ElevenLabs v3 Audio Tags

Read this only when using the ElevenLabs v3 fallback (`model: "eleven_v3"`) or maintaining a legacy ElevenLabs-tagged workflow. For new PR0TA TTS, prefer Gemini Flash TTS and the main `pr0ta-audio` Gemini prompting section.

## Syntax

Eleven v3 interprets words in square brackets as performance directions. Tags are v3-specific; older ElevenLabs models ignore them.

Place tags inline in the text, before or within the speech they modify:

```text
[sorrowful] I couldn't sleep that night... [quietly] And suddenly, that's when I saw it.
```

Tags can be combined:

```text
[hesitant][nervous] I... I'm not sure this is going to work. [gulps]
```

## Tag Reference

**Emotional states:** `[excited]`, `[nervous]`, `[frustrated]`, `[sorrowful]`, `[calm]`, `[angry]`, `[sad]`, `[cheerfully]`, `[flatly]`, `[deadpan]`, `[playfully]`, `[annoyed]`, `[flustered]`, `[casual]`, `[tired]`, `[curious]`, `[resigned]`

**Reactions and human sounds:** `[sigh]`, `[laughs]`, `[gulps]`, `[gasps]`, `[whispers]`, `[shouts]`, `[clears throat]`, `[soft chuckle]`, `[crying]`, `[breathes]`, `[swallows]`

**Delivery and pacing:** `[pause]`, `[continues after a beat]`, `[rushed]`, `[slows down]`, `[deliberate]`, `[rapid-fire]`, `[stammers]`, `[drawn out]`, `[timidly]`, `[emphasized]`, `[understated]`, `[continues softly]`, `[hesitates]`

**Narrative tone:** `[dramatic tone]`, `[lighthearted]`, `[reflective]`, `[serious tone]`, `[conversational tone]`, `[sarcastic tone]`, `[wistful]`, `[matter-of-fact]`, `[awe]`

**Character and accent:** `[British accent]`, `[Australian accent]`, `[Southern US accent]`, `[French accent]`, `[American accent]`, `[childlike tone]`, `[fantasy narrator]`, `[sci-fi AI voice]`, `[classic film noir]`

**Sound effects, experimental:** `[gunshot]`, `[applause]`, `[explosion]`, `[leaves rustling]`, `[gentle footsteps]`, `[clapping]`

## Dialogue

Tag the emotional shift, not just the base emotion:

```text
[excited] You won't believe what I found down there!

[skeptical][dry] Let me guess -- another "ancient artifact" that turns out to be a pipe fitting.

[defensive] No, this is different. [quieter, more serious] This one was moving.
```

Use reaction tags between lines for conversational texture. Use dashes for interruptions and ellipses for trailing thoughts.

## Narration

Set a base tone at the start of a passage, then add moment-specific tags sparingly:

```text
[reflective] I never thought I'd say this, but... [pause] maybe the machine was right.

[building intensity] The signal was getting stronger. Every reading confirmed what we'd feared.
[whispers] And then -- silence. Complete, absolute silence.

[awe] When I opened my eyes, the sky had changed color.
```

Use `[pause]` and `[continues after a beat]` for dramatic pacing when punctuation is not enough.

## Punctuation

Eleven v3 treats punctuation as implicit delivery direction:

- Ellipses create pauses and trailing-off effects.
- Dashes create abrupt stops and interruptions.
- Caps add emphasis to specific words.
- Exclamation marks increase energy; question marks add rising inflection.
- Short sentences speed up pacing; long flowing sentences slow it down.

## Constraints

- SSML is not supported in v3. Do not use `<break>`, `<phoneme>`, or other SSML tags.
- Voice selection matters more than tags. Match the voice to the emotional range you need.
- Professional Voice Clones are not optimized for v3. Use Instant Voice Clones or prompt-designed voices for better tag responsiveness.
- Tags are suggestive, not deterministic. Regenerate if a take does not land.
- Stability affects expressiveness. Higher stability is more consistent but less dynamic.
- Keep dialogue under 2000 characters per call for Text to Dialogue. Standard TTS allows up to 5000 characters.
