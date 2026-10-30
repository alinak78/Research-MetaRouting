"""Package the anonymous source and self-contained new-study artifact."""
from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[3]
PAPER=ROOT/'papers/meta-routing/intellisys2027'
OUT=ROOT/'output/intellisys2027'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=[p for p in PAPER.iterdir() if p.suffix in ('.tex','.cls','.sty','.bst','.bib')]
    source+=list((PAPER/'figures').glob('*.pdf'))
    # Internal feedback/overlap notes are not part of the anonymous source upload.
    with zipfile.ZipFile(OUT/'IntelliSys2027_Anonymous_Source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source):z.write(p,str(p.relative_to(PAPER)))
        z.write(PAPER/'build/main.bbl','main.bbl')
        z.writestr('BUILD.txt','Build main.tex with XeLaTeX and the supplied unmodified svproc class. Times New Roman is required. The PDF is a research draft requiring human-author and related-submission review.\n')
    prefixes=['benchmarks/recovery2027','experiments/meta-routing/intellisys2027','results/meta-routing/intellisys2027']
    files=[]
    for prefix in prefixes:files += [p for p in (ROOT/prefix).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    files += [ROOT/'src/metarouter/recovery_study.py',ROOT/'tests/test_recovery_study.py',PAPER/'STUDY_PROTOCOL.md',PAPER/'README.md']+source
    with zipfile.ZipFile(OUT/'IntelliSys2027_Recovery_Reproducibility.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(files)):z.write(p,str(p.relative_to(ROOT)))
        z.writestr('src/metarouter/__init__.py','"""Self-contained numerical recovery study."""\n')
        z.writestr('requirements.txt','numpy>=1.24\nmatplotlib>=3.8\npytest>=7\n')
        z.writestr('README.md','See papers/meta-routing/intellisys2027/README.md. Supplied traces can be verified with PYTHONPATH=src python experiments/meta-routing/intellisys2027/prepare_paper.py. Test with PYTHONPATH=src python -m pytest -q. Rerunning experiments requires a fresh results directory; preserve the supplied run. The collision extension is exploratory.\n')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.zip')}
    (OUT/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(hashes)
if __name__=='__main__':main()
