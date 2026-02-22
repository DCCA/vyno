from __future__ import annotations

from datetime import datetime, timedelta
import random


def _seed() -> None:
    random.seed(42)


def _status_chip(label: str, tone: str = "neutral") -> str:
    colors = {
        "good": "#0f766e",
        "warn": "#b45309",
        "bad": "#b91c1c",
        "neutral": "#334155",
    }
    bg = colors.get(tone, colors["neutral"])
    return (
        f"<span style='display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;"
        f"font-size:0.78rem;font-weight:600;color:white;background:{bg};'>{label}</span>"
    )


def _inject_css(st) -> None:
    st.markdown(
        """
<style>
:root {
  --bg-grad-1: #f8fafc;
  --bg-grad-2: #eef2ff;
  --ink: #0f172a;
  --muted: #334155;
  --card: #ffffff;
  --line: #e2e8f0;
  --brand: #0f766e;
  --brand-soft: #ccfbf1;
}
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
section[data-testid="stSidebar"] * {
  color: #e2e8f0 !important;
}
.block-container {
  background: radial-gradient(circle at 10% 10%, var(--bg-grad-2), var(--bg-grad-1) 50%);
  color: var(--ink);
  max-width: 1200px;
  padding-top: 1.4rem;
}
div[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.75rem 0.9rem;
}
.ui-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.7rem;
}
.ui-title {
  font-size: 1.9rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
}
.ui-sub {
  color: var(--muted);
  margin: 0.2rem 0 0 0;
}
.ui-kicker {
  display: inline-block;
  background: var(--brand-soft);
  color: var(--brand);
  padding: 0.22rem 0.55rem;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
hr {
  border: 0;
  border-top: 1px solid var(--line);
}
</style>
""",
        unsafe_allow_html=True,
    )


def _mock_runs():
    now = datetime.utcnow()
    rows = []
    statuses = ["success", "partial", "success", "failed", "success", "partial", "success"]
    for i, status in enumerate(statuses, start=1):
        ts = now - timedelta(hours=i * 3)
        rows.append(
            {
                "run_id": f"run{9000+i}",
                "status": status,
                "started_at": ts.isoformat(timespec="seconds") + "Z",
                "items": random.randint(8, 42),
                "source_errors": 0 if status == "success" else random.randint(1, 3),
                "summary_errors": 0 if status == "success" else random.randint(0, 2),
            }
        )
    return rows


def _mock_sources():
    return {
        "rss": [
            "https://openai.com/news/rss.xml",
            "https://blog.google/technology/ai/rss/",
            "https://feeds.arstechnica.com/arstechnica/index",
        ],
        "youtube_channel": [
            "UCXUPKJO5MZQN11PqgIvyuvQ",
            "UCMLtBahI5DMrt0NPvDSoIRQ",
        ],
        "github_org": ["openai", "vercel-labs"],
        "github_repo": ["openai/openai-cookbook"],
    }


