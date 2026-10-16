"""Construye copias GIS y derivados de visualización; no reestima modelos.

Ejecutar con el entorno geoespacial del estudio. Los datos fuente se abren
en lectura. Todo lo generado queda en RECONSTRUCCION_3D_QUITO.
"""
from pathlib import Path
import os
os.environ['GDAL_CACHEMAX'] = '64'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import base64
import csv
import hashlib
import json
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_bounds, from_origin
from rasterio.warp import reproject
from rasterio.windows import Window
from shapely.geometry import box, mapping
from PIL import Image
from scipy.ndimage import distance_transform_edt
import matplotlib
matplotlib.use('Agg')
from matplotlib import colormaps

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT.parent
P5 = EX/'VERSION_5_QUITO_10M/1_INVESTIGACION'
P6 = EX/'VERSION_6_ENSO_PREDICTIBILIDAD/1_INVESTIGACION'
P7 = EX/'VERSION_7_CALIBRACION_NMME/1_INVESTIGACION'
P10 = EX/'VERSION_10_ESCORRENTIA_LOCAL/1_INVESTIGACION'
P12 = EX/'VERSION_12_PRIORIDAD_NBI/1_INVESTIGACION'
DATA = ROOT/'2_CAPAS'
WEB = ROOT/'4_VISOR'
QA = ROOT/'5_VERIFICACION'
WC_COLORS = {10:('#267a3c','Árboles'),20:('#c4a74b','Arbustos'),30:('#9fc66c','Herbáceas'),
    40:('#e0bd58','Cultivos'),50:('#aeb9c2','Construido'),60:('#c8b6a4','Suelo desnudo'),
    70:('#f0f5ff','Nieve / hielo'),80:('#2b77c3','Agua'),90:('#4dada0','Humedal herbáceo'),
    95:('#709f58','Manglar'),100:('#b79a73','Musgos / líquenes')}
MANIFEST = []
LAYERS = []


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def copy_source(source, filename):
    target=DATA/filename
    if not target.exists() or target.stat().st_size != source.stat().st_size:
        shutil.copyfile(source,target)
    original_hash=digest(source)
    assert digest(target)==original_hash
    MANIFEST.append({'source':str(source.relative_to(EX)), 'copy':filename,
                     'bytes':target.stat().st_size,'sha256':original_hash})
    print('Copia verificada:',filename,flush=True)


def scaled_read(path, band, shape, mode=Resampling.average):
    with rasterio.open(path) as src:
        if mode == Resampling.max:
            a=np.full(shape,np.nan,np.float32)
            reproject(rasterio.band(src,band),a,src_transform=src.transform,src_crs=src.crs,
                dst_transform=from_bounds(*src.bounds,shape[1],shape[0]),dst_crs=src.crs,
                src_nodata=src.nodata,dst_nodata=np.nan,resampling=mode)
            return a
        a=src.read(band,out_shape=shape,resampling=mode,masked=True).astype('float32')
        return np.ma.filled(a,np.nan)


def register(id, name, group, file, band=1, unit='', source='', cmap='viridis',
             low=None, high=None, categorical=None, opacity=1.0, note=''):
    info=dict(id=id,name=name,group=group,file=file,band=band,unit=unit,
              source=source,cmap=cmap,low=low,high=high,categorical=categorical,
              opacity=opacity,note=note)
    LAYERS.append(info)
    return info


