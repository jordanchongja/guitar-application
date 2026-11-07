"""
pages/5_Quiz_Scores.py

Recent scores saved from the quizzes. Practice minutes live on the Practice page.
"""

import streamlit as st

from modules.database import get_recent_quiz_scores
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Quiz Scores", page_icon="📊", layout="wide")
render_sidebar_settings()

st.title("📊 Quiz Scores")

scores_df = get_recent_quiz_scores(limit=15)
if scores_df.empty:
    st.info("No quiz scores saved yet. Play the Fretboard Tester or Ear Training quiz and click "
             "**Finish & Save Score**.")
else:
    scores_df["accuracy"] = (scores_df["score"] / scores_df["total"] * 100).round(1).astype(str) + "%"
    st.dataframe(scores_df, width='stretch', hide_index=True)
