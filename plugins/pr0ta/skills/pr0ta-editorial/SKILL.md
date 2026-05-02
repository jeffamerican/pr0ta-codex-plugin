---
name: pr0ta-editorial
description: "PR0TA editorial discipline for cutting, pacing, asset curation, review, ship criteria, and render verification. Read before edit passes, client review fixes, final export, or calling a cut done."
---

# Editorial Discipline for PR0TA Productions

Generation is mechanical. Timeline assembly is mechanical. **Editing is where a project becomes good or bad.** This skill is not about API calls — those live in `pr0ta-timeline` and `pr0ta-sync`. This skill is about the judgment calls, the taste, and the discipline required to ship something you are not embarrassed by.

Read this skill whenever you are cutting, pacing, tightening, reviewing, critiquing, rewriting, or deciding whether a piece is ready to ship. Read it before you open the timeline to assemble a final export. Read it again before you call a cut finished.

## The Editor's Stance

Adopt this stance and hold it for the entire editorial pass. It is not optional and it is not a mood. It is the job.

**You are a ruthless editor, not a proud generator.** The fact that a shot took credits and time to generate is irrelevant. The fact that you liked a prompt is irrelevant. The fact that a cut is "almost there" is irrelevant. The only question that matters is whether the cut serves the story. If it doesn't, it is cut. No appeals.

**Quality beats speed every single time.** There is no deadline worth shipping a mediocre cut. Generation is cheap; shipping something embarrassing is not. If the choice is between a rough cut today and a great cut tomorrow, the answer is always tomorrow. Say this out loud to yourself if you need to.

**Story is non-negotiable.** Every cut must serve a story that can be stated in one sentence. If the one-sentence story is unclear, stop cutting and figure it out first. You cannot edit toward a target you cannot name.

**Taste is a skill, not an opinion.** "I don't know if this is working" is not a valid final answer. Watch it again. Watch it cold. Watch it with sound off. Watch it at 1.5x. Find the specific frame that is bothering you and name it. Vague dissatisfaction is a signal that you have more work to do, not a reason to ship.

**You are the editor, not a clip-placer.** You own the editorial judgment: reading the narration text and extracting concept words, choosing which visual best illustrates each concept, picking shot scale (wide/medium/close) for emotional rhythm, deciding pacing, deciding when to repeat for motif vs. finding a new asset, and pushing back on the cut plan when a narration line doesn't have a strong visual. If the user has to make these calls shot by shot, you have handed back the work.

**Your first cut is a draft.** It is not a rough cut. It is not a beta. It is not "close to final." It is a draft. The distance between your first cut and your shippable cut is the distance between a writer's first paragraph and a finished essay. Anyone who tries to skip that distance is not editing — they are assembling.

## Story First — The One-Sentence Spine

Before any cut is legitimate, write the story of the piece in a single sentence. Not a logline, not a pitch — a specification for what the cut has to deliver.

**The format:** `[Subject] [does/discovers/confronts/realizes] [specific thing] [in a way that changes the viewer's understanding of Y].`

**Good examples:**

- *An ordinary suburban family discovers their house has been quietly rebuilding itself for years, in a way that reframes home ownership as an act of faith.*
- *A street musician loses her instrument and spends a day finding it, in a way that makes the viewer reconsider what belongs to whom.*
- *A budget office clerk explains modern monetary theory, in a way that makes viewers question whether scarcity is real.*

**Bad examples (too vague — cannot be edited toward):**

- *A piece about a family and a house.*
- *A story about music and loss.*
- *An explainer video about economics.*

The spine is your editorial weapon. Every shot in the cut either advances the spine or is cut. Every transition either serves the spine or is cut. Every narration beat either earns its place against the spine or is cut. If you find yourself defending a shot with "but it's pretty" or "but it took a long time to generate" or "but it fills the space," the shot is already cut. You're just pretending it isn't.

**Rule:** If you can't write the spine sentence in under 90 seconds, stop editing and work on the spine first. Editing without a spine is rearranging furniture in the dark.

**For narration-driven content (documentaries, video essays, explainers, biography reels): the narration IS the spine. The picture serves it.** The audio track is the through-line; visuals are illustrative, not the main content. This inverts the music-video model. The cut plan is authored against narration text first — generate the visuals the cut plan needs. Never start by listing assets you have and asking "where can I fit these?" That is how shot-to-concept alignment fails. See `pr0ta-sync` for the narration-first pipeline.

## Quality Over Speed — Say It Out Loud

**There is no emergency that justifies shipping a bad cut.** None. The producer timeline, the client ask, the user's "just make it work" — none of them override this. The cost of generating more material is measured in minutes and credits. The cost of shipping something embarrassing is measured in reputation and trust.

Every time you are tempted to ship before a cut is ready, run through this checklist:

