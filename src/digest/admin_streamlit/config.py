from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class StreamlitAdminConfig:
    sources_path: str
    profile_path: str
    db_path: str
    overlay_path: str
    run_lock_path: str
    bot_pid_path: str
    bot_log_path: str
    admin_user: str
    admin_password: str


def load_streamlit_admin_config() -> StreamlitAdminConfig:
    return StreamlitAdminConfig(
        sources_path=os.getenv("ADMIN_STREAMLIT_SOURCES", "config/sources.yaml"),
        profile_path=os.getenv("ADMIN_STREAMLIT_PROFILE", "config/profile.yaml"),
        db_path=os.getenv("ADMIN_STREAMLIT_DB", "digest.db"),
        overlay_path=os.getenv("ADMIN_STREAMLIT_OVERLAY", "data/sources.local.yaml"),
        run_lock_path=os.getenv("ADMIN_STREAMLIT_RUN_LOCK", ".runtime/run.lock"),
        bot_pid_path=os.getenv("ADMIN_STREAMLIT_BOT_PID", ".runtime/bot.pid"),
        bot_log_path=os.getenv("ADMIN_STREAMLIT_BOT_LOG", ".runtime/bot.out"),
        admin_user=os.getenv("ADMIN_PANEL_USER", "").strip(),
        admin_password=os.getenv("ADMIN_PANEL_PASSWORD", "").strip(),
    )
