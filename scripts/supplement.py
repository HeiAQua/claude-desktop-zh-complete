"""Extra display-only patches. No credentials, telemetry, or model requests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def read_asar(path):
    raw = Path(path).read_bytes()
    a, size, payload, length = struct.unpack('<4I', raw[:16])
    if a != 4 or payload + 4 != size or length > payload - 4:
        raise ValueError('Unsupported ASAR header')
    return json.loads(raw[16:16 + length]), raw[8 + size:]


def catalog_bytes(header, body, name):
    entry = header['files']['resources']['files']['i18n']['files'][name]
    start = int(entry['offset'])
    return json.loads(body[start:start + entry['size']])


def add_native_catalog(archive, translations):
    header, body = read_asar(archive)
    files = header['files']['resources']['files']['i18n']['files']
    # Merge against the installed app, so newer menu keys retain a fallback.
    merged = catalog_bytes(header, body, 'en-US.json')
    merged.update(catalog_bytes(header, body, 'zh-Hans.json'))
    merged.update(json.loads(Path(translations).read_text(encoding='utf-8-sig')))
    for key, value in merged.items():
        if isinstance(value, str):
            merged[key] = value.replace('Cowork', '协作').replace('Claude Code', 'Claude 编程')
    data = json.dumps(merged, ensure_ascii=False, separators=(',', ':')).encode()
    block = 4 * 1024 * 1024
    files['zh-CN.json'] = {
        'size': len(data), 'offset': str(len(body)),
        'integrity': {'algorithm': 'SHA256', 'hash': hashlib.sha256(data).hexdigest(),
                      'blockSize': block,
                      'blocks': [hashlib.sha256(data[i:i + block]).hexdigest()
                                 for i in range(0, len(data), block)]}}
    encoded = json.dumps(header, ensure_ascii=False, separators=(',', ':')).encode()
    payload = (len(encoded) + 4 + 3) // 4 * 4
    Path(archive).write_bytes(struct.pack('<4I', 4, payload + 4, payload, len(encoded))
                             + encoded + bytes(payload - 4 - len(encoded)) + body + data)
    result, new_body = read_asar(archive)
    assert catalog_bytes(result, new_body, 'zh-CN.json') == merged


def patch_frontend(root, hide_suggestions=True):
    root = Path(root)
    assets = root / 'assets' / 'v1'
    if not assets.is_dir():
        raise ValueError('Unsupported frontend asset layout')
    label_files = 0
    suggestion_files = 0
    for path in assets.glob('*.js'):
        text = path.read_text(encoding='utf-8')
        changed = text
        # Only display label properties, never icon names, IDs, or enum values.
        if 'key:"task",label:"Cowork"' in text or 'mode:"cowork",icon:"Tasks",label:"Cowork"' in text:
            changed = changed.replace('label:"Cowork"', 'label:"协作"').replace('label:"Code"', 'label:"编程"')
            label_files += 1
        if hide_suggestions and ' as ChorusCoworkSuggestions}' in text:
            match = re.search(r'export\{([\w$]+) as ChorusCoworkSuggestions\}', text)
            if not match:
                raise ValueError('Suggestions export changed')
            symbol = re.escape(match.group(1))
            pattern = r'(' + symbol + r'=[\w$]+\(function\(e\)\{)(?!return null;)'
            changed, count = re.subn(pattern, r'\1return null;', changed)
            if count != 1:
                raise ValueError('Suggestions component changed; no files installed')
            suggestion_files += 1
        if changed != text:
            path.write_text(changed, encoding='utf-8')
    if label_files != 2 or (hide_suggestions and suggestion_files != 1):
        raise ValueError(f'Unsupported frontend anchors: labels={label_files}, suggestions={suggestion_files}')
    for path in (root / 'i18n' / 'zh-CN.json', root / 'i18n' / 'dynamic' / 'zh-CN.json'):
        if path.exists():
            values = json.loads(path.read_text(encoding='utf-8-sig'))
            for key, value in values.items():
                if isinstance(value, str):
                    values[key] = value.replace('Cowork', '协作').replace('Claude Code', 'Claude 编程')
            values.update({'9SUDUxrxDf': '编程', '+MH0VdRCHz': '协作', 'wgBR+rwN23': '协作'})
            path.write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--resources', type=Path, required=True)
    parser.add_argument('--keep-suggestions', action='store_true')
    args = parser.parse_args()
    patch_frontend(args.resources / 'ion-dist', not args.keep_suggestions)
    add_native_catalog(args.resources / 'app.asar', args.resources / 'zh-CN.json')
    print('Supplemental patches verified')