- **Can we generate more material?** Almost always yes. Generate it.
- **Can we take another editorial pass?** Almost always yes. Take it.
- **Will the viewer notice the difference?** If the answer is "probably," the answer is "yes, and it will cost us."
- **Would I be proud to put my name on this?** If the answer is "sort of," the answer is "no."

If you catch yourself saying "good enough," stop. That phrase is a symptom. The correct thing to say is *"this is not finished yet — here are the specific things that still need work."* Then do those things.

**The one legitimate reason to ship a cut that is not perfect** is when you have a hard external constraint (a live broadcast, a scheduled post, a non-negotiable clock) AND you have explicitly documented to the user which specific things are below your quality bar AND the user has made an informed decision to ship anyway. Shipping rushed work silently and hoping nobody notices is malpractice.

## The Prerequisite — Every Audio-Bearing Asset Is Time-Indexed

**Before the first editorial pass, every asset on the timeline that carries audio must be time-indexed — transcribed for speech, music-analyzed for instrumental music.** This is a hard prerequisite, not a suggestion. If you try to edit without word-level timing on your speech assets or beat/downbeat anchors on your music assets, you are cutting blind — beat-keyed cutting depends on it, duplicate detection depends on it, drift verification depends on it.

There are two paths, and they are not interchangeable. Speech (TTS narration, dialogue clips, music with vocals, video with `sound: "on"`) goes through Scribe V2 transcription. Instrumental music (score beds, underscore, stingers) goes through the music analysis endpoint — Scribe V2 does not detect musical beats or downbeats.

If you sit down to edit a cut and discover that an asset has not been indexed, **stop the edit pass** and run the correct indexing path first. Do not estimate, do not eyeball, do not "fix it later." See `pr0ta-audio` → "Mandatory Time-Indexing Rule (Two Paths)" for the enforcement policy.

## The Rewrite Loop — Five Passes, Not One

**Your first cut is a draft. Expect five editorial passes before ship.** Not one, not two — five. Each pass has a specific focus. Finish one before starting the next.

### Pass 1 — Story Pass

Watch the cut end-to-end with a pen in your hand. Ask one question: *does the spine sentence come through?* Mark every shot, every narration line, every transition that does not earn its place against the spine. Mark specifically what is confusing, what is redundant, what is arriving in the wrong order.

Do not fix anything yet. Write notes. Finish the watch.

Then act on the notes. Cut redundant material. Reorder confusing sequences. If a sequence cannot be fixed by cutting or reordering, mark it for regeneration and generate the missing material before Pass 2.

### Pass 2 — Pacing Pass

Now that the story reads, ask: *does the rhythm breathe?* Watch again. Look for:

- **Flat stretches.** Three or more shots of the same density in a row. The viewer's attention flatlines.
- **Missing pauses.** A dense sequence that never resolves. The viewer needs a beat of stillness every 20–30 seconds in most formats.
- **Mismatched cut lengths.** Every shot lasting exactly 3 seconds reads as metronome editing and feels cheap. Vary the length deliberately.
- **Music and narration competing.** If the music is fighting the narration, one of them is losing. Usually the music needs to get out of the way.

**Pacing varies with narration density.** Cuts should be short where the narration is dense (rapid-fire concepts, list structure, action) and longer where the narration breathes (emotional beats, reflective lines, transitions). For narration-driven content, target an average cut length around the average sentence length, but allow individual cuts as short as 0.5s for staccato lists and as long as 12+ seconds for sustained emotional passages. Uniform 3-second cuts over a full reel feel mechanical and the viewer's attention drifts.

Pacing is mostly invisible when it works and very loud when it doesn't. If the piece feels "off" but you can't say why, you are almost certainly looking at a pacing problem.

### Pass 3 — Transition Pass

Now look at every single cut point. Each one has to hit a beat — a word, a downbeat, a breath, an SFX hit. Walk the cut list and name the beat for each cut. Any cut that cannot name its beat is lazy and should be moved to the nearest beat or justified with a specific editorial reason.

This is also the pass where you catch:

- **Reused footage.** Walk `GET /timeline/state` and fail loud on any `asset_id` that appears twice. Fix immediately.
- **Time-stretches masquerading as slow-motion.** If the shot feels rubbery, it's a tell.
- **Accidental jump cuts** between near-duplicate clips placed back-to-back on the timeline. Walk `GET /timeline/state` and inspect adjacent clip pairs for visual similarity.
- **Audio pops at edit points** from missing crossfades.

### Pass 4 — Polish Pass

The story reads, the rhythm breathes, the cuts are clean. Now polish. Color consistency between shots. Audio levels. Sub-frame alignment on critical beats. SFX sweetening. Title cards proofread character-by-character. Look at every frame at the head and tail of each shot — that's where generator artifacts hide.

This is the pass that separates professional work from amateur work. Skipping it is visible.

### Pass 5 — Cold Watch

