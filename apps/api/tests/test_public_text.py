from app.research.public_text import PublicText


def test_public_text_omits_executable_capability_fields_and_retains_readable_context():
    parser = PublicText("https://example.test/article")
    parser.feed('<h1>Company succession</h1><script>edit_token="secret"</script><form>password value</form><p>Announced July 1.</p><a href="/terms">Terms</a><a href="/edit?access_token=secret">Edit</a>')
    assert "Announced July 1." in parser.text
    assert "secret" not in parser.text and "password" not in parser.text
    assert parser.links == ["https://example.test/terms"]
