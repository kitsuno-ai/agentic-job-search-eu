from __future__ import annotations

import json
import unittest

from tools.freshness.parser import parse_mpsv_json, parse_mpsv_xml, parse_payload


class TestParser(unittest.TestCase):
    def test_parse_valid_mpsv_json(self):
        sample = {
            "polozky": [
                {
                    "id": "CZ-1001",
                    "portalId": 1001,
                    "datumVlozeni": "2026-09-01T08:00:00Z",
                    "datumZmeny": "2026-09-10T12:00:00Z",
                    "expirace": "2026-10-31",
                },
                {
                    "referencniCislo": "CZ-1002",
                    "datumVlozeni": "2026-09-05",
                    "operace": "smaz",
                },
            ]
        }
        res = parse_mpsv_json(sample)
        self.assertEqual(res.raw_count, 2)
        self.assertEqual(len(res.listings), 2)
        self.assertEqual(res.drift_warnings, [])

        l1 = res.listings[0]
        self.assertEqual(l1.listing_id, "CZ-1001")
        self.assertEqual(l1.posted, "2026-09-01")
        self.assertEqual(l1.updated, "2026-09-10")
        self.assertEqual(l1.expires, "2026-10-31")
        self.assertEqual(l1.operation, "active")

        l2 = res.listings[1]
        self.assertEqual(l2.listing_id, "CZ-1002")
        self.assertEqual(l2.posted, "2026-09-05")
        self.assertEqual(l2.operation, "delete")

    def test_parse_valid_mpsv_xml(self):
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <volna_mista>
            <polozka>
                <id>XML-501</id>
                <datumVlozeni>2026-08-15T09:30:00</datumVlozeni>
                <datumZmeny>2026-08-20T10:00:00</datumZmeny>
                <expirace>2026-11-15</expirace>
                <operace>vloz</operace>
            </polozka>
            <polozka>
                <id>XML-502</id>
                <datumVlozeni>2026-08-18</datumVlozeni>
                <operace>zmena</operace>
            </polozka>
        </volna_mista>
        """
        res = parse_mpsv_xml(xml_content)
        self.assertEqual(res.raw_count, 2)
        self.assertEqual(len(res.listings), 2)
        self.assertEqual(res.drift_warnings, [])

        l1 = res.listings[0]
        self.assertEqual(l1.listing_id, "XML-501")
        self.assertEqual(l1.posted, "2026-08-15")
        self.assertEqual(l1.expires, "2026-11-15")
        self.assertEqual(l1.operation, "add")

        l2 = res.listings[1]
        self.assertEqual(l2.listing_id, "XML-502")
        self.assertEqual(l2.operation, "update")

    def test_schema_drift_missing_polozky(self):
        sample = {"some_other_key": [{"id": "123"}]}
        res = parse_mpsv_json(sample)
        self.assertTrue(any("Expected top-level array 'polozky'" in w for w in res.drift_warnings))

    def test_schema_drift_missing_id(self):
        # 10 records missing IDs should trigger drift warning (> 5%)
        sample = {
            "polozky": [{"datumVlozeni": "2026-09-01"} for _ in range(10)]
        }
        res = parse_mpsv_json(sample)
        self.assertTrue(any("Over 5% of records" in w and "lacked an identifiable ID" in w for w in res.drift_warnings))

    def test_parse_payload_auto_detect(self):
        json_bytes = b'{"polozky": [{"id": "A1", "datumVlozeni": "2026-01-01"}]}'
        res = parse_payload(json_bytes, format_hint="auto")
        self.assertEqual(len(res.listings), 1)
        self.assertEqual(res.listings[0].listing_id, "A1")

        xml_bytes = b'<volna_mista><polozka><id>B1</id><datumVlozeni>2026-01-01</datumVlozeni></polozka></volna_mista>'
        res_xml = parse_payload(xml_bytes, format_hint="auto")
        self.assertEqual(len(res_xml.listings), 1)
        self.assertEqual(res_xml.listings[0].listing_id, "B1")


if __name__ == "__main__":
    unittest.main()
