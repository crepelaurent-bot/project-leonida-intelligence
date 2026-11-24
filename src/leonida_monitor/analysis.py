from datetime import datetime, timezone

PRIORITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
MAP_WORDS = ("map", "maps", "gis", "coordinate", "landmark", "road", "rail", "waterway",
             "heightmap", "raster", "vector", "coastline", "contour", "qgis", "geojson",
             "shapefile", "tiles", "basemap", "vice city", "leonida keys")
TECH_WORDS = ("shader", "spir-v", "vulkan", "d3d12", "reverse", "rpf", "runtime", "loader",
              "recompil", "disassembl", "decoder", "texture", "model", "audio", "pipeline",
              "tool", "benchmark", "test harness")
ASSET_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".tif", ".tiff", ".geojson",
              ".shp", ".gpkg", ".qgz", ".qgs", ".obj", ".dds", ".rpf", ".glb", ".gltf")

def parse_time(value):
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def classify(title="", paths=None, repo_role="primary", kind="commit"):
    paths = paths or []
    text = (title + " " + " ".join(paths)).lower()
    map_hits = sum(1 for w in MAP_WORDS if w in text)
    tech_hits = sum(1 for w in TECH_WORDS if w in text)
    asset_hits = sum(1 for p in paths if p.lower().endswith(ASSET_EXTS))
    critical_terms = ("major map", "new region", "full map", "map reconstruction", "milestone")
    major_release_terms = ("major release", "breaking release", "stable release", "version 1.0", "v1.0")
    if any(x in text for x in critical_terms) or (kind == "release" and any(x in text for x in major_release_terms)):
        priority = "CRITICAL"
    elif kind == "release" or map_hits >= 2 or asset_hits >= 3 or tech_hits >= 3:
        priority = "HIGH"
    elif map_hits or tech_hits or asset_hits or kind in ("release", "pull_request", "issue"):
        priority = "MEDIUM"
    else:
        priority = "LOW"
    if repo_role in ("mapping", "gis", "mapping_data") and map_hits:
        priority = "HIGH" if priority == "MEDIUM" else priority
    if any(p.lower().endswith((".md", ".rst", ".txt")) for p in paths) and not (map_hits or tech_hits):
        priority = "LOW"
    confidence = "high" if paths else ("medium" if kind in ("release", "pull_request", "issue", "branch", "tag") else "low")
    return priority, confidence, map_hits > 0, tech_hits > 0

def make_event(repo, role, kind, ident, title, summary, url, created_at, paths=None, extra=None):
    priority, confidence, is_map, is_tech = classify(title, paths, role, kind)
    return {
        "event_key": f"{repo}:{kind}:{ident}",
        "repo": repo, "role": role, "kind": kind,
        "priority": priority, "confidence": confidence,
        "created_at": parse_time(created_at).astimezone(timezone.utc).isoformat(),
        "title": title or "(untitled)",
        "summary": summary or "No description supplied by GitHub.",
        "url": url, "paths": paths or [],
        "is_map": is_map, "is_technical": is_tech,
        "payload": extra or {}
    }