def build_exact_result():
    meta=json.loads((P12/'2_DATOS/PROCESADOS/control_aplicacion.json').read_text())
    result=json.loads((P12/'6_FINAL/control_integracion.json').read_text())
    n=meta['n_generated']
    flat=np.load(P12/'2_DATOS/PROCESADOS/indice_pixel.npy',mmap_mode='r')[:n]
    score=np.load(P12/'2_DATOS/PROCESADOS/scores_aplicacion.npy',mmap_mode='r')
    clipped=np.load(P12/'2_DATOS/PROCESADOS/soporte_recortado.npy',mmap_mode='r')[:n]
    with rasterio.open(DATA/'worldcover_2021_10m.tif') as ds:
        profile=ds.profile.copy()
    profile.update(count=1,dtype='uint8',nodata=0,compress='LZW',tiled=True,predictor=2)
    selected=score[:,0]>=result['thresholds']['red_residual']
    assert int(selected.sum()) == round(result['priority_area_red_ha']*100)
    output=DATA/'construido_decil_exacto_10m.tif'
    with rasterio.open(output,'w',**profile) as dst:
        dst.set_band_description(1,'1 construido válido; 2 decil exacto del modelo residual')
        dst.update_tags(interpretacion='No agua observada ni inundación futura; corte sobre scores completos',
                        source='V12, mismos píxeles de la Figura 1',no_data='fuera de construido válido')
        for row in range(0,profile['height'],128):
            rows=min(128,profile['height']-row); start=np.searchsorted(flat,row*profile['width']);end=np.searchsorted(flat,(row+rows)*profile['width'])
            a=np.zeros(rows*profile['width'],np.uint8)
            a[flat[start:end]-row*profile['width']]=1+selected[start:end].astype(np.uint8)
            dst.write(a.reshape(rows,profile['width']),1,window=Window(0,row,profile['width'],rows))
    profile.update(dtype='float32',nodata=-9999.,predictor=3)
    for filename,values,label in [
        ('densidad_relativa_residual_10m.tif',np.exp(score[:,0]),'Densidad relativa media 1 sobre construido'),
        ('soporte_acotado_10m.tif',clipped.astype('float32'),'1 alguna covariable acotada; 0 sin recorte')]:
        with rasterio.open(DATA/filename,'w',**profile) as dst:
            dst.set_band_description(1,label)
            for row in range(0,profile['height'],128):
                rows=min(128,profile['height']-row);start=np.searchsorted(flat,row*profile['width']);end=np.searchsorted(flat,(row+rows)*profile['width'])
                a=np.full(rows*profile['width'],-9999.,np.float32)
                a[flat[start:end]-row*profile['width']]=values[start:end]
                dst.write(a.reshape(rows,profile['width']),1,window=Window(0,row,profile['width'],rows))
    return {'valid_built_pixels':int(n),'selected_pixels':int(selected.sum()),
            'selected_area_ha':round(float(selected.sum()*.01),2),
            'threshold_log_density':result['thresholds']['red_residual']}


def prepare_vectors():
    gpkg=DATA/'vectores_quito.gpkg'
    sources={
      'parroquias':P12/'6_FINAL/prioridad_integrada_quito.geojson',
      'rios':P5/'2_DATOS/ORIGINALES/VECTORES/red_hidrica.geojson',
      'quebradas':P5/'2_DATOS/ORIGINALES/VECTORES/quebrada_viva.geojson',
      'colectores':P5/'2_DATOS/ORIGINALES/VECTORES/colector.geojson',
      'microcuencas':P5/'2_DATOS/ORIGINALES/VECTORES/microcuencas.geojson',
      'vias_principales':P10/'2_DATOS/ORIGINALES/vias_71.geojson',
      'vias_locales':P10/'2_DATOS/ORIGINALES/vias_68.geojson',
      'rutas_potenciales':P10/'6_FINAL/rutas_potenciales_fabdem_30m.geojson',
      'candidatos_digitales':P10/'6_FINAL/candidatos_con_parroquia.geojson',
    }
    counts={}
    parish=None
    for name,path in sources.items():
        g=gpd.read_file(path).to_crs(32717)
        if name=='parroquias':parish=g
        for col in list(g.columns):
            if col!='geometry' and g[col].dtype=='object':
                g[col]=g[col].map(lambda x:json.dumps(x,ensure_ascii=False) if isinstance(x,(dict,list)) else x)
        g.to_file(gpkg,layer=name,driver='GPKG',index=False)
        counts[name]=len(g)
        print('Vector:',name,len(g),flush=True)
    reports=gpd.read_file(P5/'2_DATOS/PROCESADOS/reportes_quito.geojson')
    reports=reports[(reports.evento_norm=='INUNDACION')&(reports.fecha<='2025-09-30')]
    assert len(reports)==331
    reports.to_file(gpkg,layer='reportes_inundacion',driver='GPKG',index=False)
    counts['reportes_inundacion']=len(reports)
    grid=json.loads((P6/'2_DATOS/PROCESADOS/grilla_lluvia.json').read_text())
    a,b,c,d,e,f=grid['transform'][:6]
    fixed=pd.read_csv(P7/'6_FINAL/pronostico_calibracion_fija_nov2026_ene2027.csv')
    fixed=fixed[(fixed.tipo_unidad=='QUITO_CELDA')&(fixed.modelo=='red_ENSO__beta_PIT')].set_index('unit')
    features=[]
    for cell in grid['cells']:
        r,col=cell['row'],cell['col'];x=c+a*col;y=f+e*r;entry=fixed.loc[cell['id']]
        features.append({'id_celda':cell['id'],'p_humedo':float(entry.p_humedo),
          'lluvia_mediana_mm':float(entry.lluvia_mediana_mm),'temporada':'2026-11 / 2027-01',
          'ultimo_predictor':'2026-08','geometry':box(x,y+e,x+a,y)})
    weather=gpd.GeoDataFrame(features,crs=4326).to_crs(32717)
    weather.to_file(gpkg,layer='lluvia_estacional',driver='GPKG',index=False)
    counts['lluvia_estacional']=len(weather)
    return parish,weather,reports,counts


