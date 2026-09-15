import pytest
from app.research.retrieval import _bounded_text_excerpt


def test_long_headers_and_page_chrome_cannot_displace_article_text():
    html = '<head><script>' + 'tracking();' * 1000 + '</script></head>'
    html += '<body><nav>Home Sign in</nav><main>Navigation<article><h1>Owner retires</h1><p>Acme &amp; Sons <b>announced</b> a succession.</p></article></main><footer>Legal</footer></body>'
    assert _bounded_text_excerpt(html.encode(), 'text/html') == 'Owner retires Acme & Sons announced a succession.'


def test_hidden_and_executable_content_is_never_a_source_excerpt():
    html = '<main><p hidden>secret</p><p aria-hidden="true">hidden</p><div style="display: none">hidden</div><template>hidden</template><script type="application/ld+json">{"articleBody":"hidden body"}</script><p>Visible <em>source</em> text.</p></main>'
    assert _bounded_text_excerpt(html.encode(), 'text/html') == 'Visible source text.'


@pytest.mark.parametrize('marker', [
    '<meta property="article:content_tier" content="metered">',
    '<script type="application/ld+json">{"isAccessibleForFree":false,"articleBody":"protected"}</script>',
])
def test_declared_restricted_content_is_not_extracted(marker):
    assert _bounded_text_excerpt((marker + '<article>Protected article</article>').encode(), 'text/html') is None


def test_excerpt_is_bounded_and_plain_text_is_preserved():
    assert len(_bounded_text_excerpt(('<p>' + 'word ' * 1000 + '</p>').encode(), 'text/html')) == 2000
    assert _bounded_text_excerpt(b'Exact source\ntext', 'text/plain') == 'Exact source\ntext'
    assert _bounded_text_excerpt(b'{"value":12}', 'application/json') == '{"value":12}'


def test_missing_hidden_close_does_not_expose_following_text():
    assert _bounded_text_excerpt(b'<main><div hidden>hidden</main>still hidden', 'text/html') is None
    assert _bounded_text_excerpt(b'<main><p>Readable<br>text', 'text/html') == 'Readable text'
    assert _bounded_text_excerpt(b'<meta property><main aria-hidden>Readable</main>', 'text/html') == 'Readable'
    assert _bounded_text_excerpt(b'<div>' * 257 + b'text', 'text/html') is None
