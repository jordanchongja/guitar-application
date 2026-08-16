# Guitar Learning App (Streamlit) - Project Roadmap and Plan

This document outlines the roadmap, feature assessment, and tasking for building a comprehensive Guitar Learning App using Streamlit. This plan is designed to be handed off to an LLM (like Claude) for step-by-step implementation.

## Feature Assessment

Your suggested features are **excellent** and form a very solid foundation for a comprehensive guitar learning tool. Streamlit is particularly well-suited for this because of its interactive widgets (`st.selectbox`, `st.slider`) and ability to render charts/images (for fretboards).

Here is an assessment of your proposed features:

1. **Scale Reference & Chord Progressions:** Very useful. Adding CAGED shapes will make this practically applicable for guitarists.
2. **Fretboard Tester:** A killer feature. Using libraries like `matplotlib`, `plotly`, or even custom SVG/HTML generation within Streamlit will make this highly interactive.
3. **Theory & Reference (Circle of Fifths, Chord Dictionary, Interval Cheatsheet):** Essential for a complete learning hub.
4. **Practice Builders & Progress Tracker:** Great for user retention. SQLite is perfect for local state/tracking.
5. **Ear Training & Audio:** Excellent use of `st.audio`. This bridges the gap between visual learning and aural skills.
6. **Customization (Tuning, Left-Handed Mode):** Highly requested features in any guitar app. 

### Additional Feature Suggestions

To make the app even more comprehensive, consider these additions:

* **Arpeggio Visualizer:** Similar to scales, but showing Major 7, Minor 7, Dominant 7, and Diminished arpeggio shapes across the fretboard. Essential for lead playing and jazz.
* **Sight-Reading Trainer:** Displays a note on standard musical notation (sheet music) and asks the user to find it on the fretboard (or vice-versa).
* **"Daily Challenge" / "Riff of the Day":** A randomized daily goal (e.g., "Play a II-V-I in Bb minor" or "Find all the E notes on the fretboard in 30 seconds").
* **Custom Tuning Builder:** Instead of just presets (Drop D, Open G), allow the user to select the tuning for each string individually.

---

## Roadmap

The project should be broken down into iterative phases to ensure stable development.

### Phase 1: Core Foundation & Theory (The "Reference" Phase)
* **Setup & UI Skeleton:** Basic Streamlit layout with sidebar navigation.
* **Scale Reference:** Implementation of Major, Minor, Pentatonic scales with Key selection.
* **Fretboard Visualization:** Building the core rendering engine for the fretboard (e.g., a reusable Python function that takes notes/positions and returns a Plotly/Matplotlib chart or SVG).
* **Left-Handed & Tuning Toggles:** Implementing the logic to flip the fretboard and adjust string intervals.

### Phase 2: Interactive Testing (The "Quiz" Phase)
* **Fretboard Tester:** Implementing the quiz logic (highlighting a fret, providing multiple-choice answers, tracking score).
* **Chord Dictionary:** Allowing users to click frets and calculating the resulting chord.
* **Progress Tracking:** Integrating SQLite to save quiz scores and practice time.

### Phase 3: Advanced Theory & Practice (The "Application" Phase)
* **Chord Progression Generator:** Logic to generate diatonic chords based on the selected key.
* **Interactive Circle of Fifths:** Visual representation of key signatures.
* **Randomized Practice Generator:** Logic to pull from a list of exercises and generate a timed routine.
* **Arpeggio Visualizer:** Adding arpeggios to the reference section.

### Phase 4: Audio & Ear Training (The "Aural" Phase)
* **Audio Setup:** Integrating `st.audio` and managing sound files (or using synthesis libraries like `scipy.io.wavfile` or `pydub` to generate tones on the fly).
* **Interval & Chord Quality Quizzer:** Playing sounds and taking user input.
* **Jam Track Embeds:** Adding YouTube embeds for practice backing tracks.

---

## Claude Prompting & Tasking Guide

Copy and paste the following prompts into Claude to guide the development process step-by-step. 

