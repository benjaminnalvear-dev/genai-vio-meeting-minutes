"""CLI de D3: corre condiciones sobre reuniones, guarda resultados y trazas, y arma la tabla.

    python -m agentes.correr --reunion M01 --en-vivo                 # sistema completo, conversación en pantalla
    python -m agentes.correr --condicion todas                      # las 7 condiciones en las 10 reuniones de test
    python -m agentes.correr --tabla                                # solo evaluar lo ya guardado
"""
import argparse
import json
import sys
from pathlib import Path

from . import d2
from .datos import RAIZ, ZIP_DEFECTO, load_split
from .evaluador import evaluate
from .grafo import CONDICIONES, correr

REFERENCIAS = ('baseline', 'structured', 'd2_combined')
TODAS = REFERENCIAS + CONDICIONES


def guardar(path, valor):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(valor, ensure_ascii=False, indent=2), encoding='utf-8')


def correr_condicion(condicion, mid, tr, salida, en_vivo):
    path = salida / 'resultados' / condicion / f'{mid}.json'
    if path.exists():
        print(f'  {condicion} {mid}: reutiliza {path.relative_to(salida)}')
        return json.loads(path.read_text(encoding='utf-8'))
    if condicion == 'baseline':
        res = d2.run_baseline(tr)
    elif condicion == 'structured':
        res = d2.run_structured(tr)
    elif condicion == 'd2_combined':
        res = d2.run_combined(tr, correr_condicion('structured', mid, tr, salida, False))
    else:
        if en_vivo:
            print(f'\n=== {mid} · {condicion} ===')
        res, traza = correr(tr, condicion, en_vivo)
        traza.guardar(salida / 'trazas' / condicion / f'{mid}.jsonl')
    guardar(path, res)
    print(f"  {condicion} {mid}: {res['seconds']} s" + (f", {res['llamadas']} llamadas" if 'llamadas' in res else ''))
    return res


def tabla(condiciones, mids, transcripts, gold, salida):
    filas = []
    for c in condiciones:
        outs = {}
        for mid in mids:
            p = salida / 'resultados' / c / f'{mid}.json'
            if p.exists():
                out = json.loads(p.read_text(encoding='utf-8'))
                if c == 'd2_combined':  # costo real: borrador + corrección
                    out['seconds'] = out.get('seconds_con_borrador', out['seconds'])
                outs[mid] = out
        if len(outs) < len(mids):
            print(f'  {c}: faltan {len(mids) - len(outs)} reuniones, se omite de la tabla')
            continue
        filas.append(evaluate('baseline' if c == 'baseline' else c, outs, transcripts, gold))
    guardar(salida / 'resumen.json', filas)
    enc = '| Condición | JSON válido | F1 decisiones | F1 tareas | Estado | Plazo | Responsable | Evidencia existe | Llamadas/reunión | Tiempo total |'
    lin = [enc, '|' + '---|' * 10]
    for f in filas:
        llam = [m['llamadas'] for m in f['per_meeting'] if m.get('llamadas')]
        llam = f'{sum(llam) / len(llam):.1f}' if llam else ('2' if f['arm'] == 'd2_combined' else '1')
        lin.append(f"| {f['arm']} | {f['schema_valid']} | {f['decisions']['f1']:.3f} | {f['tasks']['f1']:.3f} | "
                   f"{f['state_accuracy_matched']} | {f['deadline_accuracy_matched']} | "
                   f"{f['assignee_accuracy_matched']} | {f['evidence_id_exists']} | {llam} | {f['seconds_total']} s |")
    md = '\n'.join(lin)
    (salida / 'tabla.md').write_text(md + '\n', encoding='utf-8')
    print(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--condicion', action='append', choices=TODAS + ('todas',),
                    help='repetible; por defecto full')
    ap.add_argument('--reunion', action='append', help='repetible; por defecto todas las del split')
    ap.add_argument('--split', default='test', choices=('train', 'validation', 'test'))
    ap.add_argument('--datos', default=str(ZIP_DEFECTO), help='ruta a Fine Tuning.zip')
    ap.add_argument('--salida', default=None, help='carpeta de salida (por defecto resultados/d3/<split>)')
    ap.add_argument('--en-vivo', action='store_true', help='imprime los mensajes entre agentes')
    ap.add_argument('--tabla', action='store_true', help='no corre nada: evalúa lo guardado')
    a = ap.parse_args(argv)

    transcripts, gold = load_split(a.split, a.datos)
    mids = a.reunion or sorted(transcripts)
    faltan = [m for m in mids if m not in transcripts]
    if faltan:
        sys.exit(f'reuniones inexistentes en {a.split}: {faltan}')
    if a.condicion is None:
        condiciones = list(TODAS) if a.tabla else ['full']
    else:
        condiciones = list(TODAS) if 'todas' in a.condicion else a.condicion
    salida = Path(a.salida) if a.salida else RAIZ / 'resultados' / 'd3' / a.split

    if not a.tabla:
        for i, mid in enumerate(mids, 1):
            print(f'[{i}/{len(mids)}] {mid}')
            for c in condiciones:
                correr_condicion(c, mid, transcripts[mid], salida, a.en_vivo)
    tabla(condiciones, mids, transcripts, gold, salida)


if __name__ == '__main__':
    main()
