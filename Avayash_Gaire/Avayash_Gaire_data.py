"""Avayash Gaire: reconstruct pre-match features from source snapshots and validate."""
import argparse
from pathlib import Path
from build_dataset import build
from project import ROOT, prepare

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=ROOT / 'data' / 'sources')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data' / 'raw')
    parser.add_argument('--out', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    build(args.sources, args.raw)
    prepare(args.raw, args.out / 'prepared')
    print(f'Prepared and validated the real-source datasets: {args.out.resolve()}')
