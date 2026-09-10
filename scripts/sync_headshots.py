"""Download ID-matched, transparent source portraits; never synthesize player photos."""
import concurrent.futures
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'dashboard-web'


def main():
    (ROOT / 'assets').mkdir(exist_ok=True)
    for name, url in {
        'roster2026': 'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2026.csv',
        'players': 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',
    }.items():
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        records = list(csv.DictReader(io.StringIO(response.text)))
        (ROOT / f'assets/{name}.json').write_text(json.dumps(records), encoding='utf-8')
    data = requests.get('http://localhost:8054/api/data', timeout=120).json()
    identities = {r['player_id']: r['player_name'] for key, rows in data.items()
                  if key.startswith('player_') for r in rows}
    rosters = {r['gsis_id']: r for r in json.loads((ROOT / 'assets/roster2026.json').read_text())}
    players = {r['gsis_id']: r for r in json.loads((ROOT / 'assets/players.json').read_text())}
    folder = ROOT / 'assets/headshots'
    folder.mkdir(parents=True, exist_ok=True)

    def download(item):
        pid, name = item
        roster, player = rosters.get(pid, {}), players.get(pid, {})
        candidates = [(roster.get('headshot_url'), '2026 roster'),
                      (player.get('headshot'), 'Latest player reference')]
        if player.get('espn_id'):
            candidates.append((f"https://a.espncdn.com/i/headshots/nfl/players/full/{player['espn_id']}.png", 'Latest ESPN headshot'))
        record = {'name': player.get('display_name') or name, 'roster_2026': bool(roster),
                  'team_2026': roster.get('team'), 'photo': None, 'status': 'unavailable'}
        for url, source in candidates:
            if not url or url == 'NA':
                continue
            if 'static.www.nfl.com/image/upload/' in url:
                url = url.replace('f_auto,q_auto', 'f_png,w_256,c_limit')
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                with Image.open(io.BytesIO(response.content)) as im:
                    alpha = im.convert('RGBA').getchannel('A')
                    low, high = alpha.getextrema()
                    if low != 0 or high != 255:
                        continue
                    # Inspect transparency only. Save source bytes without image edits.
                    if im.format != 'PNG':
                        continue
                (folder / f'{pid}.png').write_bytes(response.content)
                record.update(photo=f'/assets/headshots/{pid}.png', status='available',
                              source=source, source_url=url, transparent=True)
                break
            except (requests.RequestException, OSError, ValueError):
                continue
        return pid, record

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for i, (pid, record) in enumerate(pool.map(download, identities.items()), 1):
            results[pid] = record
            if i % 100 == 0:
                print(f'Checked {i}/{len(identities)}', flush=True)
    payload = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'players': results}
    (ROOT / 'assets/headshots.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'total': len(results), 'available': sum(r['status'] == 'available' for r in results.values()),
                      'from_2026_roster': sum(r.get('source') == '2026 roster' for r in results.values()),
                      'unavailable': [r['name'] for r in results.values() if r['status'] != 'available']}), flush=True)


if __name__ == '__main__':
    main()
