"""Kalyan Acharya: rebuild inputs, evaluate both tasks and integrate results."""
import argparse
from pathlib import Path
from build_dataset import build
from project import ROOT, run_all

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-open', action='store_true', help='Save results without opening the browser')
    parser.add_argument('--sources', type=Path, default=ROOT / 'data' / 'sources')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data' / 'raw')
    parser.add_argument('--out', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    build(args.sources, args.raw)
    run_all(args.raw, args.out)
    from review_models import review
    review(args.raw, args.out)
    print(f'Both tasks completed: {args.out.resolve()}')

    from view_results import present
    present(args.out, open_browser=not args.no_open)
