import json
import tempfile
import unittest
from pathlib import Path

import app.db as db
from app import seed
from app.services.metro_service import MetroService, ValidationError


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        seed.init_db()

    def tearDown(self):
        self._tmp.cleanup()

    def test_seed_lines_and_memberships(self):
        with MetroService() as s:
            by_code = {l["code"]: l for l in s.lines()}
            self.assertEqual(set(by_code), {"L1", "L2"})
            self.assertEqual(by_code["L1"]["color"], "#e85d04")
            a2 = s.station("A2")
            self.assertEqual({l["code"] for l in a2["lines"]}, {"L1", "L2"})
            a1 = s.station("A1")
            self.assertEqual([l["code"] for l in a1["lines"]], ["L1"])
            edges = s.edges()
            edge = {(e["a"], e["b"]): e for e in edges}
            self.assertEqual(edge[("A1", "A2")]["line_code"], "L1")
            self.assertEqual(edge[("A1", "A2")]["line_color"], "#e85d04")

    def test_change_color_rejects_bad_value(self):
        with MetroService() as s:
            before = {l["code"]: l["color"] for l in s.lines()}
            for bad in ["red", "#fff", "#12345", "123456", "#gggggg", ""]:
                with self.assertRaises(ValidationError):
                    s.update_line_color("L1", bad)
            after = {l["code"]: l["color"] for l in s.lines()}
            self.assertEqual(before, after)

    def test_change_color_unknown_line_is_404(self):
        with MetroService() as s:
            self.assertIsNone(s.update_line_color("L9", "#000000"))

    def test_change_color_ok_then_snapshot_everywhere(self):
        with MetroService() as s:
            row = s.update_line_color("L1", "#112233")
            self.assertEqual(row["color"], "#112233")
            # 线网概览色带
            dash = next(l for l in s.dashboard()["lines"] if l["code"] == "L1")
            self.assertEqual(dash["color"], "#112233")
            # 该线路下站点详情同一口径
            a1 = s.station("A1")
            self.assertEqual(a1["lines"][0]["color"], "#112233")
            # 邻接列表同一口径
            edge = next(e for e in s.edges() if (e["a"], e["b"]) == ("A1", "A2"))
            self.assertEqual(edge["line_color"], "#112233")

    def test_assign_rejects_empty(self):
        with MetroService() as s:
            with self.assertRaises(ValidationError):
                s.update_station_lines("A3", [])
            self.assertEqual(
                [l["code"] for l in s.station("A3")["lines"]], ["L1"]
            )

    def test_assign_rejects_unknown_line_without_half_state(self):
        with MetroService() as s:
            original = [l["code"] for l in s.station("A3")["lines"]]
            with self.assertRaises(ValidationError):
                # 含一个不存在线路：整笔失败
                s.update_station_lines("A3", ["L2", "L9"])
            untouched = [l["code"] for l in s.station("A3")["lines"]]
            self.assertEqual(untouched, original)

    def test_assign_unknown_station_is_404(self):
        with MetroService() as s:
            self.assertIsNone(s.update_station_lines("X9", ["L1"]))

    def test_assign_replaces_and_dedups(self):
        with MetroService() as s:
            row = s.update_station_lines("A3", ["L2", "L2", "L1"])
            self.assertEqual([l["code"] for l in row["lines"]], ["L1", "L2"])

    def test_dashboard_groups_stations_by_line(self):
        with MetroService() as s:
            lines = {l["code"]: l for l in s.dashboard()["lines"]}
            self.assertEqual(
                {c["code"] for c in lines["L1"]["stations"]}, {"A1", "A2", "A3"}
            )
            self.assertEqual(
                {c["code"] for c in lines["L2"]["stations"]}, {"A2", "B1", "B2"}
            )

    def test_quote_line_sequence_and_transfer(self):
        with MetroService() as s:
            q = s.quote("A1", "B2", persist=False)
            self.assertEqual(q["path"], ["A1", "A2", "B1", "B2"])
            self.assertEqual([seg["code"] for seg in q["line_sequence"]], ["L1", "L2", "L2"])
            self.assertEqual(q["transfers"], 1)

    def test_persisted_quote_keeps_snapshot_after_recolor(self):
        with MetroService() as s:
            q = s.quote("A1", "B2", persist=True)
            run_id = q["run_id"]
            s.update_line_color("L1", "#abcdef")
        with MetroService() as s:
            rec = next(r for r in s.history() if r["id"] == run_id)
            payload = json.loads(rec["result_json"])
            # 已写入记录不回填新色带
            self.assertEqual(payload["line_sequence"][0]["color"], "#e85d04")
            self.assertEqual(payload["line_sequence"][0]["code"], "L1")
            # 起终点编码不变
            self.assertEqual(payload["start"], "A1")
            self.assertEqual(payload["end"], "B2")
            # 新询价反映新色带
            fresh = s.quote("A1", "B2", persist=False)
            self.assertEqual(fresh["line_sequence"][0]["color"], "#abcdef")


if __name__ == "__main__":
    unittest.main()
