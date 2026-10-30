import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('supplement', Path(__file__).parents[1] / 'scripts/supplement.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def archive(path):
    en = json.dumps({'one': 'File', 'new': 'Untranslated fallback'}).encode()
    zh = json.dumps({'one': '文件'}).encode()
    files = {'en-US.json': {'offset': '0', 'size': len(en)},
             'zh-Hans.json': {'offset': str(len(en)), 'size': len(zh)}}
    header = {'files': {'resources': {'files': {'i18n': {'files': files}}},
                        'native.node': {'size': 2, 'unpacked': True}}}
    encoded = json.dumps(header).encode()
    payload = (len(encoded) + 7) // 4 * 4
    path.write_bytes(struct.pack('<4I', 4, payload + 4, payload, len(encoded))
                     + encoded + bytes(payload - 4 - len(encoded)) + en + zh)
    return en + zh


class SupplementTests(unittest.TestCase):
    def test_catalog_preserves_original_offsets_and_unpacked_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = archive(root / 'app.asar')
            (root / 'zh.json').write_text(json.dumps({'extra': '菜单'}), encoding='utf-8')
            module.add_native_catalog(root / 'app.asar', root / 'zh.json')
            header, body = module.read_asar(root / 'app.asar')
            self.assertEqual(body[:len(original)], original)
            self.assertTrue(header['files']['native.node']['unpacked'])
            catalog = module.catalog_bytes(header, body, 'zh-CN.json')
            self.assertEqual(catalog['one'], '文件')
            self.assertEqual(catalog['new'], 'Untranslated fallback')
            self.assertEqual(catalog['extra'], '菜单')

    def test_rejects_corrupt_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'bad.asar'
            p.write_bytes(struct.pack('<4I', 7, 0, 0, 0))
            with self.assertRaises(ValueError):
                module.read_asar(p)

    def test_display_labels_keep_ids_and_icons(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            assets = root / 'assets/v1'
            assets.mkdir(parents=True)
            (assets / 'a.js').write_text('const a={key:"task",label:"Cowork"};const b={key:"code",label:"Code"};', encoding='utf-8')
            (assets / 'b.js').write_text('const a={mode:"cowork",icon:"Tasks",label:"Cowork"};const b={icon:"Code",label:"Code"};', encoding='utf-8')
            (assets / 's.js').write_text('var A=m(function(e){let x=1;return x});export{A as ChorusCoworkSuggestions};', encoding='utf-8')
            module.patch_frontend(root)
            self.assertIn('key:"code",label:"编程"', (assets / 'a.js').read_text(encoding='utf-8'))
            self.assertIn('icon:"Code",label:"编程"', (assets / 'b.js').read_text(encoding='utf-8'))
            self.assertIn('function(e){return null;', (assets / 's.js').read_text(encoding='utf-8'))

    def test_unknown_frontend_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'assets/v1').mkdir(parents=True)
            with self.assertRaises(ValueError):
                module.patch_frontend(root)


if __name__ == '__main__':
    unittest.main()
