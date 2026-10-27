"""Build an installable ZIP containing only the integration's runtime files."""

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = ROOT / 'custom_components/boocue'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                archive.write(path, 'boocue/' + path.relative_to(source).as_posix())
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(args.output.suffix + '.sha256').write_text(f'{digest}  {args.output.name}\n')
    print(f'{args.output} · {args.output.stat().st_size} bytes · SHA-256 {digest}')


if __name__ == '__main__':
    main()
