"""
main.py

Entry point for the Guitar Learning App: builds the sidebar, then runs whichever page is open. The sections and pages are listed in modules/navigation.py.
"""

import streamlit as st

from modules.navigation import SECTIONS

st.navigation(
    {section: [st.Page(path, title=title, icon=icon, default=path == "pages/Home.py")
               for path, title, icon in pages]
     for section, pages in SECTIONS.items()},
    expanded=True,
).run()
