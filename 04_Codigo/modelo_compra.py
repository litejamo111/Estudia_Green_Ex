"""Clasificación logística didáctica con partición temporal. Sin dependencias."""
from pathlib import Path
from datetime import date,timedelta
from collections import defaultdict
import csv,json,math,statistics

def run(root):
    with (root/'01_Datos/ventas.csv').open(encoding='utf-8-sig') as f: sales=list(csv.DictReader(f))
    hist=defaultdict(list)
    for v in sales:
        if v['estado']=='Confirmada':hist[v['cliente_id']].append(date.fromisoformat(v['fecha']))
    with (root/'01_Datos/clientes.csv').open(encoding='utf-8-sig') as f: clients=list(csv.DictReader(f))
    rows=[]
    for year in [2025,2026]:
        for month in range(1,13):
            nxt=date(year+1,1,1) if month==12 else date(year,month+1,1)
            cut=nxt-timedelta(days=1)
            if cut<date(2025,3,31) or cut>date(2026,9,30):continue
            for c in clients:
                if date.fromisoformat(c['fecha_alta'])>cut:continue
                ds=[d for d in hist[c['cliente_id']] if d<=cut]
                rec=(cut-max(ds)).days if ds else 730
                f30=sum(0<=(cut-d).days<30 for d in ds);f90=sum(0<=(cut-d).days<90 for d in ds)
                label=int(any(cut<d<=cut+timedelta(days=30) for d in hist[c['cliente_id']]))
                rows.append({'cliente_id':c['cliente_id'],'corte':str(cut),'recencia_dias':rec,'frecuencia_30d':f30,'frecuencia_90d':f90,'historial_n':len(ds),'compra_30d':label})
    train=[x for x in rows if x['corte']<='2026-04-30'];valid=[x for x in rows if '2026-05-01'<=x['corte']<='2026-06-30'];test=[x for x in rows if x['corte']>='2026-07-01']
    fields=['recencia_dias','frecuencia_30d','frecuencia_90d','historial_n']
    mu=[statistics.mean(x[f] for x in train) for f in fields];sd=[statistics.pstdev(x[f] for x in train) or 1 for f in fields]
    def vec(x):return [1]+[(x[f]-m)/s for f,m,s in zip(fields,mu,sd)]
    def sig(z):return 1/(1+math.exp(-max(-35,min(35,z))))
    w=[0.0]*5
    for epoch in range(600):
        g=[0.0]*5
        for row in train:
            a=vec(row);error=sig(sum(k*v for k,v in zip(w,a)))-row['compra_30d']
            for j in range(5):g[j]+=error*a[j]
        w=[v-.1*(g[j]/len(train)+(.001*v if j else 0)) for j,v in enumerate(w)]
    def prob(x):return sig(sum(k*v for k,v in zip(w,vec(x))))
    def metrics(data,predict):
        tp=tn=fp=fn=0
        for x in data:
            y=x['compra_30d'];p=predict(x)
            tp+=bool(p and y);tn+=bool(not p and not y);fp+=bool(p and not y);fn+=bool(not p and y)
        precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
        return {'n':len(data),'TP':tp,'TN':tn,'FP':fp,'FN':fn,'precision':round(precision,4),'recall':round(recall,4),'F1':round(2*precision*recall/(precision+recall),4) if precision+recall else 0}
    thresholds=[.2,.3,.4,.5,.6,.7,.8]
    threshold=max(thresholds,key=lambda t:metrics(valid,lambda x:prob(x)>=t)['F1'])
    result={'modelo':'Regresión logística didáctica; pesos aprendidos en datos de prueba','entrenamiento_hasta':'2026-04-30','validacion':'mayo-junio 2026','prueba':'julio-septiembre 2026','ventana_objetivo_dias':30,'umbral_elegido_solo_en_validacion':threshold,'variables':fields,'media_entrenamiento':mu,'desviacion_entrenamiento':sd,'pesos':w,'validacion':metrics(valid,lambda x:prob(x)>=threshold),'prueba_modelo':metrics(test,lambda x:prob(x)>=threshold),'prueba_linea_base_compra_ultimos_30d':metrics(test,lambda x:x['frecuencia_30d']>0),'advertencia':'No demuestra rendimiento en datos empresariales. No cambiar umbral usando la prueba final. Fotografías del mismo cliente reaparecen en distintos meses; mide seguimiento temporal, no generalización a clientes nuevos.'}
    dest=root/'Salidas';dest.mkdir(exist_ok=True)
    (dest/'metricas_modelo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,data in [('fotografias_modelo.csv',rows),('predicciones_prueba.csv',[dict(x,probabilidad_prueba=round(prob(x),6),prediccion=int(prob(x)>=threshold)) for x in test])]:
        with (dest/name).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=data[0]);writer.writeheader();writer.writerows(data)
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':run(Path(__file__).resolve().parents[1])