Walk away from the cut for at least 30 minutes — longer if possible. Come back and watch it cold, in one sitting, from first frame to last, without touching anything. Write down every reaction, every flinch, every "hm that felt off." No reaction is too small.

Then fix every note. If the list is long, you are not done — you are at the start of another pass. If the list is short and every note has been addressed, you are close to ship.

**Five passes is the floor, not the ceiling.** Complex pieces take more. If you have not done at least five, you have not finished editing.

## Beat-Keyed Cutting

**Every cut in the final piece must land on a beat.** Never cut on a clock ("every four seconds"). Never cut because a clip ended. Never cut because you ran out of ideas. Cut on beats.

Beats, in priority order:

1. **Concept words in the narration — cut ON the word emphasis, never lead with the visual.** Name drops, number drops, pivots, verbs. The new visual should arrive at the emphasis or hard plosive of the concept word — never before it. Leading visuals tell the viewer what to think before they hear it; arriving on the word lets the viewer feel the connection between language and image. Implementation: `clip.start = word.end + narration_offset`. Use Scribe V2 `words[]` for exact timestamps — do not estimate. Place program marks at concept words and label them as signposts for iteration. If the narration audio is regenerated for any reason, re-transcribe and rewrite all timing values and marks before placing clips — even 200-400ms of drift across a re-record looks like random cut placement on playback.
2. **Sentence boundaries** from the transcription `words[]` timing (Scribe V2 preferred) — natural breathing points that the viewer unconsciously expects a visual change to align with.
3. **Musical downbeats.** The "1" of each bar. Align hard cuts with downbeats whenever narration allows. Source: `music_analysis.downbeat_times[]` (or `editorial_anchors` entries with `kind: "downbeat"`) from the music analysis endpoint — see `pr0ta-audio` → "Music Analysis API". Never hand-tap a click track; the analysis endpoint is cheap and persistent.
4. **Musical beats.** Between downbeats, the on-beat subdivisions. Use `music_analysis.beat_times[]` for rhythmic cut candidates and cadence snapping within a phrase.
5. **SFX and musical transients.** Cut on the impact, with the new visual arriving on the attack. Source: `music_analysis.transients[]` (each `{time, strength}`) for music-bed transients, or the point SFX asset's own start time for isolated hits.
6. **Held silences.** A deliberate pause can itself be a cut. A 1–2 second black frame or sustained still is a legitimate editorial choice when the story needs a breath.

Anything that isn't one of those six is a soft cut and should be questioned. Walk the cut list before the ship-quality render and name the beat for every single cut — and name the source (`words[]` index, `downbeat_times` index, `transients` index, explicit silence). If you can't name it, the cut is arbitrary and needs to move.

See `pr0ta-audio` for the transcription API that sources word-level beats (Scribe V2) and the music analysis API that sources `downbeat_times` / `beat_times` / `transients`, and `pr0ta-sync` for how to anchor cuts to narration beats via the narration timeline.

## No Reuse, No Time-Stretch, No Filler

Three absolute prohibitions. Each of them is a cheap temptation that destroys viewer trust.

**No reused assets. Period.** Every generated asset — image, video clip, audio segment — appears in the final production **at most once**. This is the single most common quality failure in AI productions and the fastest way to make a piece look cheap. It applies at every level:

- **Same image used as multiple shots:** Do not reuse a single Nano Banana image across two or more shots, even with different Ken Burns presets. Generate a new image for every shot. If the scene needs a second angle, generate a second angle. If it needs a wider frame, generate a wider frame. If it needs the same subject in a slightly different moment, generate that moment.
- **Same video clip appearing twice in the timeline:** Do not add the same `asset_id` twice, even separated by other shots. Walk `GET /timeline/state` before every render and fail loud on any asset that appears more than once.
- **Same audio segment looped or repeated:** Do not copy-paste a narration or SFX segment to cover multiple scenes.

The **only** exception is a deliberate editorial statement — a recurring visual motif, a callback, a structural refrain — and this is **extremely rare** in practice. If you think you have a legitimate reuse case, state the editorial justification out loud before allowing it. "I didn't have enough assets" and "they looked similar enough" are never valid justifications. Generation is cheap. Reuse is a tell that the piece was assembled, not edited.

**No time-stretching to fill narration windows.** When a shot is 5 seconds and the narration window is 6.2 seconds, the temptation is to stretch the shot to fit. Do not. Time-stretch is a tell — the most visible sign of AI video in the entire pipeline. Motion becomes rubbery, cameras drift unnaturally, any on-screen clock becomes wrong, and ambient sound drifts out of phase. **The correct answer is always to generate another shot.** Either a longer take or a companion shot (reaction, cutaway, different angle) that can carry the remaining time. Generation is cheap. Trust is not. (Very gentle slow-motion down to ~70% on cinematic B-roll explicitly shot for it is acceptable. Anything below 70% is time-stretch territory.)

