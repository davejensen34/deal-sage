"""Non-executable retained public text for bounded case-specific review."""

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, parse_qsl
from app.research.sanitization import is_sensitive_field


def public_link(url):
    """Allow ordinary public links without retaining capability query fields."""
    try:
        parsed = urlsplit(url)
        if (parsed.scheme in {"http", "https"} and parsed.hostname
                and not parsed.username and not parsed.password
                and not any(is_sensitive_field(k) for k, _ in parse_qsl(parsed.query))):
            return url
    except ValueError:
        pass
    return None


class PublicText(HTMLParser):
    def __init__(self, url):
        super().__init__()
        self.url, self.parts, self.links, self.skip = url, [], [], []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "form", "template"}:
            self.skip.append(tag)
        if self.skip:
            return
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            link = urljoin(self.url, attrs["href"])
            if public_link(link):
                self.links.append(link)

    def handle_endtag(self, tag):
        if self.skip and self.skip[-1] == tag:
            self.skip.pop()

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())

    @property
    def text(self):
        return "\n".join(self.parts)
