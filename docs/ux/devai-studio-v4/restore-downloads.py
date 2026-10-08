#!/usr/bin/env python3
"""Restore the exact delivered UX archive and self-contained gallery; no dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def restore(output_dir=None):
    source = Path(__file__).resolve().parent / 'downloads'
    target = Path(output_dir) if output_dir else source / 'restored'
    target.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / 'manifest.json').read_text())
    for entry in manifest['files']:
        digest = hashlib.sha256()
        total = 0
        with tempfile.NamedTemporaryFile(dir=target, delete=False) as output:
            temporary = Path(output.name)
            try:
                for part in entry['parts']:
                    data = (source / part['name']).read_bytes()
                    if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
                        raise ValueError('Missing or corrupt part: ' + part['name'])
                    output.write(data)
                    digest.update(data)
                    total += len(data)
                if total != entry['bytes'] or digest.hexdigest() != entry['sha256']:
                    raise ValueError('Restored checksum mismatch: ' + entry['name'])
                output.flush()
                os.fsync(output.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        destination = target / entry['name']
        temporary.replace(destination)
        print('Restored and verified: ' + str(destination))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    restore(parser.parse_args().output_dir)
