from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import re

def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "event"

def write_immutable(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.stem}-revision-{n}{path.suffix}")
        if not candidate.exists():
            candidate.write_text(content, encoding="utf-8")
            return candidate
        n += 1

def render_event(event):
    paths = event.get("paths") or []
    lines = [
        f"# {event['priority']}: {event['title']}", "",
        f"- **Zeitpunkt (UTC):** {event['created_at']}",
        f"- **Repository:** [{event['repo']}](https://github.com/{event['repo']})",
        f"- **Typ:** `{event['kind']}`",
        f"- **Priorität:** `{event['priority']}`",
        f"- **Vertrauen:** `{event['confidence']}`",
        f"- **Quelle:** {event['url']}", "",
        "## Zusammenfassung", "", event.get("summary", ""), "",
        "## Technische Details", "",
        f"- Quelle klassifiziert als: `{event.get('role','unknown')}`.",
        f"- Mapping/GIS-Bezug: `{'ja' if event.get('is_map') else 'nicht erkannt'}`.",
        f"- Technischer Forschungsbezug: `{'ja' if event.get('is_technical') else 'nicht erkannt'}`.",
        f"- Erkannte Dateien: {len(paths)}."
    ]
    if paths:
        lines += ["", "### Geänderte Dateien", ""] + [f"- `{p}`" for p in paths[:300]]
        if len(paths) > 300:
            lines.append(f"- … plus {len(paths)-300} weitere Pfade.")
    lines += ["", "## Bedeutung und Vergleich", "",
              "Die Bedeutung wird heuristisch aus Titel, Repository-Rolle und Dateipfaden abgeleitet. "
              "Vor einer fachlichen Schlussfolgerung sind Diff und Projektkontext zu prüfen.",
              "", "## Vertrauensbewertung", "",
              f"**{event['confidence']}** – GitHub-Quelle direkt verlinkt; inhaltliche Interpretation ist regelbasiert.",
              ""]
    return "\n".join(lines)

def generate_reports(store, reports_dir, new_events=None):
    root = Path(reports_dir)
    events = store.all_events()
    new_events = new_events or []
    if not events or not new_events:
        return []
    created = []
    for e in new_events:
        if e.get("_reported"):
            continue
        stamp = e["created_at"][:19].replace(":", "").replace("-", "")
        name = f"{stamp}-{slug(e['repo'] + '-' + e['title'])}.md"
        if e.get("priority") == "CRITICAL":
            folder = "breaking"
        elif e.get("is_map"):
            folder = "maps"
        elif e.get("is_technical"):
            folder = "technical"
        else:
            continue
        path = write_immutable(root / folder / name, render_event(e))
        created.append(path)
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    today_events = [e for e in events if day_start.isoformat() <= e["created_at"] < day_end.isoformat()]
    if today_events and new_events:
        content = render_rollup(f"Tagesbericht {day_start.date()}", today_events)
        created.append(write_immutable(root / "daily" / f"{day_start.date()}.md", content))
    iso = now.isocalendar()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_events = [e for e in events if week_start.isoformat() <= e["created_at"] <= now.isoformat()]
    if week_events and new_events:
        created.append(write_immutable(root / "weekly" / f"{iso.year}-W{iso.week:02d}.md",
                                      render_rollup(f"Wochenbericht {iso.year}-W{iso.week:02d}", week_events)))
    return created

def render_rollup(title, events):
    counts = Counter(e["priority"] for e in events)
    lines = [f"# {title}", "", f"- Erstellt (UTC): {datetime.now(timezone.utc).isoformat()}",
             f"- Beobachtete Ereignisse: {len(events)}", "",
             "## Prioritäten", ""]
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        lines.append(f"- {level}: {counts.get(level, 0)}")
    lines += ["", "## Ereignisse", ""]
    for e in events:
        lines += [f"### [{e['priority']}] {e['title']}", "",
                  f"- Repository: `{e['repo']}` · Typ: `{e['kind']}`",
                  f"- Quelle: {e['url']}", "", e["summary"], ""]
    return "\n".join(lines)

def update_changelog(path, events):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Intelligence changelog\n\n"
    known = set(re.findall(r"event-id: ([^\s]+)", existing))
    new = [e for e in events if e["event_key"] not in known]
    if not new:
        return False
    sections = []
    for e in new:
        sections += [f"## {e['created_at'][:10]} — {e['title']}", "",
                     f"- **{e['priority']}** · `{e['kind']}` · `{e['repo']}`",
                     f"- {e['summary']}", f"- Quelle: {e['url']}",
                     f"- event-id: {e['event_key']}", ""]
    path.write_text(existing.rstrip() + "\n\n" + "\n".join(sections), encoding="utf-8")
    return True
