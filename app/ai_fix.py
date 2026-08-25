import json
import os
import re

from app.rule_fixes import lookup_fix


def get_fix(rule_id: str, description: str, html_snippet: str, wcag_tags: list) -> dict:
    # check pre-written dictionary first — covers ~90% of common rules without needing an API key
    cached = lookup_fix(rule_id)
    if cached:
        return cached

    # if there's an API key, ask Claude for rules we don't have a template for
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        return _ask_claude(api_key, rule_id, description, html_snippet, wcag_tags)

    return {
        "fixed_html": html_snippet,
        "explanation": f"No built-in fix for '{rule_id}'. Add ANTHROPIC_API_KEY to .env for AI-generated fixes.",
    }


def _ask_claude(api_key, rule_id, description, html_snippet, wcag_tags):
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=(
            "You are a web accessibility expert. Given a WCAG violation and its HTML, "
            'return only a JSON object: {"fixed_html": "...", "explanation": "one sentence"}. '
            "No markdown, no extra text."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"Rule: {rule_id}\n"
                f"Description: {description}\n"
                f"WCAG: {', '.join(wcag_tags) or 'n/a'}\n\n"
                f"Offending HTML:\n{html_snippet}"
            ),
        }],
    )

    text = resp.content[0].text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

    return {"fixed_html": html_snippet, "explanation": "Could not parse Claude's response."}