def _mock_feedback():
    return [
        {"run_id": "run9001", "item_id": "a1", "rating": 5, "label": "high-signal", "comment": "great mix"},
        {"run_id": "run9002", "item_id": "a2", "rating": 3, "label": "noisy", "comment": "too long video desc"},
        {"run_id": "run9003", "item_id": "a3", "rating": 4, "label": "useful", "comment": "good github updates"},
    ]


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("streamlit is required. Install with: pip install streamlit") from exc

    _seed()
    st.set_page_config(page_title="Admin UX Prototype", page_icon="🧭", layout="wide")
    _inject_css(st)

    with st.sidebar:
        st.markdown("### Admin Console")
        st.caption("Prototype mode - no backend writes")
        page = st.radio(
            "Navigate",
            ["Overview", "Sources", "Runs", "Logs", "Outputs", "Feedback", "Bot"],
            index=0,
        )
        st.markdown("---")
        st.write("Design toggles")
        compact = st.toggle("Compact rows", value=True)
        dark_logs = st.toggle("Dense logs view", value=True)
        _ = compact, dark_logs

    st.markdown("<span class='ui-kicker'>Prototype</span>", unsafe_allow_html=True)
    st.markdown("<h1 class='ui-title'>AI Digest Admin UX Preview</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='ui-sub'>Use this to review information architecture and task flow before backend coupling.</p>",
        unsafe_allow_html=True,
    )

    runs = _mock_runs()
    sources = _mock_sources()
    feedback = _mock_feedback()

    if page == "Overview":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bot", "Running", "healthy")
        c2.metric("Latest Run", runs[0]["status"], runs[0]["run_id"])
        c3.metric("Sources", sum(len(v) for v in sources.values()))
        c4.metric("Avg Rating", f"{sum(x['rating'] for x in feedback)/len(feedback):.1f}/5")

        st.markdown("### Action Center")
        a1, a2, a3 = st.columns([1, 1, 3])
        a1.button("Run now", type="primary")
        a2.button("Add source")
        a3.text_input("Quick search (run_id/source/item)", placeholder="run9002, vercel-labs, benchmark")

        st.markdown("### Recent Runs")
        for r in runs[:5]:
            tone = "good" if r["status"] == "success" else "warn" if r["status"] == "partial" else "bad"
            st.markdown(
                (
                    "<div class='ui-card'>"
                    f"<b>{r['run_id']}</b> { _status_chip(r['status'], tone)}<br/>"
                    f"<span style='color:#475569'>Started: {r['started_at']} · Items: {r['items']} · "
                    f"Source errors: {r['source_errors']} · Summary errors: {r['summary_errors']}</span>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    elif page == "Sources":
        st.markdown("### Source Management")
        c1, c2 = st.columns([2, 1])
        with c1:
            with st.form("add_source_form"):
                t = st.selectbox("Source Type", ["rss", "youtube_channel", "youtube_query", "github_org", "github_repo", "github_topic", "github_query"])
                v = st.text_input("Source Value", placeholder="https://github.com/vercel-labs")
                confirm = st.checkbox("I reviewed canonical value preview")
                st.caption("Canonical preview: `vercel-labs` for github_org URLs")
                st.form_submit_button("Add Source", disabled=not confirm)
        with c2:
            st.markdown("<div class='ui-card'><b>Guardrails</b><br/>"
                        "• Duplicate detection<br/>"
                        "• Type-specific validation<br/>"
                        "• Overlay-only mutations</div>", unsafe_allow_html=True)

        st.markdown("### Effective Sources")
        tabs = st.tabs(list(sources.keys()))
        for tab, key in zip(tabs, sources.keys()):
            with tab:
                st.dataframe({"value": sources[key]}, width="stretch")

    elif page == "Runs":
        st.markdown("### Runs")
        f1, f2, f3 = st.columns([1, 1, 2])
        status_filter = f1.multiselect("Status", ["success", "partial", "failed"], default=["success", "partial", "failed"])
        _ = f2.date_input("From")
        f3.text_input("run_id contains", value="")

        filtered = [r for r in runs if r["status"] in status_filter]
        st.dataframe(filtered, width="stretch", hide_index=True)
        with st.expander("Run details preview"):
            st.code("""run_id: run9002\nstage: score\nsource_errors: 1\nsummary_errors: 1""")

    elif page == "Logs":
        st.markdown("### Logs")
        c1, c2, c3 = st.columns(3)
        c1.text_input("run_id", value="run9002")
        c2.text_input("stage", value="score")
        c3.selectbox("level", ["ALL", "INFO", "ERROR"], index=2)
        st.code("""
{\"ts\":\"2026-02-22T09:10:21Z\",\"run_id\":\"run9002\",\"stage\":\"score\",\"level\":\"ERROR\",\"message\":\"Agent scoring timeout\"}
{\"ts\":\"2026-02-22T09:10:21Z\",\"run_id\":\"run9002\",\"stage\":\"score\",\"level\":\"INFO\",\"message\":\"Rules fallback applied\"}
""")

    elif page == "Outputs":
        st.markdown("### Outputs")
        l, r = st.columns(2)
        with l:
            st.markdown("#### Telegram")
            st.code(
                """AI Digest - 2026-02-22\n\nTop Highlights\n1. OpenAI Cookbook release ...\n\nGitHub\n- openai/openai-cookbook ..."""
            )
        with r:
            st.markdown("#### Obsidian")
            st.code(
                """---\ndate: 2026-02-22\nrun_id: run9001\n---\n\n## Top Highlights\n1. ...\n\n## GitHub\n- ..."""
            )

    elif page == "Feedback":
        st.markdown("### Feedback")
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg rating", "4.0")
        c2.metric("Low-signal flags", "1", "-2 vs last week")
        c3.metric("Feedback count", str(len(feedback)))

        with st.form("feedback_form"):
            st.selectbox("Run", [x["run_id"] for x in feedback])
            st.text_input("Item ID", value="a2")
            st.slider("Rating", min_value=1, max_value=5, value=4)
            st.selectbox("Label", ["high-signal", "useful", "noisy", "irrelevant"])
            st.text_area("Comment", value="Could be shorter in Telegram")
            st.form_submit_button("Save Feedback")

        st.dataframe(feedback, width="stretch", hide_index=True)

    elif page == "Bot":
        st.markdown("### Bot Lifecycle")
        st.markdown(
            (
                "<div class='ui-card'><b>Status:</b> "
                + _status_chip("running", "good")
                + "<br/><span style='color:#475569'>pid: 48211 · started: 2026-02-22T09:12:01Z</span></div>"
            ),
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.button("Start")
        c2.button("Stop")
        c3.button("Restart")
        st.warning("UI prototype: actions are disabled in preview mode.")


if __name__ == "__main__":
    main()
