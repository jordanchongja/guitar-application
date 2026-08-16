"""
pages/5_Progress_Dashboard.py

Task 5: Database & Progress Tracking.

- Log practice time for the day.
- Bar chart of practice minutes over the last 7 days.
- Table of recent quiz scores saved from Fretboard Tester / Ear Training.
"""

import datetime as dt

import streamlit as st

from modules.database import get_practice_last_n_days, get_practice_summary, get_recent_quiz_scores, log_practice
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Progress Dashboard", page_icon="📊", layout="wide")
render_sidebar_settings()

st.title("📊 Progress Dashboard")

st.subheader("Log Today's Practice")
with st.form("log_practice_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        practice_date = st.date_input("Date", value=dt.date.today())
    with c2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=600, value=30, step=5)
    with c3:
        focus_area = st.selectbox(
            "Focus Area",
            options=["Scales", "Chords", "Fretboard Knowledge", "Ear Training", "Repertoire", "Technique", "Other"],
        )
    submitted = st.form_submit_button("➕ Log Practice")
    if submitted:
        log_practice(int(duration), focus_area, date=practice_date.isoformat())
        st.success(f"Logged {duration} minutes of {focus_area} on {practice_date.isoformat()}.")

st.divider()

summary = get_practice_summary()
sum_col1, sum_col2 = st.columns(2)
sum_col1.metric("Total Practice Time", f"{summary['total_minutes']} min")
sum_col2.metric("Days Practiced", summary["days_practiced"])

st.subheader("Practice Minutes — Last 7 Days")
practice_df = get_practice_last_n_days(7)
st.bar_chart(practice_df["minutes"])

st.subheader("Recent Quiz Scores")
scores_df = get_recent_quiz_scores(limit=15)
if scores_df.empty:
    st.info("No quiz scores saved yet. Play the Fretboard Tester or Ear Training quiz and click "
             "**Finish & Save Score**.")
else:
    scores_df["accuracy"] = (scores_df["score"] / scores_df["total"] * 100).round(1).astype(str) + "%"
    st.dataframe(scores_df, width='stretch', hide_index=True)