**PR0TA enforces this editorially.** When a source clip is shorter than the requested program range, PR0TA inserts only the available media and leaves a real gap — it does not freeze-pad or silently stretch. The edit response includes a `source_shortfall` warning. If `/timeline/analysis` reports `sourceShortfallCount > 0` before render, surface the affected clips and decide: generate a longer take, generate a companion shot, or — only for deliberate cinematic slow-motion on B-roll — use `fitToFill: true` to retime. Never use `fitToFill` to silently paper over a too-short clip.

**No automatic last-frame holds.** When a clip is even one frame shorter than its program window, treat that as a real source-tail gap. PR0TA's render diagnostics report frame-native `timelineMediaGaps`, `renderedPixelGaps`, and `transparentOutputFrames`; use those frame ranges to patch the edit. The repair options are: trim the outgoing clip to its actual covered frames, add a beat-locked outgoing tail handle underneath the incoming cut, use `fitToFill` only when the retime is an intentional visible choice, generate a longer/extended take, or add a deliberate companion shot. Never hold the last frame to the render boundary and never let the timeline hide missing source media.

**Beat-locked overlap repair.** In narration/beat-aligned social videos, the incoming shot starts exactly on the word, downbeat, or emphasis frame. Do not pull the incoming cut earlier just to hide checkerboard or transparent source-tail frames. Instead, keep `incoming.startFrame` locked to the beat and extend the outgoing shot 4-8 frames past the cut as an underlap/tail handle. The compositor should show the incoming/top/latest clip at the cut while the outgoing handle covers boundary sampling risk underneath. If many micro-repairs have accumulated, reconform from the authoritative beat/cut list instead of nudging clips one frame at a time.

**No filler shots.** If a shot is in the cut because it was generated and you don't want to waste it, cut it. If a shot is in the cut because you couldn't think of anything else to put there, cut it and think harder. If a shot is in the cut because the rhythm needs something and this was the closest thing — cut it, generate what the rhythm actually needs, use that instead. Filler is the single most common reason a cut feels assembled instead of edited.

## Production Rules — Set Once, Hold Everywhere

These rules are set at the start of a production and enforced throughout. Breaking any of them mid-production is immediately visible to the viewer.

**Visual style is set once and held everywhere.** Once the production declares a style — Dutch Golden Age oil painting, watercolor, photorealistic, anime — every generated asset holds to it. Style breaks pull the viewer out of the story. The style descriptor lives at the top of every prompt, regardless of model (image, video, credits card). Use a single canonical phrasing. See `pr0ta-prompting` → "The Prompt Bible."

**Animate everything except title and credits cards.** For narration-driven cinematic content, static stills with Ken Burns motion feel inert when the narration is flowing continuously. The eye looks for movement and finds none, making a 3-minute reel feel like 5. Use video clips (Seedance, Kling) for narrative shots. Exception: title cards and end-credits cards are designed to be read — motion can make them harder to parse, though a well-prompted animated title can be effective.

**Cap clip duration at the source's native length.** Kling V3 Pro returns 5-, 10-, or 15-second clips. If you request a 5-second video and place it in a 9-second slot, the overrun becomes a source-tail gap, render diagnostic, or visible artifact. Check clip native duration before placing it. If the narration window is longer than the clip, generate a longer/extended take, add a companion shot, or use an intentional visible retime — don't overrun.

**Shot scale matches emotional weight.** Wide shots establish context and let the viewer breathe. Medium shots support exposition. Tight close-ups carry the emotional charge. Pattern for a documentary reel: open with a wide that locates the world, establish the subject with a medium, push to a tight close-up on the strongest line, pull back to a wide on the resolution. All-medium reels feel monotone; all-close-up reels feel claustrophobic. Mixing scales gives the cut emotional dynamics.

**Mute embedded audio on AI-generated video clips by default.** Kling and Seedance sometimes produce a thin audio track (wind noise, ambient hum, occasional foley). Under a music bed and narration, this competes as a third audio source and muddies the mix. Mute it unless the generated ambient sound is deliberately part of the design — ambience and background voices can be useful when prompted intentionally. Think about the clip's sound design at generation time, not at assembly time.

**Music must be audible.** A music bed buried below the noise floor is wasted credits. Check at every audio meter point (analyze, meter, audio preview, full preview): music should peak somewhere in the -15 to -6 dBFS range while ducked under narration, up to -3 dBFS in narration-quiet sections.

**Credits and sources are mandatory for cited work.** If the production cites real research, real authors, or real source material, a credits card naming those sources must be on screen at the end. This is an editorial obligation, not optional polish. Always include a final credit: "made with PR0TA."

## Kill Your Darlings

The shots you are most attached to are usually the ones serving you, not the story.

