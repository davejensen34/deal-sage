"""Bounded retrieval with durable access observations under the $5 envelope."""

import argparse
import asyncio
from hashlib import sha256
import re
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import httpx

from app.research.retrieval import assert_public_network_url
from app.research.public_text import PublicText, public_link
from app.research.validation_budget import ValidationBudget, PROTOCOL

# Utah Business's reviewed terms prohibit automated collection. A permissive
# robots file is not permission to ignore that publisher contract.
BLOCKED = {"legacy.com", "utahbusiness.com", "prnewswire.com", "facebook.com", "instagram.com", "linkedin.com", "x.com", "youtube.com"}


async def fetch(budget, url, purpose):
    if not public_link(url):
        raise ValueError("Retrieval requires a non-capability public URL")
    await assert_public_network_url(url)
    attempt = budget.reserve("http", {"url": url, "purpose": purpose}, label=purpose)
    result = {"status": "failed", "url": url, "purpose": purpose}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False, headers={"User-Agent":"DealSage/0.1 responsible-research"}) as client:
            async with client.stream("GET", url) as response:
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > 1000000:
                        raise ValueError("Response too large")
                media = response.headers.get("content-type", "").split(";",1)[0]
                result.update(http_status=response.status_code, media_type=media, raw_sha256=sha256(body).hexdigest())
                if response.is_redirect:
                    # Record the redirect, but require review before a new request.
                    location = public_link(urljoin(url, response.headers.get("location", "")))
                    result.update(status="redirect")
                    if location and len(location) <= 2000:
                        result["location"] = location
                    else:
                        result["redirect_review"] = "sensitive_or_unsupported_location"
                elif media in {"text/html", "text/plain", "application/xhtml+xml"}:
                    text = body.decode("utf-8", "replace")
                    if media != "text/plain":
                        parser = PublicText(url); parser.feed(text); text = parser.text
                        links = list(dict.fromkeys(parser.links))
                        result["policy_links"] = [u for u in links if re.search(r"terms|privacy|/legal(?:/|$)|/polic(?:y|ies)(?:/|$)", urlsplit(u).path, re.I)][:30]
                        result["public_links"] = links[:150]
                    # Only non-executable extracted text crosses persistence.
                    result.update(status="returned", text_file=f"text-{attempt:03}.txt", text_sha256=sha256(text.encode()).hexdigest())
                    # Hash and persist identical bytes on Windows as well as Unix.
                    # Text-mode writes would expand LF to CRLF after hashing.
                    (budget.directory / result["text_file"]).write_bytes(text.encode("utf-8"))
                else:
                    result["status"] = "unsupported_media"
        budget.finish(attempt, result)
        return result
    except Exception as error:
        result["error_class"] = type(error).__name__
        budget.finish(attempt, result)
        return result


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--approval", choices=[PROTOCOL], required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--purpose", choices=["article", "policy"], default="article")
    args = parser.parse_args()
    host = urlsplit(args.url).hostname or ""
    if any(host == h or host.endswith("."+h) for h in BLOCKED) or host.startswith("obits."):
        print({"status":"blocked", "reason":"publisher_contract_or_alias_requires_review"}); return
    budget = ValidationBudget(args.directory, args.approval)
    with budget.locked():
        origin = f"{urlsplit(args.url).scheme}://{urlsplit(args.url).netloc}"
        robots = await fetch(budget, origin+"/robots.txt", "robots")
        if robots.get("http_status") == 404:
            allowed, delay = True, 0
        elif robots.get("status") == "returned" and robots.get("http_status") == 200:
            rp=RobotFileParser(); rp.parse((budget.directory/robots["text_file"]).read_text(encoding="utf-8").splitlines())
            allowed = rp.can_fetch("DealSage", args.url)
            delay = rp.crawl_delay("DealSage") or rp.crawl_delay("*") or 0
        else:
            print({"status":"blocked", "reason":"robots_unavailable", "observation":robots}); return
        if not allowed or delay > 30:
            print({"status":"blocked", "reason":"robots_disallowed_or_delay", "observation":robots}); return
        if delay: await asyncio.sleep(delay)
        result = await fetch(budget, args.url, args.purpose)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
