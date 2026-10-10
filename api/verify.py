"""Read-only integration checks against the running same-origin demo."""
import json
import re
import sys
import urllib.error
import urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8080'
client = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(path):
    return client.open(base + path, timeout=10)

def expect_status(path, status):
    try:
        actual = get(path).status
    except urllib.error.HTTPError as error:
        actual = error.code
    assert actual == status, (path, actual)

summaries = json.load(get('/api/snapshots'))
assert summaries, 'No published snapshots'
snapshot = json.load(get('/api/snapshots/' + summaries[0]['snapshot_id']))
assert snapshot['captured_at'] == summaries[0]['captured_at']
assert snapshot['areas'], 'No shelf areas'
for url in [snapshot['image_url'], snapshot['areas'][0]['crop_url']]:
    response = get(url)
    assert response.headers['Content-Type'].startswith('image/')
    assert response.read(), 'Empty image'
assert json.load(get('/api/snapshots/' + snapshot['snapshot_id'])) == snapshot
expect_status('/api/snapshots/unknown', 404)
expect_status('/assets/unknown', 404)
expect_status('/assets/%2e%2e%2fsnapshots.json', 400)
html = get('/').read().decode()
resources = re.findall(r'(?:src|href)="(/app/[^"]+)"', html)
assert len(resources) >= 2, 'Missing bundled frontend'
for path in resources:
    assert get(path).read(), 'Empty frontend resource'
print(f'PASS: {len(summaries)} snapshots; detail, timestamps, images, frontend, repeated requests and invalid IDs')
