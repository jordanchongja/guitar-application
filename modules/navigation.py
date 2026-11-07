"""
modules/navigation.py

The app's pages, grouped into the sidebar sections. main.py builds the sidebar from this and the
Home page builds its quick links from it. Each page is (file, title, icon).
"""

SECTIONS = {
    "": [
        ("app_pages/Home.py", "Home", ":material/home:"),
    ],
    "Practice": [
        ("app_pages/0_Practice.py", "Practice", ":material/timer:"),
        ("app_pages/0_Pathway.py", "Pathway", ":material/route:"),
        ("app_pages/9_Practice_Generator.py", "Practice Generator", "🗒️"),
    ],
    "Tools": [
        ("app_pages/1_Scale_Reference.py", "Scale Reference", "🎼"),
        ("app_pages/6_Chord_Dictionary.py", "Chord Dictionary", "📖"),
        ("app_pages/3_Chord_Progressions.py", "Chord Progressions", "🎶"),
        ("app_pages/8_Arpeggio_Visualizer.py", "Arpeggio Visualizer", "🎹"),
        ("app_pages/7_Circle_of_Fifths.py", "Circle of Fifths", "🎡"),
        ("app_pages/12_Custom_Tuning_Builder.py", "Custom Tuning Builder", "🎛️"),
        ("app_pages/14_Metronome.py", "Metronome", "🥁"),
    ],
    "Quizzes": [
        ("app_pages/2_Fretboard_Tester.py", "Fretboard Tester", "🎯"),
        ("app_pages/4_Ear_Training.py", "Ear Training (Intervals)", "👂"),
        ("app_pages/13_Functional_Ear_Trainer.py", "Functional Ear Trainer", "🎯"),
        ("app_pages/10_Sight_Reading_Trainer.py", "Sight-Reading Trainer", "🎼"),
        ("app_pages/11_Daily_Challenge.py", "Daily Challenge", "🔥"),
        ("app_pages/5_Quiz_Scores.py", "Quiz Scores", "📊"),
    ],
}
