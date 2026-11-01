"""
modules/pathway_seed.py

The starting pathway map: what's worth learning on guitar, grouped into branches, roughly in the
order things build on each other. It's a map, not a plan: you pick what to work on.

How it was put together:
- Order within branches follows the common sequence in graded rock/pop syllabi (e.g. Rockschool:
  minor pentatonic -> major pentatonic & 7th chords -> blues scale, arpeggios, barre chords) and
  JustinGuitar's intermediate modules (barre chords, technique, rhythm, major scale, groove).
- Each item has a concrete "done when" goal, so "comfortable" means something.
- Practice principles from motor-learning research are built into how the app nudges you:
  mix 2-3 areas in a session (interleaving tends to help long-term retention), come back to things
  after a gap (spacing -> the "getting rusty" list), track a tempo for anything metronome-able,
  and record yourself now and then (feedback you can't get while playing).
Edit freely in the app: add, rename, reorder, delete.
"""

BRANCHES = ["Fretboard", "Scales", "Chords", "Rhythm", "Technique", "Theory & ear", "Application"]

BRANCH_ICONS = {
    "Fretboard": ":material/grid_on:",
    "Scales": ":material/stairs:",
    "Chords": ":material/piano:",
    "Rhythm": ":material/graphic_eq:",
    "Technique": ":material/back_hand:",
    "Theory & ear": ":material/hearing:",
    "Application": ":material/music_note:",
}

BRANCH_IDS = {"Fretboard": "fb", "Scales": "sc", "Chords": "ch", "Rhythm": "rh",
              "Technique": "te", "Theory & ear": "th", "Application": "ap"}

STATUSES = ["Not started", "Working on", "Comfortable", "Solid"]
SONG_STATUSES = ["Wishlist", "Learning", "Polishing", "Learned", "Paused"]

_P = "pages/"
T_SCALES = _P + "1_Scale_Reference.py"
T_FRET = _P + "2_Fretboard_Tester.py"
T_PROG = _P + "3_Chord_Progressions.py"
T_EAR = _P + "4_Ear_Training.py"
T_CHORDS = _P + "6_Chord_Dictionary.py"
T_CIRCLE = _P + "7_Circle_of_Fifths.py"
T_ARP = _P + "8_Arpeggio_Visualizer.py"
T_FUNC = _P + "13_Functional_Ear_Trainer.py"
T_METRO = _P + "14_Metronome.py"