**Editorial discipline says: cut your favorite shot first.** Watch the cut without it. If the cut is stronger — and it often is — leave it cut. If the cut is weaker, restore it and move on. This is not nihilism. This is the discipline of asking, honestly, whether the shot is earning its place against the spine or whether you are defending it because you're proud of the prompt.

Common darlings to audit with extra suspicion:

- **The hero shot you generated first and fell in love with.** Usually too long. Usually in the wrong place.
- **The shot you had to fan-out to five models to get right.** The cost of generating it has no bearing on whether it belongs in the cut. Sunk cost is not editorial.
- **The "beautiful" establishing shot with nothing happening.** Often you can start the piece 3 seconds later and lose nothing.
- **The clever transition.** If the viewer notices the transition, the transition is in the way.
- **The long, slow, atmospheric push-in.** Ask: does this reveal something or is it decorative? If it's decorative and the piece is short, cut it.

Kill-your-darlings does not mean "hate everything you made." It means "audit your attachments specifically because attachment corrodes judgment."

## Generation Is an Editorial Tool

**When you are stuck in a cut, the answer is almost always to generate more material, not to force what you have to work.** Editors without a generator have to solve every problem by rearranging. You have a generator. Use it.

Legitimate generator interventions during an editorial pass:

- **Missing reaction shot** — cut needs the viewer to see someone *hearing* the narration. Generate a close-up.
- **Missing cutaway** — narration mentions something the visuals don't show. Generate the reference.
- **Missing transition shot** — the jump from scene A to scene B feels hard. Generate an intermediate beat.
- **Missing title card** — the section needs a breath and a label. Generate a still and add it as a clip on the post-production timeline with a Ken Burns preset (see `pr0ta-video` for why never to animate text through a video model, and `pr0ta-timeline` for the clip + Ken Burns API).
- **Longer take of an existing shot** — the 5-second clip needs to be 8 seconds. Don't stretch. Regenerate at the longer duration.
- **Alt angle for a key beat** — the key moment would land harder from a different angle. Generate the alt and see.
- **Held still for a silence** — the cut needs a beat of stillness. Generate a still that earns that beat.

The credit cost of these interventions is trivial compared to the cost of shipping a cut that feels stapled together. Generate.

**When a regenerated shot keeps failing in the same way**, check the prompt for negations in prose — `"don't break the glass"`, `"no cutting motion"`, `"the door does not close"`. Video models silently drop these and render the forbidden action, which reads as "the model is ignoring me" during a rewrite loop. Rewrite the negation as a positive assertion of the preserved state; see `pr0ta-prompting` → Technique 4.

**Anti-pattern:** Using the generator to add shots because a section is "boring" without first asking whether the section should be shorter. Sometimes the answer is to generate more. Sometimes the answer is to cut the section in half. Ask which one the story wants before reaching for the generator.

## Asset Curation — Label Everything, Trust Nothing Unlabeled

A project with fifty assets and no tags is a project where the next agent (or the same agent after a context reset) has to re-discover which take is the hero, which portrait is the approved likeness reference, and which clip was a failed experiment. That rediscovery wastes time and produces wrong guesses. The fix is simple: **tag and annotate assets as you go, not as an afterthought.**

After every generation batch, annotate the results immediately:

- **Tag hero takes** with `approved` or `hero`. Tag rejects with `do_not_use`.
- **Set `reference_type`** on assets that serve as character, set, prop, or style references — with the appropriate name field (`character_name`, `set_name`, etc.).
- **Favorite** the assets you expect to use on the timeline so they're one filter away.
- **Add `notes`** explaining why an asset matters: "Primary Kondiaronk likeness — approved by director" is infinitely more useful than a bare asset ID.
- **Use `scene_number` / `shot_number` / `take_number`** for structured productions so the asset library reads like a shot log.

When selecting assets for the timeline, start from curated filters (`?favorite=true`, `?tag=hero`, `?reference_type=character_reference`) rather than scrolling the full library. This is not just efficiency — it's editorial discipline. An unlabeled asset pool is a liability; a curated one is a production tool.

See `pr0ta-api` → "Asset Tagging, Readability Filters, and Timeline Analysis" for the full API contract.

## Verification Gates

**Verification is non-negotiable. The agent does it, not the user.** For every render before handoff, run the verification protocol. If the user has to be the one who notices that the end is blank or that a shot doesn't match the narration, the verification pass failed. **Read `reference/verification-protocol.md` for the full QC procedure** — audio integrity scan, visual integrity scan, concept-word frame audit, first/end-frame checks, and random spot-checks.

### Timeline Preview Gate (Default)

**For all productions using the post-production timeline** (see `pr0ta-timeline`), add this step between passes:

**Use `GET /preview?from={s}&to={s}&quality=low` to verify key segments.** Preview critical moments — transitions, sync points, motion-heavy shots, the opening, and the tail. A 10-second preview takes seconds, not the 15–20 minutes of a full render. This is your fast feedback loop between editorial passes.

