import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('importer', Path(__file__).resolve().parents[1] / 'scripts/update_publications.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Synthetic fixtures exercise the importer; these are not actual bibliography data.
XML = b'''<dblpperson pid="15/2739" n="1"><r><article key="journals/test/example"><author>Engin Erzin</author><title>A <i>mixed</i> title.</title><year>2025</year><journal>Test</journal></article></r></dblpperson>'''

class ImportTests(unittest.TestCase):
    def test_preserves_text_and_count(self):
        data = module.convert(XML, '2026-10-21')
        self.assertEqual(data['publications'][0]['title'], 'A mixed title.')
        self.assertEqual(data['source_record_count'], len(data['publications']))
        self.assertEqual(data['publications'][0]['category'], 'Journal Articles')

    def test_rejects_incomplete_wrong_person_and_challenge(self):
        for raw in [XML.replace(b'n="1"', b'n="2"'), XML.replace(b'15/2739', b'99/999'), b'<html>challenge</html>', XML.replace(b'<year>2025</year>', b'')]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                module.convert(raw, '2026-10-21')

    def test_rejects_duplicates(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(XML)
        root.append(ET.fromstring(XML).find('r'))
        root.set('n', '2')
        with self.assertRaises(ValueError):
            module.convert(ET.tostring(root), '2026-10-21')
