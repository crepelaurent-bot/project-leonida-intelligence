from datetime import datetime, timezone
from .analysis import make_event
from .github_api import GitHubAPIError

def _time(obj, *keys):
    for key in keys:
        if obj.get(key):
            return obj[key]
    return datetime.now(timezone.utc).isoformat()

class Monitor:
    def __init__(self, client, store, poll):
        self.client, self.store = client, store
        self.per_page = int(poll.get("per_page", 100))
        self.max_items = int(poll.get("max_items_per_endpoint", 5000))
        self.bootstrap_pages = int(poll.get("history_pages_on_bootstrap", 0))

    def _add(self, event):
        return self.store.add_event(event)

    def run_repo(self, repo_cfg, bootstrap=False):
        repo = repo_cfg["full_name"]
        role = repo_cfg.get("role", "related")
        added = []
        meta = self.client.get(f"/repos/{repo}")
        default_branch = meta["default_branch"]
        branch_names = [default_branch]
        for item in self.client.pages(f"/repos/{repo}/branches", self.per_page, self.max_items):
            name = item.get("name", "")
            sha = (item.get("commit") or {}).get("sha")
            if not name:
                continue
            if name not in branch_names:
                branch_names.append(name)
            event = make_event(repo, role, "branch", f"{name}:{sha}", f"Branch head changed: {name}",
                               f"Branch `{name}` currently points to `{sha or 'unknown SHA'}`.",
                               f"https://github.com/{repo}/tree/{name}",
                               datetime.now(timezone.utc).isoformat())
            if self._add(event): added.append(event)
        for item in self.client.pages(f"/repos/{repo}/tags", self.per_page, self.max_items):
            name = item.get("name", "")
            sha = (item.get("commit") or {}).get("sha")
            if not name:
                continue
            event = make_event(repo, role, "tag", f"{name}:{sha}", f"Tag observed: {name}",
                               f"Tag `{name}` resolves to `{sha or 'unknown SHA'}`.",
                               f"https://github.com/{repo}/releases",
                               datetime.now(timezone.utc).isoformat())
            if self._add(event): added.append(event)
        for release in self.client.pages(f"/repos/{repo}/releases", self.per_page, self.max_items):
            ident = release.get("id") or release.get("tag_name")
            event = make_event(repo, role, "release", str(ident) + ":" + str(release.get("updated_at")), release.get("name") or release.get("tag_name"),
                               release.get("body") or "Release published without notes.",
                               release.get("html_url") or f"https://github.com/{repo}/releases",
                               _time(release, "published_at", "created_at"),
                               extra={"tag_name": release.get("tag_name"), "draft": release.get("draft"),
                                      "prerelease": release.get("prerelease")})
            if self._add(event): added.append(event)
        for branch in branch_names:
            cursor = self.store.get_cursor(repo, branch)
            commit_path = f"/repos/{repo}/commits?sha={branch}"
            commits_seen = []
            max_items = self.max_items
            if not cursor and not bootstrap:
                max_items = min(self.per_page, self.max_items)
            elif not cursor and bootstrap and self.bootstrap_pages > 0:
                max_items = min(self.bootstrap_pages * self.per_page, self.max_items)
            for commit in self.client.pages(commit_path, self.per_page, max_items):
                sha = commit.get("sha")
                if not sha:
                    continue
                if cursor and sha == cursor:
                    break
                commits_seen.append(commit)
            for commit in reversed(commits_seen):
                sha = commit["sha"]
                detail = self.client.get(f"/repos/{repo}/commits/{sha}")
                changed = detail.get("files", [])
                paths = [f.get("filename", "") for f in changed]
                msg = (detail.get("commit") or {}).get("message", "").splitlines()[0]
                author_date = ((detail.get("commit") or {}).get("author") or {}).get("date")
                event = make_event(repo, role, "commit", sha, msg,
                                   f"Commit `{sha[:12]}`: {len(paths)} changed file(s).",
                                   detail.get("html_url") or f"https://github.com/{repo}/commit/{sha}",
                                   author_date, paths,
                                   {"sha": sha, "files": changed, "branch": branch})
                if self._add(event): added.append(event)
            if commits_seen:
                self.store.set_cursor(repo, branch, commits_seen[0]["sha"])
            else:
                self.store.set_cursor(repo, branch, cursor or "")
        for item in self.client.pages(f"/repos/{repo}/issues?state=all&sort=updated&direction=desc",
                                      self.per_page, self.max_items):
            is_pr = "pull_request" in item
            kind = "pull_request" if is_pr else "issue"
            ident = item.get("number")
            updated = item.get("updated_at") or item.get("created_at")
            event = make_event(repo, role, kind, f"{ident}:{updated}", item.get("title"),
                               item.get("body") or "No description supplied.",
                               item.get("html_url") or f"https://github.com/{repo}/issues/{ident}",
                               _time(item, "updated_at", "created_at"),
                               extra={"state": item.get("state"), "number": ident,
                                      "updated_at": item.get("updated_at")})
            if is_pr:
                try:
                    changed_files = list(self.client.pages(f"/repos/{repo}/pulls/{ident}/files",
                                                            self.per_page, self.max_items))
                    event["paths"] = [f.get("filename", "") for f in changed_files]
                    from .analysis import classify
                    event["priority"], event["confidence"], event["is_map"], event["is_technical"] = classify(
                        event["title"], event["paths"], role, kind)
                except GitHubAPIError:
                    pass
            if self._add(event):
                added.append(event)
                try:
                    comments = self.client.pages(f"/repos/{repo}/issues/{ident}/comments",
                                                  self.per_page, self.max_items)
                    for comment in comments:
                        cid = comment.get("id")
                        body = comment.get("body") or "(empty comment)"
                        reply = make_event(repo, role, "comment", str(cid) + ":" + str(comment.get("updated_at")),
                                           f"Developer comment on {kind} #{ident}",
                                           body[:4000], comment.get("html_url") or event["url"],
                                           _time(comment, "updated_at", "created_at"),
                                           extra={"parent_number": ident, "parent_kind": kind})
                        if self._add(reply): added.append(reply)
                except GitHubAPIError:
                    pass
        return {"repo": repo, "default_branch": default_branch, "new_events": added}

    def run(self, repositories, bootstrap=False):
        results, errors = [], []
        for cfg in repositories:
            try:
                results.append(self.run_repo(cfg, bootstrap))
            except Exception as exc:
                errors.append({"repo": cfg.get("full_name"), "error": str(exc)})
        return results, errors