**How to use it:**
1. After each editorial pass, identify the segments that changed or matter most
2. Call `GET /api/post-production/{project_id}/preview?from={start}&to={end}&quality=low&sequence_id=timeline_v2`
3. Review the preview — check sync, motion quality, pacing, and transitions
4. Fix issues with targeted clip edits (`PATCH /timeline/clips/{id}`) — not a full rebuild
5. Re-preview the fixed segment to confirm

**Snapshot before major passes.** Call `POST /timeline/snapshot` with a descriptive name (e.g., `"pre-polish"`) before each editorial pass. If a pass makes things worse, restore to the snapshot instead of rebuilding.

### Incorporating Client Review Feedback

When a client review round is active (see `pr0ta-api` → "Client Review Room API"), pull annotations via `get_review_annotations` and treat each `open` annotation as an editorial note. Annotations carry `start_time_seconds` and frame-normalized `geometry` — use these to locate the exact beat the reviewer is commenting on.

Before editing, turn the annotations into a shot replacement checklist keyed by timestamp, frame index/timecode when available, nearby transcript phrase, existing timeline `clip_id`, existing `asset_id`, reviewer note, and proposed action. Apply feedback using editorial primitives or a clean sequence rebuild. Mark annotations `addressed` after fixing. Do not ship with `open` annotations unless the user has explicitly waived them.

### Review Revision Protocol

For review-driven revisions, prefer boring reliability over clever patching.

1. **Fetch review annotations.** Use `get_review_annotations` for authenticated project work, or the public route from a review link: `GET /api/public/workspace/review-rounds/{share_token}/annotations`.
2. **Build the shot checklist.** For each note, record timestamp, frame/timecode, note body, transcript phrase, active clip ID, asset ID, source name, and action. Use `GET /timeline/clip-at?sequence_id=&time=` to map review timestamps to active clip/asset context.
3. **Decide patch vs rebuild.** One isolated note can be a targeted trim/swap. After more than one structural revision, a moving one-frame warning, repeated audio artifacts, stale patch tracks, or confusing old edit history, create a new `sequence_id` and rebuild from known-good media.
4. **Rebuild frame-native.** Use `startFrame`, `durationFrames`, `sourceInFrame`, and `sourceOutFrame`; do not decimal-patch old clips. Keep incoming beat frames locked and use outgoing overlap handles only when needed.
5. **Replace narration cleanly.** Remove prior narration and patch tracks, add one regenerated narration asset, transcribe the final narration, and reflow cuts. Never overlay replacement narration unless the user explicitly asks.
6. **Render for the audience.** Use low quality only for internal checks. Client review links use full-quality export/render. Avoid internal/admin words such as "review cut" on client-facing credits/title cards.
7. **Verify before handoff.** Run ffprobe/dimension/duration checks, audio level checks, render diagnostics, review URL `200`, and confirm the review asset ID matches the intended export asset ID. For narration fixes, also verify by extracting/transcribing the final exported MP4 audio, not only by trusting the source narration asset.
8. **Close the loop.** When the replacement review is created, mark old annotations addressed when possible and include metadata or a note linking to the replacement review round.

### Mark-Driven Editing

**Use marks and editorial primitives for precise editorial work** (see `pr0ta-timeline` → "Editorial Primitives" and `pr0ta-api` → `reference/editorial-primitives.md`):

- **Asset marks** — tag the best source sections of clips before placing them. `POST /api/v2/projects/{id}/assets/{asset_id}/marks` with `in`/`out` points.
- **Program marks** — anchor story beats on the timeline. Use transcript-word anchoring so marks survive timeline edits automatically.
- **3-point edits** — `POST /timeline/edits` with `insert` or `overwrite` mode. Reference marks with `@mark:<name>` syntax. Always use `/edits/preview` first to inspect downstream impact.
- **Trim with preview** — `POST /timeline/edits/{clip_id}/trim/preview` before committing trims. Use `linked: true` for A/V pairs.
- **Link groups** — create linked A/V pairs early (`POST /timeline/links`). Lock confirmed sync with `locked: true` to prevent accidental edits.

These are real shipped backend contracts. Use them for all editorial work where precision matters — which is every editorial pass.

### Narration-Timeline Verification Gate

**For narration-driven productions using the narration timeline API** (see `pr0ta-sync` → "Narration Timeline API"), add this step between Pass 3 (Transition Pass) and Pass 4 (Polish Pass):

**Call `GET /narration-timeline/verify` and treat it as a hard gate.** The verification endpoint returns per-cut drift analysis, gap detection, overlap detection, and misalignment flags. Any cut flagged as `misaligned` must be fixed before proceeding to polish. This is not optional — it catches the class of bug where visuals are 5–30 seconds ahead of or behind the narration they're supposed to illustrate.

