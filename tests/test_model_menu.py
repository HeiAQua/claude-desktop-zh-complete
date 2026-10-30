import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class ModelMenuTests(unittest.TestCase):
    def test_existing_provider_keeps_background_routes_and_1m(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / 'home'
            local = root / 'local'
            (home / '.cc-switch').mkdir(parents=True)
            library = local / 'Claude-3p/configLibrary'
            library.mkdir(parents=True)
            routes = {f'claude-{role}-5': {'model': 'deepseek-v4-pro', 'supports1m': True}
                      for role in ['sonnet', 'opus', 'haiku', 'fable']}
            db = home / '.cc-switch/cc-switch.db'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE providers(id,app_type,is_current,settings_config,meta)')
                c.execute('INSERT INTO providers VALUES(?,?,?,?,?)', ('test', 'claude-desktop', 1,
                    json.dumps({'env': {'ANTHROPIC_BASE_URL': 'https://api.deepseek.com/anthropic'}}),
                    json.dumps({'claudeDesktopModelRoutes': routes})))
            c.close()
            profile = {'inferenceProvider': 'gateway', 'inferenceGatewayBaseUrl': 'http://127.0.0.1:15721',
                       'inferenceModels': [{'name': name, 'supports1m': True} for name in routes]}
            path = library / 'local.json'
            path.write_text(json.dumps(profile), encoding='utf-8')
            env = {**os.environ, 'USERPROFILE': str(home), 'LOCALAPPDATA': str(local)}
            command = [sys.executable, str(Path(__file__).parents[1] / 'scripts/model_menu.py'),
                       '--update-flash', '--simplify-menu']
            subprocess.run(command, env=env, check=True, capture_output=True)
            models = json.loads(path.read_text(encoding='utf-8'))['inferenceModels']
            self.assertEqual(len(models), 2)
            self.assertTrue(all(m['supports1m'] for m in models))
            with sqlite3.connect(db) as c:
                meta = json.loads(c.execute('SELECT meta FROM providers').fetchone()[0])
            c.close()
            self.assertEqual(len(meta['claudeDesktopModelRoutes']), 4)
            self.assertEqual(meta['claudeDesktopModelRoutes']['claude-haiku-5']['model'], 'deepseek-flash')


if __name__ == '__main__':
    unittest.main()
