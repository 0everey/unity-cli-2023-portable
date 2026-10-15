"""Install/uninstall the bundled Unity 2023.1/2023.2 Editor bridge in a selected project."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
PACKAGE = 'com.akiojin.unity-cli-bridge'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.sha256(stream.read()).hexdigest()

def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)

def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def no_links(path):
    path = Path(path)
    for parent in [path, *path.parents]:
        if parent.exists() and parent.lstat().st_file_attributes & 0x400:
            raise ValueError('Directory links are not installation targets: ' + str(parent))

def validate(project):
    no_links(project)
    for relative in ['Assets', 'Packages', 'Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt']:
        p = project / relative
        if not p.exists():
            raise ValueError('Missing Unity project path: ' + str(p))
        no_links(p)
    version = (project / 'ProjectSettings/ProjectVersion.txt').read_text(encoding='utf-8-sig')
    if not re.search(r'^m_EditorVersion: 2023\.[12]\.\S+', version, re.M):
        raise ValueError('This distribution targets Unity 2023.1/2023.2. Use its matching Editor.')
    script = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-CimInstance Win32_Process -Filter \"Name='Unity.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    query = subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-Command', script],
                           capture_output=True, encoding='utf-8', errors='replace')
    if query.returncode:
        raise RuntimeError('Cannot inspect running Unity Editors: ' + query.stderr)
    editors = json.loads(query.stdout.lstrip('\ufeff')) if query.stdout.strip() else []
    if isinstance(editors, dict):
        editors = [editors]
    target = str(project).replace('\\', '/').casefold()
    for editor in editors:
        if target in (editor.get('CommandLine') or '').replace('\\', '/').casefold():
            raise RuntimeError('Close the selected Unity Editor normally before changing the bridge.')
    if (project / 'Temp/UnityLockfile').exists():
        raise RuntimeError('UnityLockfile exists. Close the target Editor; diagnose a stale lock before retrying.')
    if (project / '.pvzmc-main-write-lease.json').exists():
        raise RuntimeError('This project has an active writer lease. Use its existing coordination workflow.')
    state = project / '.unity-cli-portable'
    no_links(state)
    return read_json(project / 'Packages/manifest.json')

def verify_bundle():
    manifest = read_json(ROOT / 'FILES.sha256.json')
    for relative, expected in manifest.items():
        path = ROOT / relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('Invalid distribution integrity path')
        no_links(path)
        if not path.is_file() or sha(path) != expected:
            raise ValueError('Distribution content changed: ' + relative)
    return manifest

def install(project, dry_run=False):
    verify_bundle()
    manifest = validate(project)
    dependencies = manifest.get('dependencies')
    if not isinstance(dependencies, dict):
        raise ValueError('Project manifest must contain a dependencies object')
    target = project / 'Packages' / PACKAGE
    if target.exists() or PACKAGE in dependencies:
        raise RuntimeError('A Bridge is already installed/configured; retain it. Uninstall or reconcile its owner first.')
    state = project / '.unity-cli-portable'
    receipt = state / 'installation.json'
    if receipt.exists():
        raise RuntimeError('An earlier installation record exists; inspect/uninstall it first.')
    source = ROOT / 'package' / PACKAGE
    minimum = read_json(source / 'package.json')['dependencies']
    notes = []
    for name, required in minimum.items():
        current = dependencies.get(name)
        if current and current != required:
            if not re.fullmatch(r'\d+\.\d+\.\d+', current):
                raise ValueError('Custom dependency source requires project-specific reconciliation: ' + name)
            if tuple(map(int, current.split('.'))) < tuple(map(int, required.split('.'))):
                raise ValueError(name + ' requires at least ' + required + '; existing ' + current + ' is not changed automatically.')
            notes.append(name + ': retaining ' + current + '; tested baseline is ' + required)
    files = sorted(p for p in source.rglob('*') if p.is_file())
    for p in source.rglob('*'):
        no_links(p)
    facts = {'project': str(project), 'unity': '2023.1/2023.2', 'bridge': '0.18.1',
             'adaptation': 'unity2023-portable-r1', 'package_files': len(files),
             'will_add': 'Packages/' + PACKAGE, 'will_edit': 'Packages/manifest.json',
             'input_settings': 'preserved; virtual input requires Input System or Both',
             'dependency_notes': notes, 'first_import_requires_unity_package_registry': True}
    if dry_run:
        return dict(facts, dry_run=True)
    state.mkdir(exist_ok=True)
    token = uuid.uuid4().hex
    backup = state / ('backup-' + token)
    backup.mkdir()
    manifest_path = project / 'Packages/manifest.json'
    before = sha(manifest_path)
    shutil.copy2(manifest_path, backup / 'manifest.json')
    if (project / 'Packages/packages-lock.json').is_file():
        shutil.copy2(project / 'Packages/packages-lock.json', backup / 'packages-lock.json')
    stage = project / 'Packages' / ('.unity-cli-stage-' + token)
    temp = project / 'Packages' / ('.unity-cli-manifest-' + token + '.tmp')
    record = dict(facts, state='copying', before_manifest_sha256=before, backup=str(backup),
                  staging=str(stage), created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                  package_hashes={p.relative_to(source).as_posix(): sha(p) for p in files})
    write_json(receipt, record)
    committed = False
    published_package = False
    try:
        shutil.copytree(source, stage)
        for relative, expected in record['package_hashes'].items():
            if sha(stage / relative) != expected:
                raise RuntimeError('Copied package did not match: ' + relative)
        validate(project)
        if sha(manifest_path) != before or target.exists():
            raise RuntimeError('Project changed during installation; preserving current project state.')
        os.rename(stage, target)
        published_package = True
        manifest['dependencies'][PACKAGE] = 'file:' + PACKAGE
        write_json(temp, manifest)
        os.replace(temp, manifest_path)
        committed = True
        record.update(state='installed', installed_manifest_sha256=sha(manifest_path))
        write_json(receipt, record)
    except Exception:
        # Nothing is deleted on failure. Before manifest publication, retire the copied prefix.
        if not committed:
            prefix = stage if stage.exists() else target if published_package else None
            if prefix is not None and prefix.exists():
                os.rename(prefix, state / ('failed-copy-' + token))
            record['state'] = 'failed-before-publication'
            write_json(receipt, record)
        raise
    return dict(facts, installed=True, receipt=str(receipt), next='Open this project using its Unity 2023.1/2023.2 Editor; wait for package resolution/compilation.')

def uninstall(project):
    manifest = validate(project)
    state = project / '.unity-cli-portable'
    receipt = state / 'installation.json'
    record = read_json(receipt)
    if Path(record['project']) != project:
        raise ValueError('Installation record belongs to another project')
    dependency = manifest.get('dependencies', {}).get(PACKAGE)
    if dependency not in (None, 'file:' + PACKAGE):
        raise ValueError('Bridge dependency now belongs to another source; preserving it.')
    target = project / 'Packages' / PACKAGE
    no_links(target)
    token = uuid.uuid4().hex
    retired = state / ('retired-' + token)
    manifest_path = project / 'Packages/manifest.json'
    temp = project / 'Packages' / ('.unity-cli-uninstall-' + token + '.tmp')
    shutil.copy2(manifest_path, state / ('manifest-before-uninstall-' + token + '.json'))
    before = sha(manifest_path)
    if target.exists():
        os.rename(target, retired)
    try:
        manifest.get('dependencies', {}).pop(PACKAGE, None)
        write_json(temp, manifest)
        if sha(manifest_path) != before:
            raise RuntimeError('Manifest changed during uninstallation')
        os.replace(temp, manifest_path)
    except Exception:
        if retired.exists() and not target.exists():
            os.rename(retired, target)
        raise
    record.update(state='uninstalled', retired_package=str(retired))
    write_json(state / ('uninstalled-' + token + '.json'), record)
    os.rename(receipt, state / ('installation-' + token + '.json'))
    return {'uninstalled': True, 'project': str(project), 'retired_package': str(retired),
            'later_manifest_changes': 'preserved', 'packages_lock': 'retained; Unity resolves it at next import'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall', 'verify'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.action == 'verify':
        print(json.dumps({'verified': True, 'files': len(verify_bundle())})); return 0
    if args.project is None:
        parser.error('--project is required')
    no_links(args.project.absolute())
    project = args.project.resolve()
    result = install(project, args.dry_run) if args.action == 'install' else uninstall(project)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(json.dumps({'success': False, 'error': type(exc).__name__, 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
