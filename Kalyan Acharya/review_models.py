"""Training-only influence sensitivity; never replace the main model automatically."""
from pathlib import Path
import pandas as pd
from project import ROOT, ingest, split_matches, fit_pipeline, FEATURES, TARGETS

def review(raw=ROOT/'data/raw', out=ROOT/'results'):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    tables,_=ingest(raw)
    train,_=split_matches(tables['2.1'])
    if '760429' not in set(train.match_id):
        raise ValueError('Flagged source fixture 760429 is not in training; inspect influence before choosing a sensitivity case.')
    f=FEATURES['2.1']; y=TARGETS['2.1']
    full=fit_pipeline(train,f,y)
    reduced=fit_pipeline(train[train.match_id.ne('760429')],f,y)
    a=full[-1].coef_/full[1].scale_; b=reduced[-1].coef_/reduced[1].scale_
    table=pd.DataFrame({'predictor':f,'all_training_coefficient':a,'excluding_760429_coefficient':b,'change':b-a})
    table.to_csv(out/'training_coefficient_sensitivity.csv',index=False)
    print(table.to_string(index=False))
    print('Sensitivity diagnostic only. Main model and held-out predictions are unchanged.')
    return table

if __name__ == '__main__':
    review()
