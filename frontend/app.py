import os
import time

import httpx
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="A11yFix — AI Accessibility Auditor",
    page_icon="♿",
    layout="wide",
)

IMPACT_ICON = {"critical": "🔴", "serious": "🟠", "moderate": "🟡", "minor": "🔵"}
IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}

st.markdown(
    "<h1 style='margin-bottom:0'>♿ A11yFix</h1>"
    "<p style='color:gray;margin-top:0'>AI-powered WCAG 2.1 Accessibility Auditor</p>",
    unsafe_allow_html=True,
)

tab_scan, tab_history = st.tabs(["🔍 New Scan", "📋 Scan History"])


def show_results(data):
    score = data.get("score") or 0
    violations = data.get("violations", [])

    col1, col2, col3 = st.columns(3)
    color = "green" if score >= 80 else ("orange" if score >= 50 else "red")
    col1.markdown(
        f"<h2 style='color:{color};margin:0'>{score:.0f}<span style='font-size:1rem'>/100</span></h2>"
        "<small>Accessibility Score</small>",
        unsafe_allow_html=True,
    )
    col2.metric("Violations", len(violations))
    col3.metric("Unique Rules Violated", len({v["rule_id"] for v in violations}))

    st.divider()

    if not violations:
        st.success("🎉 No violations found!")
        return

    for v in sorted(violations, key=lambda x: IMPACT_ORDER.get(x["impact"], 4)):
        icon = IMPACT_ICON.get(v["impact"], "⚪")
        with st.expander(f"{icon} **[{v['impact'].upper()}]** — {v['description']}", expanded=False):
            st.markdown(f"`Rule:` **{v['rule_id']}** &nbsp;|&nbsp; `Target:` `{v['target']}`", unsafe_allow_html=True)
            if v["wcag_tags"]:
                st.caption(f"WCAG criteria: {v['wcag_tags']}")

            left, right = st.columns(2)
            with left:
                st.markdown("**Offending HTML**")
                st.code(v["html_snippet"] or "(no snippet)", language="html")
            with right:
                st.markdown("**AI-Suggested Fix**")
                st.code(v.get("fix_snippet") or "(not available)", language="html")
                if v.get("fix_explanation"):
                    st.info(f"💡 {v['fix_explanation']}")

    st.divider()

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


with tab_scan:
    with st.form("scan_form"):
        url_input = st.text_input("Website URL", placeholder="https://example.com")
        go = st.form_submit_button("🚀 Scan for Accessibility Issues", type="primary")

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

            bar = st.progress(0, text=f"Scanning {url} …")

            for tick in range(150):
                time.sleep(2)
                try:
                    poll = httpx.get(f"{API}/api/scans/{scan_id}", timeout=10).json()
                except Exception:
                    continue

                status = poll.get("status")
                if status in ("pending", "running"):
                    bar.progress(min(int(tick / 60 * 90), 90), text=f"Scanning {url} …")
                elif status == "completed":
                    bar.progress(100, text="Done!")
                    show_results(poll)
                    break
                elif status == "failed":
                    bar.empty()
                    st.error(f"Scan failed: {poll.get('error_message')}")
                    break
            else:
                bar.empty()
                st.error("Timed out — the site may be too slow or unreachable.")


with tab_history:
    if st.button("🔄 Refresh"):
        st.rerun()

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

            with st.expander(f"{badge} {entry['url']}  —  {score_str}  |  {ts}", expanded=False):
                st.write(f"Violations: {entry['violation_count']}  |  Status: {entry['status']}")
                if st.button("Load results", key=f"load_{entry['id']}"):
                    try:
                        full = httpx.get(f"{API}/api/scans/{entry['id']}", timeout=10).json()
                        show_results(full)
                    except Exception as e:
                        st.error(f"Failed: {e}")
