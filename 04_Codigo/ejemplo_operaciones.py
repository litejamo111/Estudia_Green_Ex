"""Línea base de prueba. Python 3.10+, sin dependencias externas ni conexiones."""
from pathlib import Path
import csv,json,statistics
from datetime import date,timedelta
from collections import defaultdict

def load(root,name):
    with (root/'01_Datos'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def importe(v,rates):
    if v['estado']!='Confirmada':return 0.0
    amount=int(v['cantidad'])*float(v['precio_unitario'])*(1-float(v['descuento_pct'])/100)
    if v['moneda']=='USD':return amount*float(rates[v['fecha']])
    if v['moneda']=='COP':return amount
    raise ValueError('Moneda no admitida: '+v['moneda'])

def run(root):
    cfg=json.loads((root/'02_Documentacion/parametros_prueba.json').read_text(encoding='utf-8'))
    cut=date.fromisoformat(cfg['fecha_corte']);rates={x['fecha']:x['cop_por_usd'] for x in load(root,'trm_prueba.csv')}
    groups=defaultdict(list); installs=defaultdict(list)
    for v in load(root,'ventas.csv'):
        if v['estado']=='Confirmada' and date.fromisoformat(v['fecha'])<=cut:groups[v['cliente_id']].append(v)
    for x in load(root,'base_instalada.csv'):
        if date.fromisoformat(x['fecha_inicio'])<=cut:installs[x['cliente_id']].append(x)
    out=[]
    for c in load(root,'clientes.csv'):
        vs=groups[c['cliente_id']];ds=sorted(date.fromisoformat(v['fecha']) for v in vs)
        days=(cut-ds[-1]).days if ds else None
        cold=days is not None and days>=cfg['frio_dias_sin_compra']
        near=sum(0<=(date.fromisoformat(x['fecha_fin'])-cut).days<=cfg['renovacion_dias'] for x in installs[c['cliente_id']])
        expired=sum(date.fromisoformat(x['fecha_fin'])<cut for x in installs[c['cliente_id']])
        priority='Revisar cliente frío' if cold else 'Revisar cobertura' if near or expired else 'Seguimiento habitual'
        out.append({'cliente_id':c['cliente_id'],'fecha_corte':str(cut),'transacciones_confirmadas':len(vs),'ingreso_cop':round(sum(importe(v,rates) for v in vs),2),'ultima_compra':str(ds[-1]) if ds else '', 'dias_sin_compra':days if days is not None else '', 'frecuente':len(vs)>=cfg['frecuente_min_transacciones'],'frio':cold,'sin_compras':not bool(vs),'renovaciones_proximas':near,'coberturas_vencidas':expired,'productos_historicos':'|'.join(sorted({v['producto_id'] for v in vs})),'prioridad_regla':priority,'naturaleza':'Resultado de prueba; no es una predicción'})
    dest=root/'Salidas';dest.mkdir(exist_ok=True)
    with (dest/'resumen_clientes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
    summary={'fecha_corte':str(cut),'clientes':len(out),'transacciones_confirmadas':sum(x['transacciones_confirmadas'] for x in out),'ingreso_cop':round(sum(x['ingreso_cop'] for x in out),2),'clientes_frios':sum(x['frio'] for x in out),'nota':'Indicadores de prueba. Línea base por reglas, no modelo de IA.'}
    (dest/'resumen_prueba.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2));return out,summary

if __name__=='__main__':run(Path(__file__).resolve().parents[1])
