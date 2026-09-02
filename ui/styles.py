"""Custom CSS - one place, responsive for desktop and mobile."""
import streamlit as st


def load_css():
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.4rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
            color: #1f2937;
        }
        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #1f77b4;
            border-radius: 10px;
            padding: 0.9rem 1rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.6rem 1rem;
            border-radius: 8px 8px 0 0;
        }
        @media (max-width: 640px) {
            .main-header { font-size: 1.6rem; }
            div[data-testid="stMetricValue"] { font-size: 1.1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