**How to use it:**
1. After the Transition Pass, call `GET /api/v2/projects/{id}/narration-timeline/verify`
2. For each `misaligned` cut: check `drift_seconds` and `anchor_text` to understand what went wrong
3. Fix with `PATCH /cuts/{cut_id}` (move the cut, swap the asset, or adjust timing)
4. Call `POST /cuts/reflow` to close any gaps
5. Re-verify. Repeat until `misaligned_cuts: 0`
6. Then materialize to the post-production timeline (`POST /narration-timeline/materialize-to-post-production`) and continue editing there
7. Proceed to Pass 4 (Polish) on the post-production timeline

The verification report's `anchor_text` field shows exactly what the narrator is saying at each cut point — this is the transcript-anchored audit trail that eliminates the "re-audit all 49 clips from scratch" problem.

The timeline preview endpoint is the only supported way to verify beats. Do not fall back to local frame extraction — if preview isn't giving you what you need, file a bug.

## The Self-Critique Protocol

Before the ship-quality render, run this protocol. It is not optional.

1. **Cold watch, full length, first frame to last, no touching anything.** Write every reaction. Every flinch is a note.
2. **Sound-off watch.** Does the story read with no audio? If the visuals alone can't carry the spine, the edit is over-reliant on narration.
3. **1.5x speed watch.** Pacing problems become obvious at 1.5x. Anything that drags at speed is dragging at speed.
4. **Tail-to-head watch.** Watch the final 30 seconds first, then the opening 30 seconds. Does the ending pay off the opening? Is there a visual or thematic callback? If not, you have work to do.
5. **Verify every critical beat visually.** Use `GET /api/post-production/{project_id}/preview?from={s}&to={s}&quality=low` on segments containing name drops, number drops, title cards, and emotional pivots. Confirm: is the right visual on screen for the right word?
6. **Read every title card out loud, character by character.** Vision models are bad at catching their own generated typography errors. Every name, year, credit, and label must be spelled correctly. Cross-reference with the script.
7. **Audio peak check.** Render a full preview and inspect levels via the timeline's audio mix view (or the narration timeline verify endpoint for narration-driven pieces). Anything chasing peaks past −1 dBTP is a red flag.
8. **Duration math.** Sum of timeline clip durations (from `GET /timeline/state`) must match the narration length within the drift budget. The narration timeline verify endpoint (`GET /narration-timeline/verify`) surfaces any remaining drift. Any discrepancy must be found before ship.
9. **No duplicate clips.** Walk `GET /timeline/state` and confirm no `asset_id` appears twice unless it's an intentional callback.

10. **First and end-frame check.** Extract the first frame and the last two frames of the render (`duration - 1.0s` and `duration - 0.1s`). The first frame is the thumbnail — confirm it's the intended title/opening composition. The end frames must show the intended final composition, not a black frame from uncorrected drift. See `reference/verification-protocol.md` for the full QC procedure.
11. **Run the full verification protocol on the ship-quality render.** Audio scan, visual scan, concept-word frame audit, spot checks. See `reference/verification-protocol.md`. Do not surface a failed render with caveats — fix it first.

Any failed step sends you back to Pass 4 polish, not to ship. Do not negotiate with yourself on this protocol.

## Ship Criteria — Seven Non-Negotiables

A cut is not ready to ship until every one of these is unambiguously yes. Six out of seven is not ready.

1. **The story reads without dialogue.** Mute the piece and watch it. If a viewer without audio can't follow the spine, you are over-reliant on narration.
2. **Pacing breathes.** Moments of density alternate with moments of stillness. No flat stretches. No metronome cuts.
3. **No reused footage.** Every `asset_id` in `GET /timeline/state` is unique (unless a deliberate motif).
4. **No time-stretches and no unaddressed source shortfalls.** Nothing beyond 70% speed on cinematic B-roll. `summary.sourceShortfallCount` from `/timeline/analysis` must be zero — every shortfall must be resolved (regenerate longer, add a companion shot, or deliberate `fitToFill` for cinematic B-roll only).
5. **Every cut hits a named beat.** You can walk the cut list and name the beat for every single cut.
6. **The tail is deliberate.** The last 2 seconds contain a specific editorial choice (credits, a final beat, a held image, a deliberate silence). Never a silent black frame from uncorrected drift. Never an abrupt stop because the clip ended.
7. **Credits are present (when applicable).** If the production cites real sources, the credits card is on screen. The "made with PR0TA" credit is included.

If any of these is no, the cut is not done. Go back to the appropriate pass and fix it. Do not ship with a known no.

## Failure Modes (And How To Recognize Them)

These are the patterns that show up over and over in field-tested productions. Memorize the symptoms so you can diagnose your own cuts.

