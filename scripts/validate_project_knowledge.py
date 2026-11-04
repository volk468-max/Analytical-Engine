#!/usr/bin/env python3
"""Read-only knowledge checks. Standard library only; never updates files or PRs."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
K = Path('docs/alpha-os-knowledge')
SHA = re.compile(r'^[0-9a-f]{40}$')
REPO = 'volk468-max/Analytical-Engine'
REQUIRED = ('README PROJECT_STATUS ARCHITECTURE DECISIONS RESEARCH_INDEX DATA_INVENTORY '
            'RISK_MODELS BACKTEST_RESULTS OPEN_QUESTIONS NEXT_STEPS CHANGELOG QUALITY').split()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)


def api(path):
    # Fixed GitHub host. Token is sent only here; never print response bodies or credentials.
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'alpha-os-knowledge-ci'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + path,
                                     headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f'GitHub API {path}: HTTP {exc.code}') from None


def validate(online=False, base_ref=None, fetch=api):
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    def read(path):
        return json.loads((ROOT / path).read_text())
    for name in REQUIRED:
        check((ROOT / K / (name + '.md')).is_file(), f'missing {name}.md')
    m = read(K / 'research.json')
    s = read(K / 'status.json')
    check(m['schema_version'] == 1 and m['repository'] == REPO, 'invalid schema/repository')
    check(bool(SHA.fullmatch(m['baseline_sha'])), 'invalid baseline SHA')
    check(s['baseline_sha'] == m['baseline_sha'], 'baseline status mismatch')
    check(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', s['checked_at'])), 'invalid checked_at')
    records = m['records']
    ids = [r['id'] for r in records]
    check(len(ids) == len(set(ids)), 'duplicate research ID')
    latest = {}
    commits = {m['baseline_sha']}
    for r in records:
        rid = r['id']
        check(bool(re.fullmatch(r'R\d{2,}-v[1-9]\d*', rid)), f'invalid ID {rid}')
        for field in ('title', 'branch', 'goal', 'hypothesis', 'data_period', 'method',
                      'results', 'limitations', 'decisions', 'open_questions', 'sources'):
            check(bool(r.get(field)), f'{rid}: missing {field}')
        for field in ('sha', 'base_sha', 'report_blob'):
            check(bool(SHA.fullmatch(r[field])), f'{rid}: invalid {field}')
        commits.update([r['sha'], r['base_sha']])
        pr_url = f'https://github.com/{REPO}/pull/{r["pr"]}'
        report_url = f'https://github.com/{REPO}/blob/{r["sha"]}/{r["report_path"]}'
        check(pr_url in r['sources'] and report_url in r['sources'], f'{rid}: pinned sources missing')
        check((ROOT/K/'research'/f'{rid}.md').is_file(), f'{rid}: card missing')
        version = int(rid.rsplit('-v', 1)[1])
        if r['pr'] not in latest or version > latest[r['pr']][0]:
            latest[r['pr']] = (version, r)
    states = {p['number']: p for p in s['pull_requests']}
    check(len(states) == len(s['pull_requests']), 'duplicate status PR')
    check(set(states) == set(latest), 'status/catalogue PR mismatch')
    status_text = (ROOT/K/'PROJECT_STATUS.md').read_text()
    for n, (_, r) in latest.items():
        st = states.get(n, {})
        check(st.get('head_sha') == r['sha'], f'PR{n}: latest research/status head mismatch')
        check(st.get('state') in ('open', 'closed'), f'PR{n}: invalid state')
        check(isinstance(st.get('draft'), bool) and isinstance(st.get('merged'), bool), f'PR{n}: nonboolean status')
        check(not st.get('merged') or st.get('state') == 'closed', f'PR{n}: merged/open contradiction')
        row = f'| [#{n}](https://github.com/{REPO}/pull/{n}) | {st.get("state")} | {str(st.get("draft")).lower()} | {str(st.get("merged")).lower()} |'
        check(row in status_text, f'PR{n}: PROJECT_STATUS table mismatch')
    # Resolve local Markdown links and PR/commit/blob references anywhere in knowledge.
    prs = set(states)
    object_types = read(K / 'git-object-types.json')
    mentioned_objects = set()
    for path in sorted((ROOT/K).rglob('*')):
        if path.suffix not in ('.md', '.json'):
            continue
        content = path.read_text()
        if path.name != 'git-object-types.json':
            mentioned_objects.update(re.findall(r'(?<![a-f0-9])[a-f0-9]{40}(?![a-f0-9])', content))
        for link in re.findall(r'\]\(([^)]+)\)', content):
            if not re.match(r'https?://|#', link):
                target = (path.parent / urllib.parse.unquote(link.split('#')[0])).resolve()
                check(target.is_relative_to(ROOT) and target.exists(), f'{path.name}: broken local link {link}')
        for n in re.findall(r'https://github.com/'+re.escape(REPO)+r'/pull/(\d+)', content):
            prs.add(int(n))
        for sha in re.findall(r'https://github.com/'+re.escape(REPO)+r'/(?:commit|blob)/([^/\s)"`]+)', content):
            check(bool(SHA.fullmatch(sha)), f'{path.name}: unpinned/invalid source ref')
            commits.add(sha)
        # Deliberately limited pattern scan; human review remains mandatory.
        secret_patterns = [r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
                           r'\bgh[pousr]_[A-Za-z0-9]{20,}\b', r'\bgithub_pat_[A-Za-z0-9_]{20,}\b',
                           r'\bAKIA[A-Z0-9]{16}\b', r'(?i)Bearer\s+[A-Za-z0-9_.-]{20,}',
                           r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}']
        for pattern in secret_patterns:
            check(not re.search(pattern, content), f'{path.name}: possible secret/personal data; review required')
    for sha in mentioned_objects:
        check(object_types.get(sha) in ('commit', 'tree', 'blob'), f'unclassified Git SHA: {sha}')
    for sha, kind in object_types.items():
        check(bool(SHA.fullmatch(sha)) and kind in ('commit', 'tree', 'blob'), 'invalid Git object registry entry')
    if base_ref:
        check(bool(SHA.fullmatch(base_ref)), 'base-ref must be full SHA')
        if SHA.fullmatch(base_ref):
            old_paths = set(git('ls-tree', '-r', '--name-only', base_ref, str(K)).splitlines())
            for path in old_paths:
                if '/research/' in path or '/sources/' in path:
                    old = git('show', f'{base_ref}:{path}')
                    check((ROOT/path).exists() and (ROOT/path).read_text() == old,
                          f'append-only historical source/card changed: {path}')
            if str(K/'research.json') in old_paths:
                old = json.loads(git('show', f'{base_ref}:{K}/research.json'))
                current = {r['id']: r for r in records}
                for r in old['records']:
                    check(current.get(r['id']) == r, f'historical record changed: {r["id"]}')
            if str(K/'CHANGELOG.md') in old_paths:
                old = git('show', f'{base_ref}:{K}/CHANGELOG.md')
                check((ROOT/K/'CHANGELOG.md').read_text().startswith(old), 'CHANGELOG is append-only')
            changed = git('diff', '--name-only', base_ref, 'HEAD').splitlines()
            if any(not p.startswith('.github/') for p in changed):
                for required in ('RESEARCH_INDEX.md', 'PROJECT_STATUS.md', 'NEXT_STEPS.md', 'CHANGELOG.md'):
                    check(str(K/required) in changed, f'PR freshness: review/update {required}')
    if online:
        for n in sorted(prs):
            p = fetch(f'pulls/{n}')
            if n in states:
                st = states[n]
                for field in ('state', 'draft', 'merged'):
                    check(p[field] == st[field], f'PR{n}: stale {field}; refresh knowledge')
                check(p['head']['sha'] == st['head_sha'], f'PR{n}: stale head; add new research version')
        main = fetch('branches/main')
        check(main['commit']['sha'] == m['baseline_sha'], 'main advanced: review code/data/status and update baseline')
        for sha in sorted(commits):
            check(fetch('commits/'+sha)['sha'] == sha, f'commit does not resolve: {sha}')
        for sha, kind in object_types.items():
            check(fetch(f'git/{kind}s/{sha}')['sha'] == sha, f'Git {kind} does not resolve: {sha}')
        for r in records:
            path = urllib.parse.quote(r['report_path'], safe='/')
            result = fetch(f'contents/{path}?ref={r["sha"]}')
            check(result['sha'] == r['report_blob'], f'{r["id"]}: report blob mismatch')
    return errors


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--base-ref')
    args = parser.parse_args()
    try:
        errors = validate(args.online, args.base_ref)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Knowledge validation could not complete: {type(exc).__name__}')
        return 1
    for error in errors:
        print('ERROR:', error)
    if not errors:
        print('Knowledge validation passed' + (' (including live GitHub)' if args.online else ' (offline only)'))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
