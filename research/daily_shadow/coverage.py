"""Registry/source-gate dry-run report, never a record of actual issuance."""
import csv,io,json
from .artifacts import OUT,load_artifact

def report():
 index=json.loads((OUT/'model-index.json').read_text());source=json.loads((OUT/'source-inspection.json').read_text());rows=[]
 for entry in index['models']:
  m=load_artifact(OUT/entry['file']);s=m['series']
  rows.append(dict(**s,model=m['name'],version=m['version'],historical_n=m['count_bank']['n'],historical_last_maturity=m['count_bank']['last_maturity'],code_supported=True,training_source_qualified=m['training_source_qualified'],model_qualified=m['qualified'],calibration_validated=m['calibrated'],live_provider_qualified=False,status='STATUS_BLOCKED',probability_raw=None,probability_calibrated=None,reason='NO_VERIFIED_LIVE_PUBLICATION_ACTION_LICENSE_CONTRACT; TRAINING_HISTORY_NOT_PIT; MODEL_UNQUALIFIED'))
 out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows);(OUT/'series-coverage.csv').write_text(out.getvalue())
 summary=dict(status='NOT RUNNING',mode='OFFLINE_REGISTRY_AND_QUALIFICATION_DRY_RUN',not_actual_issuance=True,requested_series=len(rows),numerical_artifacts=len(rows),genuine_live_probabilities=0,null_probabilities=len(rows),models={'HIST':sum(x['model']=='HIST' for x in rows),'REGIME':sum(x['model']=='REGIME' for x in rows)},provider_blocker=source['source_qualification'],calibrated_models=0,source_timestamps_invented=False,prospective_records_exist=False)
 (OUT/'dry-run-coverage.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return summary
if __name__=='__main__':report()