def write_texture(info, arr, valid):
    categorical=info.get('categorical')
    if categorical:
        rgba=np.zeros((*arr.shape,4),np.uint8)
        for entry in categorical:
            color=entry['color'].lstrip('#');mask=arr==entry['value']
            rgba[mask,:3]=[int(color[i:i+2],16) for i in (0,2,4)]
            rgba[mask,3]=entry.get('alpha',255)
    else:
        finite=arr[np.isfinite(arr)&valid]
        low=info.get('low');high=info.get('high')
        if low is None:low=float(np.quantile(finite,.02))
        if high is None:high=float(np.quantile(finite,.98))
        if high<=low:high=low+1
        info['low'],info['high']=low,high
        scaled=np.clip((np.nan_to_num(arr,nan=low)-low)/(high-low),0,1)
        rgba=(colormaps[info['cmap']](scaled)*255).astype(np.uint8)
    rgba[~valid | ~np.isfinite(arr),3]=0
    destination=WEB/'texturas'/f"{info['id']}.png"
    Image.fromarray(rgba).save(destination,optimize=True)
    info['texture']='texturas/'+destination.name
    if not categorical:
        bar=(colormaps[info['cmap']](np.linspace(0,1,128))*255).astype(np.uint8)[None,:,:]
        Image.fromarray(np.repeat(bar,12,axis=0)).save(WEB/'texturas'/f"leyenda_{info['id']}.png")
        info['legend']='texturas/'+f"leyenda_{info['id']}.png"


