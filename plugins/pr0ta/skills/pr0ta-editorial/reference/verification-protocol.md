# Render Verification Protocol

> **See also:** For editorial judgment and the five-pass rewrite loop, read the parent `pr0ta-editorial` SKILL.md. For timeline preview and render endpoints, read `pr0ta-timeline`.

## Why This Exists

The user's instruction: "YOU ALWAYS HAVE TO CHECK YOUR WORK. THIS IS BASIC."

If the user has to be the one who notices that the end is blank, that a shot doesn't match the narration, or that there's a silent gap in the audio, the verification pass failed. The agent does the QC, not the user. This protocol is the gate between "I rendered something" and "I can show this to the user."

---

## When to Run

Run this protocol on **every render before handoff** — preview renders during editorial passes and final exports before delivery. The scope scales: previews get a lighter pass (steps 1, 3, 5); final exports get the full protocol.

---

## The Full Protocol

### Step 1: First and End-Frame Discipline

The first frame of a social-media video is the thumbnail — it determines whether the viewer clicks. The final frame is what the viewer takes away. Both must be intentional.

The renderer can drop frames at the very end if a clip's allocated timeline slot exceeds its native duration. Do not trust the timeline's reported duration alone.

**Mandatory checks before declaring a render done:**

```bash
# Get actual duration
ffprobe -v error -show_entries format=duration -of csv=p=0 output.mp4

# Extract near-end frames
ffmpeg -ss $(echo "$DURATION - 1.0" | bc) -i output.mp4 -frames:v 1 qc_frames/end_minus_1s.jpg
ffmpeg -ss $(echo "$DURATION - 0.1" | bc) -i output.mp4 -frames:v 1 qc_frames/end_minus_0.1s.jpg

# Extract first frame
ffmpeg -ss 0 -i output.mp4 -frames:v 1 qc_frames/first_frame.jpg
```

View all three frames. Confirm:
- First frame shows the intended thumbnail/title composition
- Both end frames show the intended final composition (credits card, final beat, fade-to-black)
- Neither end frame is an unintentional black frame, transparency artifact, or frozen mid-transition

### Step 2: Audio Integrity Scan

Check for silent windows of 1+ seconds anywhere in the audio. Do **not** trust integrated loudness or `volumedetect mean_volume` — those average across the whole file and hide localized dropouts.

```bash
# Detect silent gaps (threshold: -50dB for 1+ second)
ffmpeg -i output.mp4 -af silencedetect=noise=-50dB:d=1.0 -f null - 2>&1 | grep silence_
```

If silence is detected:
- Check whether it's intentional (a deliberate pause, a breath between sections)
- If unintentional, trace back to the timeline — is there a gap between clips? A missing audio track? A clip with no audio source?
- Fix the timeline and re-render before showing the user

Also verify music audibility: the music bed must be present at a measurable level, not buried below the noise floor. Peak somewhere in the -15 to -6 dBFS range while ducked under narration; up to -3 dBFS in narration-quiet sections. A music bed you can't hear is wasted credits.

For timelines with music automation, explicitly test at least one narration gap after render. A simple failure check is to run `silencedetect` on the full rendered mix and inspect any silence window that overlaps a section where the music bed should be audible. For API-driven checks, meter or preview a narration-quiet window rather than relying only on whole-file loudness.

### Step 3: Concept-Word Frame Audit

For narration-driven productions, verify that the right visual is on screen at the right moment. For every concept word in the cut plan, extract a frame at the moment the viewer should see the matching visual:

```bash
# For each concept word: word.end + narration_offset + 0.4s
ffmpeg -ss $AUDIT_TIME -i output.mp4 -frames:v 1 "qc_frames/cut_${IDX}_${ANCHOR}_${TIME}s.jpg"
```

View each extracted frame and confirm:
- The visual content matches what the narration is describing at that moment
- The shot has arrived (not still showing the previous cut)
- The shot is not a black frame or transition artifact

Save all frames to a `qc_frames/` folder with the naming convention `cut_<idx>_<anchor>_<time>s.jpg` so the user can spot-check them later.

### Step 4: Visual Integrity Scan

Scan for transparency artifacts, unintentional black gaps, or frozen frames that aren't part of the editorial design:

```bash
# Per-frame luminance scan — detect near-black frames
ffmpeg -i output.mp4 -vf "blackdetect=d=0.5:pix_th=0.10" -f null - 2>&1 | grep black_
```

If black frames are detected, check whether they're intentional fades or gaps between clips. Unintentional black frames usually mean a clip's timeline slot extends past its native duration, or there's a gap in the track.

### Step 5: Spot-Check Random Frames

Extract 3-5 frames at random positions throughout the production:

```bash
# Random spot checks across the duration
for t in $(python3 -c "import random; d=$DURATION; print(' '.join(f'{random.uniform(0.5,d-0.5):.1f}' for _ in range(5)))"); do
  ffmpeg -ss $t -i output.mp4 -frames:v 1 "qc_frames/spot_${t}s.jpg"
done
```

View each and check for:
- Generator artifacts (warped faces, melted text, impossible geometry)
- Style breaks (a photorealistic frame in an otherwise painterly production)
- Aspect ratio or letterboxing issues
- Visual quality degradation

---

## The Gate

This protocol is a gate, not a checklist to hand-wave through. If any step fails:

1. Identify the specific issue in the timeline
2. Fix it (swap a clip, adjust timing, regenerate, re-mix)
3. Re-render
4. Re-run the full protocol on the new render

Do not surface a failed render with caveats ("there's a small issue at 2:15 but otherwise it's fine"). Fix it first. The user should never see a render that hasn't passed QC.

---

## Lighter Pass for Preview Renders

During editorial iteration (between passes), run a reduced protocol:

1. **End-frame check** — confirm the preview doesn't trail off into black
2. **Concept-word spot-check** — pick 3-5 concept words at critical moments, extract frames, confirm visual alignment
3. **Audio spot-check** — listen to the first 5 seconds, last 5 seconds, and one section in the middle for obvious issues

Save the full protocol for the ship-quality render. But never skip QC entirely — even a lightweight pass catches the most common failures.
