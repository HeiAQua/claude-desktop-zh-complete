"""Optional existing official-DeepSeek profile maintenance; never reads out secrets."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-flash', action='store_true')
    parser.add_argument('--simplify-menu', action='store_true')
    args = parser.parse_args()
    if not (args.update_flash or args.simplify_menu):
        parser.error('Choose --update-flash and/or --simplify-menu; close Claude and CC Switch first')
    home = Path(os.environ['USERPROFILE'])
    local = Path(os.environ['LOCALAPPDATA'])
    db = home / '.cc-switch/cc-switch.db'
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = local / 'ClaudeZhComplete' / 'model-backups' / stamp
    backup.mkdir(parents=True)
    with sqlite3.connect(db.as_uri() + '?mode=rw', uri=True) as conn:
        rows = conn.execute("SELECT id,settings_config,meta FROM providers WHERE app_type='claude-desktop' AND is_current=1").fetchall()
        if len(rows) != 1:
            raise ValueError('Select one existing DeepSeek Claude Desktop provider in CC Switch first')
        provider, config, metadata = rows[0]
        endpoint = json.loads(config).get('env', {}).get('ANTHROPIC_BASE_URL', '').rstrip('/')
        if endpoint != 'https://api.deepseek.com/anthropic':
            raise ValueError('This helper only supports the official DeepSeek Anthropic endpoint')
        meta = json.loads(metadata)
        routes = meta.get('claudeDesktopModelRoutes', {})
        flash = [r for key, r in routes.items() if 'haiku' in key]
        if len(flash) != 1:
            raise ValueError('Expected exactly one Haiku/Flash route')
        if args.update_flash:
            # Save ONLY the route metadata, never API keys or the whole credentials database.
            (backup / 'routes-before.json').write_text(metadata, encoding='utf-8')
            flash[0].update(model='deepseek-flash', labelOverride='DeepSeek V4.1 Flash')
            conn.execute("UPDATE providers SET meta=? WHERE id=? AND app_type='claude-desktop'",
                         (json.dumps(meta, ensure_ascii=False), provider))
    libraries = [local / 'Claude-3p/configLibrary']
    for library in libraries:
        for path in library.glob('*.json'):
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            models = data.get('inferenceModels')
            if not isinstance(models, list):
                continue
            # Only touch a CC Switch localhost profile with known role IDs.
            url = data.get('inferenceGatewayBaseUrl', '')
            if not isinstance(url, str) or not url.rstrip('/').startswith('http://127.0.0.1:15721'):
                continue
            updated = []
            for model in models:
                name = model.get('name', '')
                if args.update_flash and 'haiku' in name:
                    model['labelOverride'] = 'DeepSeek V4.1 Flash'
                if args.simplify_menu and not ('haiku' in name or 'opus' in name):
                    continue
                if args.simplify_menu and 'opus' in name:
                    model['labelOverride'] = 'DeepSeek V4 Pro'
                updated.append(model)
            if args.simplify_menu and (len(updated) != 2 or not all(m.get('supports1m') for m in updated)):
                raise ValueError('Expected two known roles with 1M enabled; profile left unchanged')
            # Backup includes profile connection material; stays local, NEVER commit it.
            shutil.copy2(path, backup / path.name)
            data['inferenceModels'] = updated
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Done. Restart CC Switch and Claude. Backups stay in local ClaudeZhComplete/model-backups.')


if __name__ == '__main__':
    main()
