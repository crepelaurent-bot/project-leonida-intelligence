import argparse
import json
import logging
import os
from pathlib import Path
from .storage import Store
from .github_api import GitHubClient
from .monitor import Monitor
from .reporting import generate_reports, update_changelog, write_immutable, render_rollup

def main():
    parser = argparse.ArgumentParser(description="Monitor public Project Leonida GitHub repositories.")
    parser.add_argument("--config", default="config/repos.json")
    parser.add_argument("--db", default="state/monitor.sqlite")
    parser.add_argument("--reports", default="reports")
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument("--bootstrap", action="store_true", help="Initial historical baseline; may consume many API requests.")
    parser.add_argument("--repo", help="Only monitor this owner/name repository.")
    args = parser.parse_args()

    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(level=os.getenv("LEONIDA_LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler("logs/monitor.log", encoding="utf-8")])
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    repos = config["repositories"]
    if args.repo:
        repos = [r for r in repos if r["full_name"].lower() == args.repo.lower()]
        if not repos:
            parser.error(f"Repository not configured: {args.repo}")
    store = Store(args.db)
    try:
        client = GitHubClient(store)
        monitor = Monitor(client, store, config.get("poll", {}))
        results, errors = monitor.run(repos, bootstrap=args.bootstrap)
        new_events = [e for result in results for e in result["new_events"]]
        all_events = store.all_events()
        report_paths = generate_reports(store, args.reports, new_events=new_events)
        update_changelog(args.changelog, all_events)
        if args.bootstrap:
            from datetime import datetime, timezone
            baseline = render_rollup("Initial research baseline", all_events)
            write_immutable(Path(args.reports) / "archive" /
                            f"{datetime.now(timezone.utc).date()}-initial-baseline.md", baseline)
        for result in results:
            logging.info("%s: %d new event(s)", result["repo"], len(result["new_events"]))
        for error in errors:
            logging.error("%s: %s", error["repo"], error["error"])
        logging.info("Reports written: %d; total stored events: %d", len(report_paths), len(all_events))
        if errors:
            raise SystemExit(2)
    finally:
        store.close()

if __name__ == "__main__":
    main()
