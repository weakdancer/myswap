import re
from markupsafe import Markup, escape

def transform_url(text):
    """Escape plain text and link only HTTP(S) URLs without allowing HTML."""
    if not text:
        return Markup('')
    parts = []
    previous_end = 0
    for match in re.finditer(r'https?://[^\s<>"\']+', text):
        parts.append(escape(text[previous_end:match.start()]))
        url = match.group(0)
        parts.append(Markup('<a target="_blank" rel="noopener noreferrer" class="myswap-link" href="{}">{}</a>').format(url, url))
        previous_end = match.end()
    parts.append(escape(text[previous_end:]))
    return Markup('').join(parts)

def init_filters(app):
    app.jinja_env.filters['transform_url'] = transform_url
