"""NFL Analytics local dashboard. SELECT-only access; ten-minute shared cache."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

from dotenv import load_dotenv
import snowflake.connector

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')
TABLES = ['team_rankings', 'team_game_results', 'player_passing_leaders',
          'player_rushing_leaders', 'player_receiving_leaders', 'player_defense_leaders',
          'player_kicking_leaders', 'player_passing_by_week', 'player_rushing_by_week',
          'player_receiving_by_week']
lock = threading.Lock()
cache = None
expires = 0


def serialize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(type(value).__name__)


def read_data():
    global cache, expires
    with lock:
        if cache is not None and time.monotonic() < expires:
            return cache
        conn = snowflake.connector.connect(
            account=os.environ['SNOWFLAKE_ACCOUNT'], user=os.environ['SNOWFLAKE_USER'],
            password=os.environ['SNOWFLAKE_PASSWORD'], warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
            database=os.environ['SNOWFLAKE_DATABASE'], schema='marts',
            role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'), login_timeout=20, network_timeout=30,
            session_parameters={'STATEMENT_TIMEOUT_IN_SECONDS': 45, 'QUERY_TAG': 'gridiron_dashboard'})
        try:
            with conn.cursor() as cur:
                def query(sql):
                    cur.execute(sql)
                    cols = [c[0].lower() for c in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
                data = {table: query('select * from marts.' + table) for table in TABLES}
                data['coverage'] = query('select season, count(*) as plays, count(distinct game_id) as games, max(game_date) as latest_game from staging.stg_pbp group by season')
                data['game_types'] = query('select season, game_type, count(*) as games from staging.stg_schedules group by season, game_type')
            data['retrieved_at'] = datetime.now(timezone.utc).isoformat()
            data['cache_seconds'] = 600
            result = ROOT.parent / 'dbt_project/target/run_results.json'
            data['validation'] = None
            if result.exists():
                artifact = json.loads(result.read_text(encoding='utf-8'))
                tests = [r for r in artifact.get('results', []) if r.get('unique_id', '').startswith('test.')]
                if tests:
                    data['validation'] = {'passed': sum(r['status'] == 'pass' for r in tests), 'total': len(tests), 'at': artifact['metadata']['generated_at']}
            cache = json.dumps(data, default=serialize, allow_nan=False).encode()
            expires = time.monotonic() + 600
            return cache
        finally:
            conn.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                 '/styles.css': ('styles.css', 'text/css'), '/favicon.svg': ('favicon.svg', 'image/svg+xml'),
                 '/assets/headshots.json': ('assets/headshots.json', 'application/json')}
        if re.fullmatch(r'/assets/headshots/00-\d{7}\.png', path):
            asset = ROOT / path.lstrip('/')
            if asset.is_file():
                self.respond(200, asset.read_bytes(), 'image/png')
            else:
                self.respond(404, b'Not found', 'text/plain')
            return
        if path == '/api/data':
            try:
                self.respond(200, read_data(), 'application/json')
            except Exception:
                self.respond(503, b'{"error":"Unable to read the Snowflake analytics. Check your local connection and warehouse configuration, then retry."}', 'application/json')
        elif path in files:
            name, mime = files[path]
            asset = ROOT / name
            if asset.is_file():
                self.respond(200, asset.read_bytes(), mime)
            else:
                self.respond(404, b'Not found', 'text/plain')
        else:
            self.respond(404, b'Not found', 'text/plain')

    def respond(self, status, body, mime):
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8054)
    args = parser.parse_args()
    print(f'NFL Analytics: http://localhost:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
