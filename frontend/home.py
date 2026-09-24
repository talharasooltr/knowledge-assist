import os
import textwrap
from typing import Any, Dict, List

import requests
import streamlit as st
from requests.auth import HTTPBasicAuth

from styles import apply_styles


# ============================================================
# Configuration
# ============================================================

BASE_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

st.set_page_config(
    page_title="Knowledge Workspace",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# Design System
# ============================================================

apply_styles()


def render_markup(markup: str) -> None:
    cleaned_markup = textwrap.dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(cleaned_markup)
    else:
        st.markdown(
            cleaned_markup,
            unsafe_allow_html=True,
        )


# ============================================================
# State
# ============================================================

def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "logged_in": False,
        "role": None,
        "username": "",
        "auth": None,
        "chat_history": [],
        "page": "Chat",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ============================================================
# Authentication
# ============================================================

def login(
    role: str,
    username: str,
    password: str,
) -> None:
    if not username.strip() or not password:
        st.error("Enter your username and password.")
        return

    try:
        auth = HTTPBasicAuth(
            username.strip(),
            password,
        )

        endpoint = "admin" if role == "Admin" else "user"

        response = requests.get(
            f"{BASE_URL}/{endpoint}/auth/check",
            auth=auth,
            timeout=10,
        )

        if response.status_code == 200:
            st.session_state.update(
                {
                    "logged_in": True,
                    "role": role.lower(),
                    "username": username.strip(),
                    "auth": auth,
                    "page": "Chat",
                    "chat_history": [],
                }
            )

            st.rerun()

        st.error("Invalid username or password.")

    except requests.exceptions.ConnectionError:
        st.error("The backend server is unavailable.")

    except requests.RequestException:
        st.error("Could not complete the sign-in request.")


def logout() -> None:
    st.session_state.clear()
    init_session_state()
    st.rerun()


# ============================================================
# Login
# ============================================================

def render_login() -> None:
    render_markup(
        "<div style='height: 80px'></div>",
    )

    _, center, _ = st.columns([1.2, 1.6, 1.2])

    with center:
        render_markup(
            "<h1 style='text-align:center; color:#111827;'>"
            "Knowledge Workspace"
            "</h1>",
        )

        render_markup(
            "<p style='text-align:center; color:#6b7280;'>"
            "Search and manage your organization's knowledge."
            "</p>",
        )

        render_markup("<div style='height: 20px'></div>")

        role = st.radio(
            "Account",
            ["User", "Admin"],
            horizontal=True,
            key="login_role",
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_username",
        )

        password = st.text_input(
            "Password",
            placeholder="Enter password",
            type="password",
            key="login_password",
        )

        render_markup("<div style='height: 8px'></div>")

        if st.button(
            "Sign in",
            type="primary",
            use_container_width=True,
        ):
            login(
                role,
                username,
                password,
            )


# ============================================================
# Header
# ============================================================

def render_app_header() -> None:
    col1, col2 = st.columns(
        [6, 1],
        vertical_alignment="center",
    )

    with col1:
        render_markup(
            """
            <div class="brand">

                <div class="brand-mark">
                    ◈
                </div>

                <div class="brand-name">
                    Knowledge Workspace
                </div>

            </div>
            """,
        )

        render_markup(
            f"""
            <div class="user-info">
                {st.session_state["username"]}
                ·
                {st.session_state["role"].capitalize()}
            </div>
            """,
        )

    with col2:
        if st.button(
            "Sign out",
            use_container_width=True,
        ):
            logout()


# ============================================================
# Navigation
# ============================================================

def render_navigation() -> None:
    pages = ["Chat", "Documents"]

    if st.session_state["role"] == "admin":
        pages.extend(
            [
                "System",
                "Health",
            ]
        )

    current = st.session_state.get(
        "page",
        "Chat",
    )

    page = st.radio(
        "Navigation",
        pages,
        index=(
            pages.index(current)
            if current in pages
            else 0
        ),
        horizontal=True,
        label_visibility="collapsed",
        key="workspace_navigation",
    )

    st.session_state["page"] = page


# ============================================================
# Chat
# ============================================================

def render_chat() -> None:
    render_markup(
        """
        <div class="chat-header">

            <div class="chat-title">
                Ask your knowledge
            </div>

            <div class="chat-description">
                Ask questions about your indexed documents.
            </div>

        </div>
        """,
    )

    history = st.session_state["chat_history"]

    if not history:
        render_markup(
            """
            <div class="empty-state">

                <div class="empty-mark">
                    ⌕
                </div>

                <div class="empty-title">
                    What would you like to know?
                </div>

                <div class="empty-description">
                    Ask a question about your documents and
                    relevant sources will appear with the answer.
                </div>

            </div>
            """,
        )

    else:
        for message in history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

                sources = message.get(
                    "sources",
                    [],
                )

                if sources:
                    with st.expander(
                        f"{len(sources)} source"
                        f"{'s' if len(sources) != 1 else ''}"
                    ):
                        for source in sources:
                            render_markup(
                                f"""
                                <div class="source-box">

                                    <div class="source-title">
                                        {source.get("title", "Source")}
                                    </div>

                                    <div class="source-text">
                                        {source.get("text", "")}
                                    </div>

                                </div>
                                """,
                            )

    query = st.chat_input(
        "Ask anything about your documents…"
    )

    if query:
        st.session_state["chat_history"].append(
            {
                "role": "user",
                "content": query,
            }
        )

        bot_response = (
            "This is a response generated from your indexed "
            f"vector documents for query: '{query}'."
        )

        sources = [
            {
                "title": "Document_A.pdf · Page 4",
                "text": (
                    "Relevant context snippet extracted from "
                    "vector similarity search."
                ),
            }
        ]

        st.session_state["chat_history"].append(
            {
                "role": "assistant",
                "content": bot_response,
                "sources": sources,
            }
        )

        st.rerun()


# ============================================================
# Documents
# ============================================================

def render_documents() -> None:
    render_markup(
        """
        <div class="chat-header">

            <div class="chat-title">
                Documents
            </div>

            <div class="chat-description">
                Add documents to your knowledge base.
            </div>

        </div>
        """,
    )

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=[
            "pdf",
            "txt",
            "docx",
        ],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.caption(
            f"{len(uploaded_files)} file(s) selected."
        )

        if st.button(
            "Process documents",
            type="primary",
        ):
            st.success(
                f"{len(uploaded_files)} document(s) "
                "processed successfully."
            )


# ============================================================
# System
# ============================================================

def render_system() -> None:
    render_markup(
        """
        <div class="chat-header">

            <div class="chat-title">
                System
            </div>

            <div class="chat-description">
                Manage indexing and system activity.
            </div>

        </div>
        """,
    )

    col1, col2 = st.columns(2)

    with col1:
        render_markup(
            """
            <div class="minimal-card">

                <div class="card-title">
                    Vector database
                </div>

                <div class="card-description">
                    Re-index the knowledge base when documents
                    or embedding configuration changes.
                </div>

            </div>
            """,
        )

        if st.button("Re-index vector store"):
            st.toast(
                "Re-indexing started.",
                icon="⚙️",
            )

    with col2:
        render_markup(
            """
            <div class="minimal-card">

                <div class="card-title">
                    Access activity
                </div>

                <div class="card-description">
                    Recent application activity.
                </div>

            </div>
            """,
        )

        st.code(
            "USER [john_doe] - GET /user/auth/check - 200 OK\n"
            "ADMIN [admin] - POST /admin/reindex - 200 OK",
            language="text",
        )


# ============================================================
# Health
# ============================================================

def render_health() -> None:
    render_markup(
        """
        <div class="chat-header">

            <div class="chat-title">
                System health
            </div>

            <div class="chat-description">
                Current knowledge infrastructure status.
            </div>

        </div>
        """,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Vector Store",
            "1,248 docs",
            "+12 today",
        )

    with col2:
        st.metric(
            "Average Latency",
            "142 ms",
            "-18 ms",
        )

    with col3:
        st.metric(
            "System Uptime",
            "99.98%",
            "Stable",
        )


# ============================================================
# Application
# ============================================================

if not st.session_state["logged_in"]:
    render_login()

else:
    render_app_header()
    render_navigation()

    page = st.session_state["page"]

    if page == "Chat":
        render_chat()

    elif page == "Documents":
        render_documents()

    elif page == "System":
        render_system()

    elif page == "Health":
        render_health()