# Pre-written fixes for common axe-core violations.
# Covers most of what you'll see on real sites — anything not here falls back to Claude (if key is set).
#
# format: rule_id -> (corrected_snippet, one-line explanation)

RULE_FIXES = {
    "button-name": (
        '<button type="button" aria-label="Describe the action">...</button>',
        "Add an aria-label (or visible text) so screen readers can announce what the button does.",
    ),
    "color-contrast": (
        "<!-- Increase text darkness or background lightness until contrast ratio hits 4.5:1.\n"
        "     Tool: https://webaim.org/resources/contrastchecker/ -->",
        "Text and background must have at least 4.5:1 contrast ratio (WCAG 1.4.3).",
    ),
    "image-alt": (
        '<img src="..." alt="Short description of what the image shows">',
        "Every <img> needs an alt attribute — use empty alt=\"\" only for decorative images.",
    ),
    "input-image-alt": (
        '<input type="image" src="submit.png" alt="Submit the form">',
        "Image inputs acting as buttons need alt text describing the action.",
    ),
    "label": (
        '<label for="email">Email address</label>\n<input id="email" type="email">',
        "Each form input needs a <label> linked via for/id, or an aria-label.",
    ),
    "link-name": (
        '<a href="/about">About us</a>\n<!-- icon-only: -->\n<a href="..." aria-label="Visit our Facebook page"><img src="fb.svg" alt=""></a>',
        "Links need descriptive text — 'click here' tells screen readers nothing; use aria-label for icon links.",
    ),
    "heading-order": (
        "<!-- Headings must go in order: h1 → h2 → h3. Don't skip levels. -->",
        "Skipping heading levels breaks screen-reader navigation (WCAG 1.3.1).",
    ),
    "landmark-one-main": (
        '<main id="main-content">\n  <!-- page content here -->\n</main>',
        "Every page needs exactly one <main> so assistive tech can jump straight to content.",
    ),
    "region": (
        "<!-- Wrap all content in landmark regions: <header>, <nav>, <main>, <footer>.\n"
        "     Content floating outside these is inaccessible via landmark navigation. -->",
        "All visible content must be inside a landmark element.",
    ),
    "bypass": (
        '<a href="#main-content" class="skip-link">Skip to main content</a>\n<main id="main-content">...',
        "A skip link as the first element lets keyboard users bypass repeated navigation menus.",
    ),
    "html-has-lang": (
        '<html lang="en">',
        "<html> must have a lang attribute so screen readers choose the right voice.",
    ),
    "html-lang-valid": (
        '<html lang="en">  <!-- must be a valid BCP 47 tag -->',
        "The lang value must be a real BCP 47 language tag like 'en', 'fr', 'hi'.",
    ),
    "document-title": (
        "<title>Page Name — Site Name</title>",
        "Every page needs a unique descriptive <title> — users rely on it to orient themselves.",
    ),
    "frame-title": (
        '<iframe src="..." title="Description of embedded content"></iframe>',
        "iframes need a title attribute so screen readers can describe what's inside.",
    ),
    "tabindex": (
        '<!-- Remove tabindex > 0. Use tabindex="0" to include in tab order, tabindex="-1" for programmatic focus. -->',
        "tabindex values above 0 break the natural tab order — just remove them.",
    ),
    "aria-required-attr": (
        '<!-- Add the required ARIA attributes for the role you\'re using.\n'
        '     e.g. role="checkbox" must have aria-checked. -->',
        "ARIA roles have required attributes — missing ones make the widget unusable for AT.",
    ),
    "aria-roles": (
        '<!-- Use a valid ARIA role. See: https://www.w3.org/TR/wai-aria/#role_definitions -->',
        "The role attribute must be a real ARIA role value.",
    ),
    "aria-hidden-focus": (
        '<!-- Don\'t put aria-hidden="true" on anything that can receive focus.\n'
        '     If needed, set tabindex="-1" on focusable children first. -->',
        "aria-hidden='true' on a focusable element creates a keyboard trap for screen reader users.",
    ),
    "aria-valid-attr-value": (
        '<!-- Fix the attribute value to match its expected type.\n'
        '     e.g. aria-expanded must be "true" or "false", not "yes". -->',
        "ARIA attribute values must match what the spec allows for that attribute.",
    ),
    "aria-allowed-attr": (
        '<!-- Remove ARIA attributes that don\'t belong on this element\'s role. -->',
        "Only ARIA attributes valid for the current role should be used.",
    ),
    "list": (
        "<ul>\n  <li>Item one</li>\n  <li>Item two</li>\n</ul>",
        "<ul> and <ol> can only have <li> as direct children — nothing else.",
    ),
    "listitem": (
        "<!-- <li> must be inside a <ul> or <ol> — can't be used standalone. -->",
        "<li> elements need to live inside a <ul> or <ol>.",
    ),
    "scrollable-region-focusable": (
        '<div style="overflow:auto" tabindex="0" role="region" aria-label="Scrollable content">\n  ...\n</div>',
        "Scrollable areas must be keyboard-focusable (tabindex='0') so non-mouse users can scroll.",
    ),
    "select-name": (
        '<label for="country">Country</label>\n<select id="country">...</select>',
        "Every <select> needs a label so its purpose is announced.",
    ),
    "autocomplete-valid": (
        '<input type="email" autocomplete="email">',
        "The autocomplete value must match the field type per the HTML living standard.",
    ),
    "form-field-multiple-labels": (
        "<!-- Each input should have exactly one label — remove duplicates. -->",
        "Multiple labels on one input confuse screen readers about what the field is for.",
    ),
    "meta-viewport": (
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "Don't set user-scalable=no or maximum-scale — that blocks users who need to zoom.",
    ),
    "p-as-heading": (
        "<h2>Section heading text</h2>",
        "Bold/large <p> used as a heading should be an actual heading element.",
    ),
    "empty-heading": (
        "<h2>Visible heading text</h2>",
        "Empty headings break screen-reader navigation — add visible text.",
    ),
    "duplicate-id-active": (
        "<!-- Every id must be unique on the page. -->",
        "Duplicate ids on interactive elements break label associations and ARIA references.",
    ),
    "duplicate-id-aria": (
        "<!-- IDs used in aria-labelledby / aria-describedby must be unique. -->",
        "ARIA attribute references break when the target id exists more than once.",
    ),
    "th-has-data-cells": (
        '<th scope="col">Column header</th>',
        "Table <th> elements need a scope attribute so AT knows which cells they cover.",
    ),
    "video-caption": (
        '<video controls>\n  <track kind="captions" src="captions.vtt" srclang="en" label="English">\n</video>',
        "Videos with audio need synchronized captions (WCAG 1.2.2).",
    ),
    "object-alt": (
        '<object data="..." type="..."><p>Text fallback describing the object.</p></object>',
        "<object> elements need a text alternative inside them.",
    ),
}


def lookup_fix(rule_id: str):
    entry = RULE_FIXES.get(rule_id)
    if entry is None:
        return None
    fixed_html, explanation = entry
    return {"fixed_html": fixed_html, "explanation": explanation}
