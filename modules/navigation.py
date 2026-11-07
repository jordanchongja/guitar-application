"""
modules/navigation.py

The app's pages, grouped into the sidebar sections. main.py builds the sidebar from this and the
Home page builds its quick links from it. Each page is (file, title, icon).
"""

SECTIONS = {
    "": [
        ("pages/Home.py", "Home", ":material/home:"),
    ],
    "Practice": [
        ("pages/0_Practice.py", "Practice", ":material/timer:"),
        ("pages/0_Pathway.py", "Pathway", ":material/route:"),
        ("pages/9_Practice_Generator.py", "Practice Generator", "🗒️"),
    ],
    "Tools": [
        ("pages/1_Scale_Reference.py", "Scale Reference", "🎼"),
        ("pages/6_Chord_Dictionary.py", "Chord Dictionary", "📖"),
        ("pages/3_Chord_Progressions.py", "Chord Progressions", "🎶"),
        ("pages/8_Arpeggio_Visualizer.py", "Arpeggio Visualizer", "🎹"),
        ("pages/7_Circle_of_Fifths.py", "Circle of Fifths", "🎡"),
        ("pages/12_Custom_Tuning_Builder.py", "Custom Tuning Builder", "🎛️"),
        ("pages/14_Metronome.py", "Metronome", "🥁"),
    ],
    "Quizzes": [
        ("pages/2_Fretboard_Tester.py", "Fretboard Tester", "🎯"),
        ("pages/4_Ear_Training.py", "Ear Training (Intervals)", "👂"),
        ("pages/13_Functional_Ear_Trainer.py", "Functional Ear Trainer", "🎯"),
        ("pages/10_Sight_Reading_Trainer.py", "Sight-Reading Trainer", "🎼"),
        ("pages/11_Daily_Challenge.py", "Daily Challenge", "🔥"),
        ("pages/5_Quiz_Scores.py", "Quiz Scores", "📊"),
    ],
}
