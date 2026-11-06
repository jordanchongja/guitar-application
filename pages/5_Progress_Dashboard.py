"""
pages/5_Progress_Dashboard.py

Read-only stats. Practice time arrives here from the Practice page.

- Bar chart of practice minutes over the last 7 days.
- Table of recent quiz scores saved from Fretboard Tester / Ear Training.
"""

import streamlit as st

from modules.database import get_practice_last_n_days, get_practice_summary, get_recent_quiz_scores
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Progress Dashboard", page_icon="📊", layout="wide")
render_sidebar_settings()

st.title("📊 Progress Dashboard")

st.caption("Practice time is added automatically when you save a session. To add one you forgot, "
           "use the Practice page.")

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