# (branch, name, done when, how to practise, tool page)
_ITEMS = [
    # Fretboard
    ("Fretboard", "Notes on the low E & A strings", "Name any note on strings 6 and 5 in under 3 seconds",
     "2-3 minutes of quizzing at the start of a session; say the note out loud as you play it", T_FRET),
    ("Fretboard", "Notes on all strings (octave shapes)", "Find every C (or any note) across the neck in one pass",
     "Use octave shapes from the 6th/5th string notes you know; pick one note per day", T_FRET),
    ("Fretboard", "Intervals on the neck", "From any root, find its 3rd, 5th and octave without counting frets",
     "Play root-3rd-5th shapes on different string pairs; sing the interval", T_SCALES),
    ("Fretboard", "Triad shapes across string sets", "Play major/minor triads on the top 3 strings in 3 inversions",
     "Move one triad up the neck through its inversions, then do the same in a progression", T_ARP),

    # Scales
    ("Scales", "Minor pentatonic: box 1", "Play it up and down cleanly at 80 bpm in 8th notes",
     "Metronome, alternate picking; then improvise with only these notes over a backing track", T_SCALES),
    ("Scales", "Minor pentatonic: all 5 boxes", "Connect the boxes and slide between them in one key",
     "Learn one new box per week; practise moving between neighbouring boxes", T_SCALES),
    ("Scales", "Major pentatonic", "Play it from the same shapes (relative major) and hear the difference",
     "Play the same box over a major backing track; notice which notes sound like 'home'", T_SCALES),
    ("Scales", "Blues scale", "Add the b5 to the minor pentatonic in 2 positions",
     "Use the b5 as a passing note, not a landing note; play a 12-bar blues over it", T_SCALES),
    ("Scales", "Major scale: 2 positions", "Play the major scale with a 6th- and a 5th-string root at 80 bpm",
     "Say the scale degrees as you play; then play simple melodies in that shape", T_SCALES),
    ("Scales", "Natural minor scale", "Play it in 2 positions and relate it to the major scale",
     "Practise A minor and C major in the same position to see the shared notes", T_SCALES),
    ("Scales", "Major scale: all positions (3NPS)", "Play 3-notes-per-string major scale across the neck",
     "Slow first, metronome up 4 bpm when clean 3 times in a row", T_SCALES),
    ("Scales", "Modes in context", "Hear and use Dorian and Mixolydian over a vamp",
     "Loop one chord (e.g. Am7 for Dorian) and target the note that makes the mode sound different", T_SCALES),

    # Chords
    ("Chords", "Open chords + clean changes", "Change between any two of C, G, D, A, E, Am, Em, Dm 40+ times a minute",
     "One-minute changes: pick a chord pair, count changes in 60s, try to beat it next time", T_CHORDS),
    ("Chords", "Power chords", "Move power chords around the neck in time with a song",
     "Mute with the picking hand; play along with a rock song", T_CHORDS),
    ("Chords", "Barre chords: E & A shapes", "Clean major and minor barre chords, change within 2 beats",
     "Short daily reps beat long sessions; check each string rings, relax between reps", T_CHORDS),
    ("Chords", "7th chords", "Play dom7, maj7 and m7 as open and barre shapes",
     "Swap them into songs you know (e.g. G -> Gmaj7) to hear the colour", T_CHORDS),
    ("Chords", "Triads & inversions", "Play a I-IV-V progression with triads in one area of the neck",
     "Find the smallest movement between chords (voice leading)", T_ARP),
    ("Chords", "CAGED system", "Play one chord in all 5 CAGED shapes up the neck",
     "Link each shape to the scale/arpeggio around it", T_ARP),
    ("Chords", "Extended chords (9/11/13)", "Recognise and play a 9th, 11th and 13th voicing",
     "Use them in a funk or neo-soul vamp", T_ARP),

    # Rhythm
    ("Rhythm", "Steady downstrokes with a metronome", "Play quarter-note downstrokes locked to the click, 60-100 bpm",
     "Count out loud; record yourself and check you land on the click", T_METRO),
    ("Rhythm", "8th-note strumming patterns", "Keep the hand moving down-up and play D DU UDU in time",
     "Constant motion: the hand never stops, you just miss the strings", T_METRO),
    ("Rhythm", "16th-note strumming & muting", "Play a 16th-note pattern with ghost strums and accents",
     "Start at 60 bpm; mute with the fretting hand for percussive hits", T_METRO),
    ("Rhythm", "Syncopation & accents", "Play pushes/anticipations (chord changes on the 'and') cleanly",
     "Tap the pattern first, then strum; play along with funk/pop recordings", T_METRO),
    ("Rhythm", "Palm muting", "Switch between palm-muted and open strums mid-bar",
     "Rest the edge of the picking hand right at the bridge; record and listen back", T_METRO),
    ("Rhythm", "Fingerstyle / Travis picking", "Keep an alternating bass with the thumb while picking melody",
     "Thumb alone until it's automatic, then add one finger at a time", T_METRO),
    ("Rhythm", "Groove & feel", "Play the same pattern straight and swung, and along with a record",
     "Play along with real songs, not just the click", T_METRO),

    # Technique
    ("Technique", "Alternate picking", "Chromatic 1-2-3-4 exercise clean at 100 bpm in 8th notes",
     "Small pick movements, metronome, +4 bpm when clean 3 times", T_METRO),
    ("Technique", "Hammer-ons & pull-offs", "Even volume between picked and slurred notes",
     "Pentatonic trills in one position for a minute each finger pair", T_SCALES),
    ("Technique", "Slides", "Land slides exactly on the target fret by ear and eye",
     "Slide between scale notes; look at the target, not your finger", T_SCALES),
    ("Technique", "Bends in tune", "Half- and whole-tone bends that match the target pitch",
     "Play the target note first, then bend to match it; unison bends", T_SCALES),
    ("Technique", "Vibrato", "Controlled, even vibrato on a held note at two speeds",
     "Rotate from the wrist; practise on the 2nd/3rd string in the 7th-10th frets", None),
    ("Technique", "String skipping & hybrid picking", "Clean arpeggio patterns skipping strings",
     "Slow, accurate picking; mute strings you're not playing", T_ARP),
    ("Technique", "Legato runs", "3-notes-per-string runs with one pick per string, even timing",
     "Metronome; accent the first note of each group", T_SCALES),

    # Theory & ear
    ("Theory & ear", "Keys & the circle of fifths", "Name the sharps/flats in any key and its relative minor",
     "Two minutes of quizzing; relate each key to songs you know", T_CIRCLE),
    ("Theory & ear", "Chords in a key", "Name and play I-ii-iii-IV-V-vi in C, G, D, A, E",
     "Use the progression tool; play I-vi-IV-V in each key", T_PROG),
    ("Theory & ear", "Intervals by ear", "Recognise the intervals within an octave by ear, 80%+ in the trainer",
     "A few minutes a day beats one long session", T_EAR),
    ("Theory & ear", "Scale degrees by ear", "Hear which scale degree a note is in a key, 80%+",
     "Functional ear training: always hear notes against the key centre", T_FUNC),
    ("Theory & ear", "Common progressions & 12-bar blues", "Recognise and play I-IV-V, I-V-vi-IV, ii-V-I, 12-bar blues",
     "Play each in 3 keys; spot them in songs you like", T_PROG),
    ("Theory & ear", "Key changes (Fretjam)", "Explain and play a dominant key change and a relative key change",
     "Follow the Fretjam lesson, then find one in a song", T_PROG),
    ("Theory & ear", "Transcribe a riff by ear", "Work out a short riff or melody from a recording without tabs",
     "Loop and slow down the recording; sing it before you find it", None),

    # Application
    ("Application", "Improvise with pentatonic licks", "Play 3-4 licks you know over a backing track and connect them",
     "Learn one lick from a song, then use it in 3 different ways", T_SCALES),
    ("Application", "Target chord tones", "Land on the 3rd of each chord as the changes go by",
     "Slow 2-chord vamp; aim for the chord tone on beat 1", T_ARP),
    ("Application", "Write a riff or short solo", "Compose and record an 8-bar riff or solo",
     "Use only what you know; record it", None),
]


def seed_rows() -> list[dict]:
    """Rows for the 'pathway' table, used the first time the app runs."""
    rows, counters = [], {}
    for branch, name, goal, how, tool in _ITEMS:
        counters[branch] = counters.get(branch, 0) + 1
        prefix = BRANCH_IDS[branch]
        rows.append({
            "id": f"{prefix}{counters[branch]:02d}",
            "branch": branch,
            "order": counters[branch],
            "name": name,
            "goal": goal,
            "how": how,
            "tool": tool or "",
            "status": "Not started",
            "last_practiced": "",
            "next_note": "",
            "bpm": "",
        })
    return rows
