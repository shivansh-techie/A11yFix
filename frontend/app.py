import os
import time

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="A11yFix — AI Accessibility Auditor",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* hide streamlit status widget (cycling spinner) */
[data-testid="stStatusWidget"] { visibility: hidden; }

/* clean top bar */
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; }

/* hero header */
.a11y-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.a11y-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #818cf8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.a11y-header p { margin: 0; color: #94a3b8; font-size: 0.9rem; }
.a11y-icon { font-size: 2.5rem; }

/* score cards */
.score-card {
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    border: 1px solid #334155;
    background: #0f172a;
}
.score-card .val { font-size: 2.2rem; font-weight: 800; }
.score-card .lbl { font-size: 0.75rem; color: #94a3b8; margin-top: 2px; }
.score-green .val { color: #22c55e; }
.score-orange .val { color: #f59e0b; }
.score-red .val { color: #ef4444; }
.stat-val { font-size: 2rem; font-weight: 700; color: #e2e8f0; }
.stat-lbl { font-size: 0.75rem; color: #94a3b8; }

/* violation card */
.vcard {
    border-radius: 8px;
    border-left: 4px solid #475569;
    background: #1e293b;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
}
.vcard.critical { border-left-color: #ef4444; }
.vcard.serious  { border-left-color: #f97316; }
.vcard.moderate { border-left-color: #eab308; }
.vcard.minor    { border-left-color: #3b82f6; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #fff;
    margin-right: 6px;
}
.badge.critical { background: #ef4444; }
.badge.serious  { background: #f97316; }
.badge.moderate { background: #eab308; color: #000; }
.badge.minor    { background: #3b82f6; }

/* divider */
.styled-divider { border: none; border-top: 1px solid #1e293b; margin: 1rem 0; }

/* snippet boxes */
.snippet-wrap { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 0.6rem; }
.snippet-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.fix-wrap { background: #0c2a1a; border: 1px solid #166534; border-radius: 6px; padding: 0.6rem; }
</style>
""", unsafe_allow_html=True)

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="a11y-header">
    <div class="a11y-icon">🛡️</div>
    <div>
        <h1>A11yFix</h1>
        <p>AI-powered WCAG 2.1 Accessibility Auditor · Powered by axe-core + Claude</p>
    </div>
</div>
""", unsafe_allow_html=True)

if "history_selected" not in st.session_state:
    st.session_state.history_selected = None

tab_scan, tab_history = st.tabs(["🔍 New Scan", "📋 Scan History"])


# ---------------------------------------------------------------------------
# Results renderer
# ---------------------------------------------------------------------------

def show_results(data):
    score = data.get("score") or 0
    violations = data.get("violations", [])
    score_class = "score-green" if score >= 80 else ("score-orange" if score >= 50 else "score-red")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="score-card {score_class}">
            <div class="val">{score:.0f}<span style="font-size:1rem;font-weight:400">/100</span></div>
            <div class="lbl">Accessibility Score</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="score-card">
            <div class="stat-val">{len(violations)}</div>
            <div class="stat-lbl">Total Violations</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        unique = len({v["rule_id"] for v in violations})
        st.markdown(f"""
        <div class="score-card">
            <div class="stat-val">{unique}</div>
            <div class="stat-lbl">Unique Rules Violated</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)

    if not violations:
        st.success("🎉 No WCAG violations found on this page!")
        return

    for v in sorted(violations, key=lambda x: IMPACT_ORDER.get(x["impact"], 4)):
        imp = v["impact"]
        with st.expander(
            f"{'🔴' if imp=='critical' else '🟠' if imp=='serious' else '🟡' if imp=='moderate' else '🔵'} "
            f"[{imp.upper()}] — {v['description']}",
            expanded=False,
        ):
            st.markdown(
                f"<code>Rule:</code> <b>{v['rule_id']}</b> &nbsp;|&nbsp; "
                f"<code>Target:</code> <code>{v['target']}</code>",
                unsafe_allow_html=True,
            )
            if v["wcag_tags"]:
                st.caption(f"WCAG: {v['wcag_tags']}")

            left, right = st.columns(2)
            with left:
                st.markdown('<div class="snippet-label">Offending HTML</div>', unsafe_allow_html=True)
                st.code(v["html_snippet"] or "(no snippet)", language="html")
            with right:
                st.markdown('<div class="snippet-label">AI-Suggested Fix</div>', unsafe_allow_html=True)
                st.code(v.get("fix_snippet") or "(not available)", language="html")
                if v.get("fix_explanation"):
                    st.info(f"💡 {v['fix_explanation']}")

    st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)

    try:
        pdf = httpx.get(f"{API}/api/scans/{data['id']}/pdf", timeout=30)
        pdf.raise_for_status()
        st.download_button(
            "📄 Download PDF Report",
            data=pdf.content,
            file_name=f"a11yfix-report-{data['id']}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.warning(f"PDF export unavailable: {e}")


# ---------------------------------------------------------------------------
# New Scan tab
# ---------------------------------------------------------------------------

with tab_scan:
    with st.form("scan_form"):
        url_input = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            label_visibility="collapsed",
        )
        go = st.form_submit_button("🚀 Scan for Accessibility Issues", type="primary", use_container_width=True)

    if go:
        url = url_input.strip()
        if not url:
            st.warning("Please enter a URL.")
        elif not url.startswith(("http://", "https://")):
            st.error("URL must start with http:// or https://")
        else:
            try:
                r = httpx.post(f"{API}/api/scans", json={"url": url}, timeout=10)
                r.raise_for_status()
                scan_id = r.json()["scan_id"]
            except Exception as e:
                st.error(f"Could not start scan: {e}")
                st.stop()

            bar = st.progress(0, text=f"🔍 Scanning {url} …")

            for tick in range(150):
                time.sleep(2)
                try:
                    poll = httpx.get(f"{API}/api/scans/{scan_id}", timeout=10).json()
                except Exception:
                    continue

                status = poll.get("status")
                if status in ("pending", "running"):
                    bar.progress(min(int(tick / 60 * 90), 90), text=f"🔍 Scanning {url} …")
                elif status == "completed":
                    bar.progress(100, text="✅ Done!")
                    show_results(poll)
                    break
                elif status == "failed":
                    bar.empty()
                    st.error(f"Scan failed: {poll.get('error_message')}")
                    break
            else:
                bar.empty()
                st.error("Timed out — the site may be too slow or unreachable.")


# ---------------------------------------------------------------------------
# History tab
# ---------------------------------------------------------------------------

with tab_history:
    col_ref, col_clear = st.columns([1, 1])
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.history_selected = None
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
            try:
                all_scans = httpx.get(f"{API}/api/scans", timeout=10).json()
                for s in all_scans:
                    httpx.delete(f"{API}/api/scans/{s['id']}", timeout=10)
                st.session_state.history_selected = None
                st.success("History cleared.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

    st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)

    try:
        history = httpx.get(f"{API}/api/scans", timeout=10).json()
    except Exception as e:
        st.error(f"Cannot reach API: {e}")
        history = []

    if not history:
        st.info("No scans yet — run one from the New Scan tab.")
    else:
        for entry in history:
            score = entry.get("score")
            score_str = f"{score:.0f}/100" if score is not None else "—"
            ts = (entry.get("timestamp") or "")[:19].replace("T", " ")
            badge = {"completed": "✅", "failed": "❌", "running": "⏳", "pending": "🕐"}.get(entry["status"], "❓")

            c1, c2, c3 = st.columns([7, 1, 1])
            with c1:
                st.markdown(
                    f"{badge} **{entry['url']}** &nbsp; "
                    f"<span style='color:#64748b;font-size:0.85rem'>{score_str} · {entry['violation_count']} violations · {ts}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("View", key=f"view_{entry['id']}", use_container_width=True):
                    st.session_state.history_selected = entry["id"]
            with c3:
                if st.button("🗑️", key=f"del_{entry['id']}", use_container_width=True, help="Delete this scan"):
                    try:
                        httpx.delete(f"{API}/api/scans/{entry['id']}", timeout=10)
                        if st.session_state.history_selected == entry["id"]:
                            st.session_state.history_selected = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
            st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)

        if st.session_state.history_selected:
            try:
                full = httpx.get(f"{API}/api/scans/{st.session_state.history_selected}", timeout=10).json()
                st.markdown(f"### 📊 Results — {full['url']}")
                show_results(full)
            except Exception as e:
                st.error(f"Failed to load results: {e}")