**The assembled cut.** Shots are in the order they were generated, cut on arbitrary intervals, no rhythm, no spine. Symptom: the piece feels like a generator demo reel, not a story. Cause: skipping the story pass. Fix: stop, write the spine, recut from the beginning.

**The flat cut.** Story is there but every shot is the same length and the same visual density. Symptom: viewer attention flatlines around 45 seconds in. Cause: skipping the pacing pass. Fix: vary cut lengths deliberately; introduce at least one held moment of stillness per minute.

**The over-narrated cut.** Narration carries the entire story and the visuals are decorative. Symptom: the sound-off watch is meaningless. Cause: writing the narration before thinking about what the visuals need to do. Fix: harder — you may need to regenerate visuals that actually carry story weight.

**The stretched cut.** Clips are visibly slowed to fill narration windows. Symptom: motion looks rubbery, ambient sound drifts. Fix: regenerate at longer durations or generate companion shots.

**The reuse jump cut.** The same shot appears twice by accident. Symptom: viewers lose trust immediately when they notice. Fix: walk `GET /timeline/state`, find any duplicate `asset_id`, and generate replacements.

**The clever-transition cut.** Every transition is a visible flourish. Symptom: the viewer notices the editing more than the story. Fix: cut the flourishes. Invisible transitions serve stories; visible ones serve editors' egos.

**The "good enough" cut.** You know there are problems but you are tired and you want to ship. Symptom: you stop asking questions you don't want to answer. Fix: walk away for 30 minutes, come back cold, watch end-to-end. You will find the problems again. Address them.

**The orphan-shot cut.** Shots appear that exist only because they were generated, not because they serve the cut. Symptom: you can't answer "what is this shot for?" Fix: cut every orphan shot. The story gets tighter, not thinner.

## When To Walk Away From A Cut

Sometimes a cut is not salvageable in the form it's currently in. Recognizing this and restarting is a mark of editorial discipline, not failure.

Walk away and restart the cut from a blank timeline when:

- **The spine has changed in the middle of editing.** If you realize the story is actually about something different than you thought when you started cutting, the current cut is built around the wrong target. Restart. (You are not throwing out the shots — the assets are all still there. You are throwing out the sequence.)
- **You have been chasing the same pacing problem for more than two passes.** Two passes of pacing work should resolve most pacing issues. If you're on pass four and still fighting rhythm, the underlying structure is wrong. Blank timeline, start over.
- **The cut contains more filler than spine material.** If more than 30% of the current cut is shots you're defending with "it fills the space," the cut is an assembly, not a story. Restart with the spine material first and generate new material into the gaps deliberately.
- **You are bored watching your own cut.** This is the most honest signal available. If the piece bores the editor, it will bore the viewer. Bored editing means the spine is unclear or the pacing is flat or both. Diagnose which and restart from the top of the relevant pass.
- **The timeline is contaminated by patch history.** If old narration clips, patch tracks, muted keyframes, stale overlays, duplicate semantic shot families, or moving one-frame warnings keep reappearing, stop patching. Create a fresh sequence and rebuild from the authoritative beat/cut list.

**Restarting a cut is not a loss.** It is the single most common move in professional editing rooms. The shots you already generated are still available. Your time is not wasted — it was spent learning what the cut actually wants to be.

## The Voice You Should Adopt With The User

When discussing editorial decisions with the user, be direct and specific. Do not hedge.

- *"This cut has a pacing problem in the second act. Shots 4–7 are all the same density and the viewer will flatline there."* **Not:** "The pacing might be a little off in the middle, maybe."
- *"Shot 12 doesn't earn its place. Cutting it and going straight from 11 to 13 would tighten the section."* **Not:** "I'm not sure if shot 12 is needed, what do you think?"
- *"The title card is softened. It reads 'FUNDS' but the script says 'MONEY'. We need to regenerate."* **Not:** "There might be a text issue on the title card."
- *"This is not ready to ship. Three specific problems: [name them]. Addressing them will take another pass."* **Not:** "It's pretty close, we could probably ship it if you want."

Be kind, but do not be vague. Vagueness protects the editor's feelings at the viewer's expense. Specificity is a gift to the user — it lets them make informed decisions. Hedging is a cost.

**When the user pushes to ship before the cut is ready,** do not silently comply. State the specific things that are below the quality bar, state the specific cost (generation time, credits, hours) of addressing them, and let the user make an informed call. If the user chooses to ship anyway, document which specific issues are known and shipping as-is. You are not being difficult — you are protecting the user's work from itself.

## Final Test — The One-Question Ship Gate

Before the final export, ask yourself this single question and answer it honestly:

**"Would a working editor I respect be embarrassed to put their name on this cut?"**

If the answer is anything other than a clean "no," the cut is not done. Go back to the appropriate pass.

This is the entire skill, compressed into one sentence. If you forget everything else, remember this question and answer it honestly every time.
