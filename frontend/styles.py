import streamlit as st


CSS = r"""
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
    );

    :root {
        --bg: #f7f8fa;
        --surface: #ffffff;
        --border: #e4e7eb;
        --text: #111827;
        --muted: #6b7280;
        --subtle: #9ca3af;
        --accent: #111827;
        --accent-foreground: #ffffff;
    }


    /* ========================================================
       Base
       ======================================================== */

    html,
    body,
    [class*="css"] {
        font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif !important;
    }

    .stApp {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main,
    .main .block-container {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    .main .block-container {
        max-width: 1000px !important;
        padding: 1.25rem 1.5rem 6rem !important;
    }

    #MainMenu,
    footer,
    header[data-testid="stHeader"] {
        visibility: hidden !important;
        height: 0 !important;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    [data-testid="collapsedControl"] {
        display: none !important;
    }


    /* ========================================================
       Global text
       ======================================================== */

    p,
    span,
    label,
    li,
    td,
    th,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: var(--text);
    }

    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span {
        color: var(--text) !important;
    }


    /* ========================================================
       App Header
       ======================================================== */

    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 0.25rem 0 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.9rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.65rem;
    }

    .brand-mark {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: var(--accent);
        color: var(--accent-foreground) !important;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 13px;
        font-weight: 600;
    }

    .brand-name {
        color: #111827 !important;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: -0.01em;
    }

    .user-info {
        color: #6b7280 !important;
        font-size: 0.72rem;
    }


    /* ========================================================
       Navigation
       ======================================================== */

    .nav-label {
        color: #9ca3af !important;
        font-size: 0.68rem;
        margin: 0.8rem 0 0.25rem;
    }

    [data-testid="stRadio"] {
        margin-bottom: 0.5rem;
    }

    [data-testid="stRadio"] > div {
        gap: 0.2rem !important;
    }

    [data-testid="stRadio"] [role="radiogroup"] {
        gap: 0.2rem !important;
    }

    [data-testid="stRadio"] label {
        min-height: 30px !important;
        padding: 0.15rem 0.7rem !important;

        border-radius: 7px !important;

        color: #6b7280 !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stRadio"] label:hover {
        background: #eef0f3 !important;
        color: #111827 !important;
    }

    [data-testid="stRadio"] label p {
        color: inherit !important;
        font-size: 0.72rem !important;
    }


    /* ========================================================
       Chat Workspace
       ======================================================== */

    .chat-header {
        padding: 1.8rem 0 1rem;
    }

    .chat-title {
        color: #111827 !important;
        font-size: 1.25rem;
        font-weight: 600;
        letter-spacing: -0.025em;
        margin-bottom: 0.25rem;
    }

    .chat-description {
        color: #6b7280 !important;
        font-size: 0.78rem;
    }

    .empty-state {
        min-height: 48vh;

        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;

        text-align: center;
    }

    .empty-mark {
        width: 42px;
        height: 42px;

        display: flex;
        align-items: center;
        justify-content: center;

        background: #eef0f3;
        border-radius: 12px;

        color: #111827 !important;
        font-size: 17px;

        margin-bottom: 0.9rem;
    }

    .empty-title {
        color: #111827 !important;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .empty-description {
        max-width: 360px;

        color: #6b7280 !important;
        font-size: 0.76rem;
        line-height: 1.5;
    }


    /* ========================================================
       Chat messages
       ======================================================== */

    .stChatMessage,
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        color: #111827 !important;
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span {
        color: #111827 !important;
    }


    /* ========================================================
       Chat input
       ======================================================== */

    [data-testid="stChatInput"] {
        background: transparent !important;
        border: 0 !important;
    }

    [data-testid="stChatInput"] > div {
        background: #ffffff !important;

        border: 1px solid #dfe3e8 !important;
        border-radius: 12px !important;

        box-shadow:
            0 3px 12px rgba(17, 24, 39, 0.05) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #111827 !important;

        border: 0 !important;
        border-radius: 12px !important;

        font-family: Inter, sans-serif !important;
        font-size: 0.8rem !important;

        box-shadow: none !important;
        caret-color: #111827 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #9ca3af !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        background: #ffffff !important;
        color: #111827 !important;
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    [data-testid="stChatInput"] button {
        color: #111827 !important;
        background: transparent !important;
        border: 0 !important;
    }


    /* ========================================================
       Buttons
       ======================================================== */

    .stButton > button,
    .stDownloadButton > button {
        min-height: 36px !important;

        background: #ffffff !important;
        color: #111827 !important;

        border: 1px solid #dfe3e8 !important;
        border-radius: 8px !important;

        font-size: 0.76rem !important;
        font-weight: 500 !important;

        box-shadow: none !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: #f3f4f6 !important;
        color: #111827 !important;
        border-color: #c9ced6 !important;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--accent) !important;
        color: var(--accent-foreground) !important;
        border-color: var(--accent) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: #1f2937 !important;
        color: var(--accent-foreground) !important;
    }

    .stButton > button *,
    .stDownloadButton > button * {
        color: inherit !important;
    }


    /* ========================================================
       Inputs
       ======================================================== */

    .stTextInput input,
    .stTextArea textarea {
        background: #ffffff !important;
        color: #111827 !important;

        border: 1px solid #dfe3e8 !important;
        border-radius: 8px !important;

        font-size: 0.8rem !important;

        box-shadow: none !important;
        caret-color: #111827 !important;
    }

    .stTextInput input {
        min-height: 38px !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9ca3af !important;
        opacity: 1 !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        background: #ffffff !important;
        color: #111827 !important;
        border-color: #9ca3af !important;
        box-shadow:
            0 0 0 2px rgba(17, 24, 39, 0.05) !important;
    }

    button[aria-label="Show password"],
    button[aria-label="Hide password"] {
        color: var(--accent-foreground) !important;
    }

    button[aria-label="Show password"] [data-testid="stIconMaterial"],
    button[aria-label="Hide password"] [data-testid="stIconMaterial"] {
        color: var(--accent-foreground) !important;
        fill: var(--accent-foreground) !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    .stTextInput label,
    .stTextArea label {
        color: #374151 !important;
        font-size: 0.74rem !important;
    }


    /* ========================================================
       Source
       ======================================================== */

    .source-box {
        background: #f8f9fb;
        border: 1px solid #e4e7eb;
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        margin-top: 0.5rem;
    }

    .source-title {
        color: #111827 !important;
        font-size: 0.7rem;
        font-weight: 600;
    }

    .source-text {
        color: #6b7280 !important;
        font-size: 0.68rem;
        line-height: 1.45;
        margin-top: 0.2rem;
    }


    /* ========================================================
       Cards
       ======================================================== */

    .minimal-card {
        background: #ffffff;
        border: 1px solid #e4e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    .card-title {
        color: #111827 !important;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .card-description {
        color: #6b7280 !important;
        font-size: 0.72rem;
        line-height: 1.45;
        margin-top: 0.25rem;
    }


    /* ========================================================
       File uploader
       ======================================================== */

    .stFileUploader section {
        background: #ffffff !important;
        border: 1px dashed #cfd4dc !important;
        border-radius: 9px !important;
    }

    [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] * {
        color: var(--accent-foreground) !important;
        -webkit-text-fill-color: var(--accent-foreground) !important;
        opacity: 1 !important;
    }


    /* ========================================================
       Metrics
       ======================================================== */

    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e4e7eb !important;
        border-radius: 9px !important;
        padding: 0.8rem !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 0.68rem !important;
    }

    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-size: 1.05rem !important;
    }


    /* ========================================================
       Expander
       ======================================================== */

    .stExpander {
        background: #ffffff !important;
        border: 1px solid #e4e7eb !important;
        border-radius: 8px !important;
    }

    .stExpander summary,
    .stExpander summary p {
        color: #374151 !important;
    }


    /* ========================================================
       Login
       ======================================================== */

    .login-container {
        max-width: 390px;
        margin: 13vh auto 0;
    }

    .login-brand {
        text-align: center;
        margin-bottom: 2rem;
    }

    .login-mark {
        width: 46px;
        height: 46px;

        margin: 0 auto 1rem;

        display: flex;
        align-items: center;
        justify-content: center;

        background: var(--accent);
        border-radius: 13px;

        color: var(--accent-foreground) !important;
        font-size: 16px;
        font-weight: 600;
    }

    .login-title {
        color: #111827 !important;
        font-size: 1.3rem;
        font-weight: 600;
        letter-spacing: -0.025em;
    }

    .login-description {
        color: #6b7280 !important;
        font-size: 0.77rem;
        margin-top: 0.35rem;
    }


    /* ========================================================
       Divider
       ======================================================== */

    hr {
        border-color: #e4e7eb !important;
    }


    /* ========================================================
       Alerts
       ======================================================== */

    [data-testid="stAlert"] {
        border-radius: 8px !important;
    }
    </style>

"""


def apply_styles() -> None:
    st.markdown(
        CSS,
        unsafe_allow_html=True,
    )