> [!TIP]
> Do not ask Claude to build the whole app at once. It will lose context and introduce bugs. Use the modular prompts below.

### Initial Setup Prompt
```text
I want to build a comprehensive Guitar Learning App using Python and Streamlit. 

Here are the core requirements:
- Use standard Streamlit widgets for navigation (e.g., st.sidebar).
- The app needs a highly modular structure. Create a `main.py` and separate files for different pages/features in a `pages/` or `modules/` directory.
- We need a reusable fretboard visualization function. Please recommend the best library for this in Streamlit (Matplotlib, Plotly, or custom SVG/HTML) and write a base function that draws a standard 22-fret guitar neck.
- Add a sidebar toggle for "Left-Handed Mode" that we will use to horizontally flip our visualizations later.

Please provide the directory structure and the initial `main.py` code to set up the skeleton of this app.
```

### Task 1: Scale Reference & Fretboard Visualization
```text
Now, let's build the "Scale Reference" page. 
Requirements:
1. Two dropdowns: "Key" (C, C#, D, etc. - default C) and "Scale Type" (Major, Minor, Major Pentatonic, Minor Pentatonic).
2. A toggle for "CAGED Position" (1 through 5, or "All Neck").
3. Use the fretboard visualization function we discussed. It needs to highlight the correct notes for the selected scale and key. Root notes should be a different color.
4. Ensure the "Left-Handed Mode" state flips the visual representation.

Provide the code for this module and explain how it integrates into the main app.
```

### Task 2: The Fretboard Tester Quiz
```text
Next, let's build the "Fretboard Tester". This is an interactive quiz.
Requirements:
1. The app highlights a single random coordinate on the fretboard (e.g., 3rd string, 5th fret).
2. Provide 4 multiple-choice buttons for the user to guess the note.
3. Allow the user to customize the quiz via checkboxes: "Include Sharps/Flats", "Limit to specific strings", "Limit to frets 1-12".
4. Keep track of the user's score in the current session using Streamlit's `st.session_state`.
5. Show a "Correct!" or "Incorrect, that was a [Note]" message after they guess, and a "Next Question" button.

Write the code for this module.
```

### Task 3: Chord Progression Generator
```text
Let's add the "Chord Progression Generator".
Requirements:
1. Dropdown to select a Key.
2. Display the diatonic chords for that key (I, ii, iii, IV, V, vi, vii°).
3. A button to "Generate Progression". When clicked, pick a common progression pattern (e.g., I-IV-V, ii-V-I, I-vi-IV-V) and display the actual chords for the selected key.
4. Underneath the generated progression, embed a YouTube video of a backing track for that key (e.g., if they pick C Major, show a C Major backing track). You can use placeholder URLs for now.

Write the code for this module.
```

### Task 4: Ear Training (Intervals)
```text
Let's build the "Ear Training" module. We will start with Intervals.
Requirements:
1. We need a way to generate or play two tones. If you recommend using pre-recorded .wav files, explain the naming convention we should use. Alternatively, can we generate simple sine wave tones dynamically in Python and pass them to `st.audio`? Let's go with dynamic generation if possible so we don't need external assets.
2. Play a root note, wait 0.5 seconds, then play a second note.
3. The user must guess the interval (Minor 3rd, Perfect 5th, etc.) via multiple choice.
4. Track the score using `st.session_state`.

Provide the implementation for this module.
```

### Task 5: Database & Progress Tracking
```text
Finally, let's add persistent tracking using SQLite.
Requirements:
1. Create a simple SQLite database `guitar_app.db` with a table `practice_logs` (columns: date, duration_minutes, focus_area) and a table `quiz_scores` (columns: date, quiz_name, score).
2. On a new "Progress Dashboard" page, allow the user to input their practice time for the day.
3. Use a chart (e.g., `st.bar_chart` or Plotly) to show their practice hours over the last 7 days.
4. Update our "Fretboard Tester" and "Ear Training" modules to automatically save their final scores to the database.

Provide the SQLite setup code and the Dashboard module code.
```
