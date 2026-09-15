"""Conservative readable excerpts, never execution or paywall extraction."""
from html.parser import HTMLParser
import re

EXCLUDED = {'head', 'script', 'style', 'template', 'noscript', 'nav', 'footer',
            'header', 'svg', 'canvas', 'form', 'aside'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
BLOCK = {'p', 'div', 'section', 'article', 'main', 'li', 'ul', 'ol', 'br', 'hr',
         'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'td', 'blockquote'}


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = {'body': [], 'main': [], 'article': []}
        self.restricted = False

    def append(self, text):
        if any(hidden for _, hidden in self.stack):
            return
        self.parts['body'].append(text)
        for scope in ('main', 'article'):
            if any(tag == scope for tag, _ in self.stack):
                self.parts[scope].append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('property') or a.get('name') or '').lower() == 'article:content_tier':
            if (a.get('content') or '').lower() in {'metered', 'premium', 'paid', 'subscriber', 'subscription'}:
                self.restricted = True
        self.append('\n' if tag in BLOCK else '')
        style = re.sub(r'\s+', '', a.get('style') or '').lower()
        hidden = (tag in EXCLUDED or 'hidden' in a or (a.get('aria-hidden') or '').lower() == 'true'
                  or 'display:none' in style or 'visibility:hidden' in style)
        if tag not in VOID:
            if len(self.stack) >= 256:
                raise ValueError('HTML nesting exceeds the excerpt limit')
            self.stack.append((tag, hidden))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        # Recover ordinary unbalanced blocks without exposing content from an
        # unclosed excluded tag. A missing script/head close stays conservative.
        matches = [i for i, (name, _) in enumerate(self.stack) if name == tag]
        if matches:
            index = matches[-1]
            if any(hidden for _, hidden in self.stack[index + 1:]):
                return
            del self.stack[index:]
        self.append('\n' if tag in BLOCK else '')

    def handle_data(self, data):
        # Inspect only an access marker in structured data, never its articleBody.
        if any(tag == 'script' for tag, _ in self.stack):
            if re.search(r'"isAccessibleForFree"\s*:\s*(?:false|"false")', data, re.I):
                self.restricted = True
        self.append(data)


def html_excerpt(content: bytes, limit: int = 2000) -> str | None:
    parser = ReadableHTML()
    try:
        parser.feed(content.decode('utf-8', errors='replace'))
        parser.close()
    except ValueError:
        return None
    if parser.restricted:
        return None
    # Prefer article/main text over surrounding chrome. This is a bounded
    # representation of retained source bytes, not an assertion of their truth.
    for scope in ('article', 'main', 'body'):
        text = re.sub(r'\s+', ' ', ''.join(parser.parts[scope])).strip()
        if text:
            return text[:limit]
    return None
