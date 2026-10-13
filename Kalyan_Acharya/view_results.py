"""Readable, offline results viewer. Opening a browser is optional."""
from pathlib import Path
import argparse
import csv
import html
import json
import webbrowser


def table(rows):
    if not rows:
        return '<p>No rows.</p>'
    headings = list(rows[0])
    def cell(value):
        if isinstance(value, float):
            value = f'{value:.4f}'
        return html.escape(str(value))
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+cell(k)+'</th>' for k in headings) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+cell(row[k])+'</td>' for k in headings)+'</tr>' for row in rows)+'</tbody></table></div>'


def read_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def generate(out, tasks=None):
    out = Path(out).resolve()
    tasks = tasks or ['2.1', '2.2']
    sections = []
    for task in tasks:
        folder = out / ('task_' + task.replace('.', '_'))
        metrics = json.loads((folder/'holdout_metrics.json').read_text())
        model = json.loads((folder/'model.json').read_text())
        predictions = read_rows(folder/'holdout_predictions.csv')
        rows = []
        for label in ['linear_regression', 'training_mean']:
            rows.append({'Model':label, **metrics[label]})
        title = 'Goal difference' if task == '2.1' else 'Team goals scored'
        comparison = 'lower' if metrics['linear_regression']['RMSE'] < metrics['training_mean']['RMSE'] else 'higher'
        sections.append(f'<section id="task{task}"><h2>Task {task} — {title}</h2><p>Holdout RMSE is <strong>{comparison}</strong> than the training-mean baseline. These are continuous regression estimates, not guaranteed scores.</p>')
        sections.append(table(rows))
        sections.append('<h3>Regression equation in original units</h3><p class="equation">'+html.escape((folder/'equation.txt').read_text())+'</p>')
        sections.append('<h3>Eight predictors and fitted coefficients</h3>'+table([{'Predictor':f,'Coefficient':b} for f,b in zip(model['features'],model['coefficients'])]))
        sections.append('<h3>All chronological holdout predictions</h3><p>Residual = actual minus predicted. The CSV preserves the full numerical precision.</p>'+table(predictions))
        sections.append('<h3>Forward validation within the training period</h3>'+table(read_rows(folder/'forward_cv_metrics.csv')))
        for image, caption in [('diagnostic_panel.png','Residuals, normal Q–Q plot, holdout predictions and training influence'),('correlations.png','Training correlations'),('predictor_relationships.png','Training predictor relationships'),('target_distribution.png','Training target distribution')]:
            sections.append(f'<figure><a href="{folder.name}/{image}"><img src="{folder.name}/{image}" alt="{html.escape(caption)}"></a><figcaption>{caption}. Click to open at full size.</figcaption></figure>')
        sections.append('<h3>Download or inspect saved files</h3><ul>'+''.join(f'<li><a href="{folder.name}/{name}">{name}</a></li>' for name in ['holdout_predictions.csv','holdout_metrics.json','equation.txt','model.json','coefficient_inference.csv','ols_summary.txt','vif.csv','training_influence.csv','diagnostics.json','split_manifest.csv'])+'</ul></section>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HIT140 Objective 2 Results</title><style>
body{font:16px/1.55 system-ui,sans-serif;max-width:1180px;margin:32px auto;padding:0 22px;color:#172536;background:#fafbfd}h1,h2,h3{line-height:1.2}section{margin:40px 0 60px}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td,th{border:1px solid #ccd4de;padding:9px;text-align:left;white-space:nowrap}th{background:#e8eef6}tr:nth-child(even){background:#f5f7fa}.scroll{overflow:auto}img{max-width:100%;height:auto}figure{margin:28px 0}figcaption{font-size:14px;color:#41516a}.equation{font-family:monospace;overflow-wrap:anywhere;background:#eef2f7;padding:16px}a{color:#1453a3}nav a{margin-right:20px}button{padding:10px 16px;font-size:16px}@media print{button{display:none}section{break-before:page}table{font-size:10px}img{max-height:600px;object-fit:contain}}</style>
<h1>HIT140 Assessment 3 Objective 2</h1><p>Avayash Gaire · Bijendra Karki · Ritesh Panta · Kalyan Acharya</p>
<p>104 match rows and 208 team-match rows. Each model has exactly eight predictors; four underlying concepts are shared. Targets include extra time and exclude penalty shootouts.</p>
<p>These results use retrospective reconstruction from source snapshots. Conservative timing bounds are assumptions, not archived publication timestamps. Both team rows stay together during validation. See the source review and data guide for limitations.</p>
<nav><a href="#task2.1">Goal difference</a><a href="#task2.2">Goals scored</a></nav><p><button onclick="window.print()">Print this results page</button></p>'''+''.join(sections)+'</html>'
    target = out/'RESULTS.html'
    target.write_text(page,encoding='utf-8')
    return target


def present(out, tasks=None, open_browser=True):
    tasks = tasks or ['2.1','2.2']
    page = generate(out, tasks)
    for task in tasks:
        folder = Path(out)/('task_'+task.replace('.','_'))
        metrics = json.loads((folder/'holdout_metrics.json').read_text())
        print('\nTASK '+task+' — CHRONOLOGICAL HOLDOUT')
        for name in ['linear_regression','training_mean']:
            m=metrics[name]
            r2='undefined' if m['R2'] is None else f"{m['R2']:.4f}"
            nrmse='undefined' if m['NRMSE_training_range'] is None else f"{m['NRMSE_training_range']:.4f}"
            print(f"  {name}: MAE={m['MAE']:.4f}  MSE={m['MSE']:.4f}  RMSE={m['RMSE']:.4f}  NRMSE={nrmse}  R2={r2}")
        print('  Equation: '+(folder/'equation.txt').read_text().strip())
        print('  Actual and predicted holdout values:')
        for r in read_rows(folder/'holdout_predictions.csv'):
            label=(r['team']+' vs '+r.get('opponent','')) if 'team' in r else r.get('team_a','')+' vs '+r.get('team_b','')
            print(f"    {r['match_id']} {label}: actual={r['actual']}, predicted={float(r['predicted']):.4f}")
    print('\nOPEN RESULTS: '+str(page))
    if open_browser:
        try:
            if not webbrowser.open(page.as_uri()):
                print('Browser did not open automatically. Double-click RESULTS.html in the output folder.')
        except Exception as exc:
            print(f'Browser could not open ({exc}). Double-click RESULTS.html in the output folder.')
    return page


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'results')
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    present(args.out,open_browser=not args.no_open)
