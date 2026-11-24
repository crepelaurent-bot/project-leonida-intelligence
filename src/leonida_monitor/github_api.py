import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"

class GitHubAPIError(RuntimeError):
    pass

class GitHubClient:
    def __init__(self, store, token=None):
        self.store = store
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.user_agent = os.getenv("LEONIDA_USER_AGENT", "ProjectLeonida-Intelligence-Monitor/1.0")

    def get(self, url):
        if url.startswith("/"):
            url = API + url
        cached = self.store.cached(url)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if cached and cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]
        if cached and cached.get("last_modified"):
            headers["If-Modified-Since"] = cached["last_modified"]
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                body = response.read().decode("utf-8")
                self.store.save_cache(url, response.headers.get("ETag"),
                                      response.headers.get("Last-Modified"), body)
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and cached:
                return json.loads(cached["body"])
            if exc.code in (403, 429):
                reset = exc.headers.get("X-RateLimit-Reset")
                remaining = exc.headers.get("X-RateLimit-Remaining")
                raise GitHubAPIError(f"GitHub rate/permission error {exc.code}; remaining={remaining}; reset={reset}") from exc
            if exc.code == 404:
                raise GitHubAPIError(f"GitHub resource not found: {url}") from exc
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise GitHubAPIError(f"GitHub HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GitHubAPIError(f"GitHub network error for {url}: {exc}") from exc

    def pages(self, path, per_page=100, max_items=5000):
        page = 1
        count = 0
        while count < max_items:
            query = urllib.parse.urlencode({"per_page": min(per_page, 100), "page": page})
            url = f"{API}{path}{'&' if '?' in path else '?'}{query}"
            data = self.get(url)
            if not isinstance(data, list):
                raise GitHubAPIError(f"Expected list from {url}")
            if not data:
                break
            for item in data:
                yield item
                count += 1
                if count >= max_items:
                    break
            if len(data) < min(per_page, 100):
                break
            page += 1
            time.sleep(0.05)
