import tempfile
import unittest
from pathlib import Path
from leonida_monitor.analysis import classify, make_event
from leonida_monitor.storage import Store
from leonida_monitor.reporting import write_immutable, render_event

class MonitorTests(unittest.TestCase):
    def test_map_asset_classification(self):
        priority, confidence, is_map, is_tech = classify(
            "Add road network and coastline data",
            ["data/roads.geojson", "rasters/heightmap_16bit.png"], "gis", "commit")
        self.assertIn(priority, ("HIGH", "CRITICAL"))
        self.assertTrue(is_map)
        self.assertEqual(confidence, "high")

    def test_technical_classification(self):
        priority, _, _, is_tech = classify("Improve shader SPIR-V Vulkan pipeline",
                                           ["src/rdna2spirv.py"], "primary", "commit")
        self.assertIn(priority, ("HIGH", "MEDIUM"))
        self.assertTrue(is_tech)

    def test_event_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "state.sqlite")
            event = make_event("owner/repo", "primary", "commit", "abc", "test",
                               "summary", "https://github.com/owner/repo/commit/abc",
                               "2026-11-24T00:00:00Z", ["README.md"])
            self.assertTrue(store.add_event(event))
            self.assertFalse(store.add_event(event))
            self.assertEqual(len(store.all_events()), 1)
            store.close()

    def test_immutable_report_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "daily.md"
            self.assertEqual(write_immutable(p, "one"), p)
            second = write_immutable(p, "two")
            self.assertNotEqual(second, p)
            self.assertEqual(p.read_text(), "one")
            self.assertEqual(second.read_text(), "two")

    def test_report_contains_source(self):
        event = make_event("owner/repo", "primary", "commit", "abc", "title",
                           "summary", "https://github.com/owner/repo/commit/abc",
                           "2026-11-24T00:00:00Z", ["src/main.py"])
        rendered = render_event(event)
        self.assertIn("https://github.com/owner/repo/commit/abc", rendered)
        self.assertIn("src/main.py", rendered)

if __name__ == "__main__":
    unittest.main()