def build_web(parishes,weather,reports):
    with rasterio.open(DATA/'fabdem_30m.tif') as ds: bounds=list(ds.bounds)
    tw=2048;th=round(tw*(bounds[3]-bounds[1])/(bounds[2]-bounds[0]));shape=(th,tw)
    transform=from_bounds(*bounds,tw,th)
    valid=rasterize([(g,1)for g in parishes.geometry],out_shape=shape,transform=transform,fill=0).astype(bool)
    terrain=scaled_read(DATA/'fabdem_30m.tif',1,shape)
    register('terreno','Relieve FABDEM','Terreno','fabdem_30m.tif',unit='m',source='FABDEM V1-2; soporte 30 m',cmap='gist_earth',note='Altura, no agua ni edificios individuales.')
    wc=[dict(value=k,color=v[0],label=v[1])for k,v in WC_COLORS.items()]
    register('cobertura','Cobertura WorldCover 2021','Cobertura','worldcover_2021_10m.tif',categorical=wc,source='ESA WorldCover 2021; 10 m')
    for band,id,name,unit,cmap,low,high in [
        (1,'altitud_modelo','Altitud usada por el modelo','m','gist_earth',None,None),
        (2,'pendiente','Pendiente','grados','magma',0,60),
        (3,'posicion','Posición topográfica','m','RdBu_r',-100,100),
        (4,'relieve','Relieve local','m','viridis',0,160),
        (5,'rio','Distancia a ríos','m','YlGnBu_r',0,2000),
        (6,'quebrada','Distancia a quebradas','m','YlGnBu_r',0,2000),
        (7,'colector','Distancia a colectores','m','YlGnBu_r',0,2000)]:
        register(id,name,'Covariables físicas','derivados_30m.tif',band,unit,'Copernicus DEM / cartografía municipal; soporte 30 m',cmap,low,high)
    register('hem','Error de altura Copernicus (HEM)','Control de calidad','derivados_30m.tif',8,'m','Copernicus DEM; indicador de calidad, no precisión del resultado','magma',0,20)
    for band,id,name in [(1,'dens110','Construido cercano: ventana 110 m'),(2,'dens510','Construido cercano: ventana 510 m')]:
        register(id,name,'Covariables físicas','densidad_construida_10m.tif',band,'fracción 0–1','WorldCover; malla 10 m','inferno',0,1)
    for band,id,name,unit,cmap,low,high in [
        (1,'depresion','Depresión digital','m','Blues',0,8),
        (2,'contribuye','Área contribuyente','ln(1 + ha)','viridis',0,None),
        (3,'urbano_arriba','Construido contribuyente','ln(1 + ha)','inferno',0,None),
        (4,'fraccion_arriba','Fracción construida aguas arriba','fracción 0–1','magma',0,1),
        (6,'vias','Distancia a vías','m','YlGnBu_r',0,2000)]:
        register(id,name,'Covariables físicas','escorrentia_fabdem_30m.tif',band,unit,'FABDEM / PUGS; soporte 30 m',cmap,low,high,note='Conectividad digital; no capacidad hidráulica observada.')
    register('susceptibilidad','Susceptibilidad: percentil construido','Resultado','percentil_residual_10m.tif',1,'percentil × 100','Red residual V12; malla 10 m','YlOrRd',0,10000,note='Valor GIS / 100 = percentil. No probabilidad de inundación.')
    register('ancla','Comparador loglineal: percentil','Resultado','percentil_ancla_10m.tif',1,'percentil × 100','Ancla V12; malla 10 m','YlOrRd',0,10000)
    register('densidad_relativa','Densidad relativa del modelo residual','Resultado','densidad_relativa_residual_10m.tif',1,'relativa; media territorial 1','Puntajes completos V12; malla 10 m','YlOrRd',0,None,note='No es probabilidad; normalización sobre el dominio construido válido.')
    register('borde','Influencia del borde hidrológico','Control de calidad','escorrentia_fabdem_30m.tif',5,'fracción / bandera del derivado','Control de conectividad digital V10','magma',0,1,note='No se interpreta como inundación ni flujo medido.')
    register('decil','Construido y decil exacto (Figura 1)','Resultado','construido_decil_exacto_10m.tif',categorical=[dict(value=1,color='#aeb9c2',label='Construido válido'),dict(value=2,color='#ba2c22',label='Decil superior exacto')],source='Puntajes completos V12; 2993.62 ha seleccionadas',note='Visor: máximo por celda de visualización. QGIS: píxeles originales de 10 m.')
    register('soporte','Covariables fuera del soporte original','Control de calidad','soporte_acotado_10m.tif',categorical=[dict(value=0,color='#4f8c7b',label='Sin recorte'),dict(value=1,color='#e5a230',label='Alguna covariable acotada')],source='Control de soporte V12')
    for field,id,name,unit,cmap in [
        ('pc_pnbi','nbi','Personas con NBI','% de personas','YlOrRd'),
        ('pc_SH','saneamiento','Saneamiento insuficiente','% de viviendas','YlOrRd'),
        ('pc_FSA','agua','Acceso limitado a agua segura','% de viviendas','YlGnBu'),
        ('pc_HAC','hacinamiento','Hacinamiento','% de hogares','PuRd'),
        ('area_prioritaria_ponderada_humedad_ha','area_final','Superficie prioritaria ponderada por lluvia','ha ponderadas','YlOrRd'),
        ('indice_NBI_ha_ponderadas','indice_nbi','Prioridad final ponderada por NBI','ha ponderadas','YlOrRd'),
        ('selecciones_NBI_de_6','estabilidad','Estabilidad de la selección NBI','selecciones de 6','YlGnBu')]:
        info=register(id,name,'Parroquias y resultado final','vectores_quito.gpkg',unit=unit,source='Integración V12 / Censo 2022; soporte parroquial',cmap=cmap,low=0,high=6 if id=='estabilidad' else float(parishes[field].max()),note='NBI y carencias son ponderaciones alternativas, no sumables.')
        info['vector_layer']='parroquias';info['field']=field
    info=register('lluvia','Probabilidad de trimestre húmedo','Lluvia estacional','vectores_quito.gpkg',unit='probabilidad 0–1',source='Red ENSO, emisión 2026-10-09; NDJ 2026–2027; celdas nativas 0.05°',cmap='Blues',low=0,high=1,note='Probabilidad de superar el percentil 80 de lluvia trimestral; no inundación.')
    info['vector_layer']='lluvia_estacional';info['field']='p_humedo'
    for info in LAYERS:
        if 'vector_layer' in info:
            g=parishes if info['vector_layer']=='parroquias' else weather
            arr=rasterize([(geom,float(value)) for geom,value in zip(g.geometry,g[info['field']])],out_shape=shape,transform=transform,fill=np.nan,dtype='float32')
        else:
            mode=Resampling.nearest if info.get('categorical') else Resampling.average
            if info['id']=='decil':mode=Resampling.max
            arr=scaled_read(DATA/info['file'],info['band'],shape,mode)
        write_texture(info,arr,valid)
        print('Textura:',info['id'],flush=True)
    # Las clases originales son una sola cobertura, no once imágenes nuevas.
    # Se conservan once vistas binarias en QGIS para reconocer sus entradas.
    wc_arr=scaled_read(DATA/'worldcover_2021_10m.tif',1,shape,Resampling.nearest)
    for code,(color,label) in WC_COLORS.items():
        info=register('clase'+str(code),'Cobertura: '+label,'Clases de cobertura','worldcover_2021_10m.tif',categorical=[dict(value=code,color=color,label=label)],source='Indicador de clase WorldCover 2021; 10 m')
        write_texture(info,wc_arr,valid)
    meshes=[]
    specs=[('distrito',bounds,300),('urbano',[765000,9960000,805000,10008000],100)]
    for name,b,step in specs:
        w=round((b[2]-b[0])/step)+1;h=round((b[3]-b[1])/step)+1
        # Se muestrean alturas reales del DEM; no se generan relieves sintéticos.
        tr=from_bounds(b[0]-step/2,b[1]-step/2,b[2]+step/2,b[3]+step/2,w,h)
        heights=np.full((h,w),np.nan,np.float32)
        with rasterio.open(DATA/'fabdem_30m.tif')as src:
            reproject(rasterio.band(src,1),heights,src_transform=src.transform,src_crs=src.crs,
                dst_transform=tr,dst_crs=src.crs,src_nodata=-9999,dst_nodata=np.nan,resampling=Resampling.bilinear)
        coverage=rasterize([(g,1)for g in parishes.geometry],out_shape=(h,w),transform=tr,fill=0).astype(bool)
        ok=coverage&np.isfinite(heights)
        nearest=distance_transform_edt(~np.isfinite(heights),return_distances=False,return_indices=True)
        heights=heights[tuple(nearest)]
        heights=np.round(heights,1)
        meshes.append({'id':name,'bounds':b,'width':w,'height':h,'spacing_approx_m':step,
                       'elevations':heights.reshape(-1).tolist(),'valid':np.packbits(ok.reshape(-1),bitorder='little').tolist()})
    parish_data=[];boundaries=[]
    for _,row in parishes.iterrows():
        geom=row.geometry.simplify(80,preserve_topology=True)
        props={k:(None if pd.isna(v) else v.item() if isinstance(v,np.generic) else v)
               for k,v in row.items()if k!='geometry'}
        parish_data.append({'properties':props,'geometry':mapping(geom)})
    report_points=[[round(g.x,2),round(g.y,2)]for g in reports.geometry]
    # Líneas de consulta simplificadas; los originales permanecen en el GeoPackage.
    vectors={}
    for name in ['rios','quebradas','rutas_potenciales']:
        lines=gpd.read_file(DATA/'vectores_quito.gpkg',layer=name)
        paths=[]
        for geom in lines.geometry.simplify(35):
            if geom is None or geom.is_empty:continue
            parts=[geom] if geom.geom_type=='LineString' else list(geom.geoms) if geom.geom_type=='MultiLineString' else []
            paths.extend([[[round(x,1),round(y,1)]for x,y,*_ in part.coords]for part in parts])
        vectors[name]=paths
    data={'crs':'EPSG:32717','bounds':bounds,'meshes':meshes,'layers':LAYERS,
        'parishes':parish_data,'reports':report_points,'vectors':vectors,
        'views':[
            dict(id='distrito',label='Distrito completo',mesh='distrito',target=[775000,9984000],distance=132000),
            dict(id='urbano',label='Núcleo urbano',mesh='urbano',target=[781000,9985000],distance=60000),
            dict(id='sur',label='Sur de Quito',mesh='urbano',target=[771000,9966000],distance=26000),
            dict(id='valles',label='Valles orientales',mesh='urbano',target=[794000,9980000],distance=31000)],
        'analysis_note':'Terreno fuente 30 m; mallas del visor 300 / 100 m. Texturas generalizadas ~43 m, decil por máximo. Análisis y consultas exactas en QGIS a 10 m.',
        'model_note':'Susceptibilidad relativa, no profundidad ni extensión de inundación futura.',
        'weather_note':'Emisión congelada 2026-10-09; noviembre 2026–enero 2027; antecedentes hasta agosto 2026.'}
    (WEB/'datos.js').write_text('window.QUITO_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)+';\n',encoding='utf-8')
    (ROOT/'1_PROYECTO_QGIS/catalogo_capas.json').write_text(json.dumps(LAYERS,ensure_ascii=False,indent=2),encoding='utf-8')
    return data


def main():
    for folder in [DATA,WEB/'texturas',QA,ROOT/'1_PROYECTO_QGIS']:
        folder.mkdir(parents=True,exist_ok=True)
    sources={
        'fabdem_30m.tif':P10/'2_DATOS/PROCESADOS/fabdem_30m_alineado.tif',
        'copernicus_dsm_30m.tif':P5/'2_DATOS/PROCESADOS/dsm_30m.tif',
        'derivados_30m.tif':P5/'2_DATOS/PROCESADOS/derivados_30m.tif',
        'escorrentia_fabdem_30m.tif':P10/'2_DATOS/PROCESADOS/escorrentia_fabdem_30m.tif',
        'densidad_construida_10m.tif':P5/'2_DATOS/PROCESADOS/densidad_construida_10m.tif',
        'worldcover_2021_10m.tif':P5/'2_DATOS/PROCESADOS/worldcover_2021_10m.tif',
        'percentil_residual_10m.tif':P12/'6_FINAL/RASTERS_10M/percentil_construido_red_residual_10m.tif',
        'percentil_ancla_10m.tif':P12/'6_FINAL/RASTERS_10M/percentil_construido_ancla_acotada_10m.tif',
    }
    for name,source in sources.items():copy_source(source,name)
    exact=build_exact_result()
    parishes,weather,reports,counts=prepare_vectors()
    data=build_web(parishes,weather,reports)
    audit={'source_copies':MANIFEST,'exact_result':exact,'vector_counts':counts,
        'display_meshes':[{'id':m['id'],'width':m['width'],'height':m['height'],'spacing_approx_m':m['spacing_approx_m']} for m in data['meshes']],
        'layer_count':len(LAYERS),'paper_modified':False,
        'not_included':'proximidad_estructura_OSM: fuente no recuperada, no se presenta como dato; alturas GEDI estimadas no utilizadas en el resultado final.',
        'textures_are_visual_generalizations':True}
    (QA/'control_capas.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items()if k!='source_copies'},ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
