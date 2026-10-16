"""Escribe un proyecto QGIS portátil, estilos, temas y cámaras 3D guardadas.

No necesita importar QGIS para escribir XML. El esquema 3D corresponde a
QGIS 3.44. La apertura nativa se verifica por separado con validar_en_qgis.py.
Usa exclusivamente las copias preparadas dentro de esta entrega.
"""
from pathlib import Path
import json
import sqlite3
import uuid
import zipfile
import xml.etree.ElementTree as E
import numpy as np
import rasterio
from pyproj import CRS
from matplotlib import colormaps
from matplotlib.colors import to_hex

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'1_PROYECTO_QGIS'
DATA=ROOT/'2_CAPAS'
CRS_OBJ=CRS.from_epsg(32717)


def sub(parent,tag,text=None,**attrs):
    item=E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
    if text is not None:item.text=str(text)
    return item


def srs(parent,tag='srs'):
    node=sub(parent,tag);sp=sub(node,'spatialrefsys',nativeFormat='Wkt')
    for name,value in [('wkt',CRS_OBJ.to_wkt()),('proj4',CRS_OBJ.to_proj4()),
       ('srsid',0),('srid',32717),('authid','EPSG:32717'),
       ('description','WGS 84 / UTM zone 17S'),('projectionacronym','utm'),
       ('ellipsoidacronym','EPSG:7030'),('geographicflag','false')]:sub(sp,name,value)


def extent(parent,bounds,tag='extent'):
    e=sub(parent,tag)
    for k,v in zip(['xmin','ymin','xmax','ymax'],bounds):sub(e,k,v)


def color(info,f):return to_hex(colormaps[info.get('cmap','viridis')](f))


def rgba(hexcolor,alpha=255):
    c=hexcolor.lstrip('#');return ','.join([str(int(c[i:i+2],16))for i in (0,2,4)]+[str(alpha)])


def symbol(parent,name,kind,hexcolor,width=.25,outline=True):
    symbol=sub(parent,'symbol',name=name,type=kind,alpha='1',clip_to_extent='1',force_rhr='0')
    klass={'fill':'SimpleFill','line':'SimpleLine','marker':'SimpleMarker'}[kind]
    layer=sub(symbol,'layer',**{'class':klass,'enabled':'1','locked':'0','pass':'0'})
    option=sub(layer,'Option',type='Map')
    if kind=='fill':
        props={'color':rgba(hexcolor),'style':'solid' if outline else 'no',
            'outline_color':'65,87,97,150','outline_style':'solid','outline_width':'0.15',
            'outline_width_unit':'MM','joinstyle':'bevel'}
    elif kind=='line':props={'line_color':rgba(hexcolor),'line_width':str(width),'line_width_unit':'MM','line_style':'solid','capstyle':'round','joinstyle':'round'}
    else:props={'name':'circle','color':rgba(hexcolor),'outline_style':'no','size':'1.6','size_unit':'MM'}
    for k,v in props.items():sub(option,'Option',name=k,value=v,type='QString')
    return symbol


def raster_style(layer,info):
    pipe=sub(layer,'pipe')
    if info.get('categorical'):
        renderer=sub(pipe,'rasterrenderer',type='paletted',band=info['band'],opacity=info.get('opacity',1),alphaBand='-1',nodataColor='')
        palette=sub(renderer,'colorPalette')
        for item in info['categorical']:
            sub(palette,'paletteEntry',value=item['value'],color=item['color'],label=item['label'],alpha=item.get('alpha',255))
    else:
        lo,hi=info['low'],info['high']
        renderer=sub(pipe,'rasterrenderer',type='singlebandpseudocolor',band=info['band'],opacity='1',alphaBand='-1',classificationMin=lo,classificationMax=hi,nodataColor='')
        shader=sub(renderer,'rastershader')
        ramp=sub(shader,'colorrampshader',colorRampType='INTERPOLATED',classificationMode='1',clip='0',minimumValue=lo,maximumValue=hi)
        factor=.01 if info['id']in ['susceptibilidad','ancla']else 1
        for f in np.linspace(0,1,21):
            v=lo+(hi-lo)*float(f)
            sub(ramp,'item',value=v,color=color(info,float(f)),alpha='255',label=f'{v*factor:.2f} {"percentil" if factor==.01 else info["unit"]}')
    sub(pipe,'brightnesscontrast',brightness='0',contrast='0',gamma='1')
    sub(pipe,'huesaturation',saturation='0',grayscaleMode='0',colorizeOn='0',colorizeRed='255',colorizeGreen='128',colorizeBlue='128',colorizeStrength='100')
    sub(pipe,'rasterresampler',maxOversampling='2')
    # No alterar el muestreo del decil ni las clases: conservar el píxel exacto.
    sub(pipe,'resamplingStage','resamplingFilter')


def vector_style(layer,info):
    if info.get('field'):
        r=sub(layer,'renderer-v2',type='graduatedSymbol',attr=info['field'],symbollevels='0',forceraster='0',enableorderby='0',graduatedMethod='GraduatedColor')
        ranges=sub(r,'ranges');symbols=sub(r,'symbols')
        lo,hi=info['low'],info['high']
        for i in range(5):
            a,b=lo+(hi-lo)*i/5,lo+(hi-lo)*(i+1)/5
            sub(ranges,'range',lower=a,upper=b,symbol=i,label=f'{a:.2f} – {b:.2f} {info["unit"]}',render='true')
            symbol(symbols,str(i),'fill',color(info,(i+.5)/5))
        sub(r,'classificationMethod',id='EqualInterval',symmetricMode='0',symmetryPoint='0',symmetryAstride='0')
    else:
        r=sub(layer,'renderer-v2',type='singleSymbol',symbollevels='0',forceraster='0',enableorderby='0')
        symbols=sub(r,'symbols');symbol(symbols,'0',info['kind'],info['color'],info.get('width',.25),info.get('fill',True))
    sub(layer,'blendMode','0');sub(layer,'featureBlendMode','0');sub(layer,'layerOpacity','1')


def main():
    info=json.loads((OUT/'catalogo_capas.json').read_text(encoding='utf-8'))
    extras=[
        ('limites','Límites parroquiales','parroquias','fill','#ffffff',False),
        ('rios_v','Ríos cartografiados','rios','line','#287bb5',True),
        ('quebradas_v','Quebradas cartografiadas','quebradas','line','#429bc3',True),
        ('colectores_v','Colectores cartografiados','colectores','line','#76648e',True),
        ('cuencas_v','Microcuencas','microcuencas','fill','#ffffff',False),
        ('viales_principales','Vías municipales: capa 71','vias_principales','line','#857e73',True),
        ('viales_locales','Vías municipales: capa 68','vias_locales','line','#ac9f85',True),
        ('rutas_v','Rutas digitales potenciales (no aforos)','rutas_potenciales','line','#8157a1',True),
        ('candidatos_v','Candidatos digitales (sin comprobación de campo)','candidatos_digitales','marker','#b17c27',True),
        ('reportes_v','Reportes históricos de inundación (331)','reportes_inundacion','marker','#df6028',True),
    ]
    for id,name,table,kind,c,fill in extras:
        info.append(dict(id=id,name=name,group='Redes y referencias',file='vectores_quito.gpkg',
            vector_layer=table,kind=kind,color=c,fill=fill,source='Cartografía y referencias del estudio V05 / V10 / V12',note='Consultar fuentes y fechas; no evidencia de daños por píxel.'))
    # Fijar IDs reproducibles facilita comprobar referencias de vistas y temas.
    for x in info:x['qgis_id']=x['id']+'_'+str(uuid.uuid5(uuid.NAMESPACE_URL,'quito3d/'+x['id'])).replace('-','_')
    by_id={x['id']:x for x in info}
    with rasterio.open(DATA/'fabdem_30m.tif')as ds:bounds=list(ds.bounds)
    doc=E.Element('qgis',version='3.44.0',projectname='Quito: relieve, susceptibilidad y prioridad social',saveUser='Wilson Gustavo Morales Lastra')
    sub(doc,'homePath',path='..');sub(doc,'title','Quito: exploración multicapa y relieve 3D')
    srs(doc,'projectCrs')
    project_metadata=sub(doc,'projectMetadata');sub(project_metadata,'title','Quito: reconstrucción de terreno y resultados territoriales')
    sub(project_metadata,'author','Wilson Gustavo Morales Lastra')
    sub(project_metadata,'abstract','Entrega de exploración independiente del manuscrito. Terreno FABDEM 30 m; análisis construido 10 m; indicadores sociales parroquiales. No simulación hidráulica ni edificios individuales.')
    tree=sub(doc,'layer-tree-group',name='',expanded='1',checked='Qt::Checked')
    ordered_groups=['Redes y referencias','Resultado','Parroquias y resultado final','Lluvia estacional','Covariables físicas','Cobertura','Clases de cobertura','Control de calidad','Terreno']
    # De arriba hacia abajo: los límites y los resultados se dibujan sobre el terreno.
    ordered=[]
    for name in ordered_groups:
        group=sub(tree,'layer-tree-group',name=name,expanded='1' if name in ['Resultado','Terreno']else '0',checked='Qt::Checked')
        members=[x for x in info if x['group']==name]
        if name=='Resultado':members.sort(key=lambda x:0 if x['id']=='decil'else 1)
        for x in members:
            uri='../2_CAPAS/'+x['file']+('|layername='+x['vector_layer']if 'vector_layer'in x else '')
            x['uri']=uri
            sub(group,'layer-tree-layer',id=x['qgis_id'],name=x['name'],source=uri,providerKey='ogr' if 'vector_layer'in x else 'gdal',expanded='0',checked='Qt::Checked' if x['id']in ['limites','decil','terreno']else 'Qt::Unchecked')
            ordered.append(x)
    custom=sub(tree,'custom-order',enabled='0')
    for x in ordered:sub(custom,'item',x['qgis_id'])
    canvas=sub(doc,'mapcanvas',name='theMapCanvas',annotationsVisible='1')
    sub(canvas,'units','meters');extent(canvas,[758000,9955000,809000,10012000]);sub(canvas,'rotation',0)
    srs(canvas,'destinationsrs');sub(canvas,'rendermaptile','0')
    layers=sub(doc,'projectlayers')
    db=sqlite3.connect(DATA/'vectores_quito.gpkg')
    for x in ordered:
        vector='vector_layer'in x
        attrs=dict(type='vector' if vector else 'raster',hasScaleBasedVisibilityFlag='0',minScale='100000000',maxScale='0',autoRefreshEnabled='0',autoRefreshTime='0')
        if vector:
            geometry=db.execute('SELECT geometry_type_name FROM gpkg_geometry_columns WHERE table_name=?',(x['vector_layer'],)).fetchone()[0]
            attrs['geometry']='Polygon' if 'POLYGON'in geometry else 'Line' if 'LINE'in geometry else 'Point'
        node=sub(layers,'maplayer',**attrs)
        sub(node,'id',x['qgis_id']);sub(node,'datasource',x['uri']);sub(node,'keywordList');sub(node,'layername',x['name'])
        sub(node,'title',x['name']);sub(node,'abstract',x.get('source','')+'. '+x.get('note',''))
        srs(node)
        if vector:
            b=db.execute('SELECT min_x,min_y,max_x,max_y FROM gpkg_contents WHERE table_name=?',(x['vector_layer'],)).fetchone()
            extent(node,b)
        else:
            with rasterio.open(DATA/x['file'])as src:
                extent(node,list(src.bounds));sub(node,'noData',noDataList='')
        sub(node,'provider','ogr' if vector else 'gdal',**({'encoding':'UTF-8'}if vector else {}))
        vector_style(node,x)if vector else raster_style(node,x)
        if vector:
            fields=db.execute('PRAGMA table_info("'+x['vector_layer']+'")').fetchall()
            aliases=sub(node,'aliases')
            friendly={'pc_pnbi':'Personas con NBI (%)','pc_SH':'Viviendas con saneamiento insuficiente (%)','pc_FSA':'Viviendas con agua limitada (%)','pc_HAC':'Hogares con hacinamiento (%)','p_humedo':'P(trimestre de lluvia > q80)','indice_NBI_ha_ponderadas':'Índice NBI (ha ponderadas, no personas)','area_prioritaria_ponderada_humedad_ha':'Superficie × probabilidad húmeda (ha ponderadas)'}
            for index,(_,field,*_)in enumerate(fields):
                if field not in ['geom','fid']:sub(aliases,'alias',field=field,index=index,name=friendly.get(field,field))
            if x['vector_layer']=='parroquias':sub(node,'previewExpression','"nombre"')
            else:sub(node,'previewExpression','')
    db.close()
    themes={
      '01 Figura 1 — construido y decil':['limites','decil','terreno'],
      '02 Relieve y cobertura':['limites','cobertura'],
      '03 Susceptibilidad residual':['limites','susceptibilidad','terreno'],
      '04 Escorrentía potencial':['rutas_v','rios_v','quebradas_v','limites','depresion','terreno'],
      '05 NBI parroquial':['limites','nbi','terreno'],
      '06 Saneamiento parroquial':['limites','saneamiento','terreno'],
      '07 Prioridad final NBI':['limites','indice_nbi','terreno'],
      '08 Lluvia estacional — NDJ':['limites','lluvia','terreno'],
      '09 Control de soporte':['limites','soporte','terreno'],
    }
    presets=sub(doc,'visibility-presets')
    for title,ids in themes.items():
        preset=sub(presets,'visibility-preset',name=title)
        for id in ids:sub(preset,'layer',id=by_id[id]['qgis_id'],visible='1')
    # QGIS 3.44 conserva cámaras y temas en el gestor de vistas del proyecto.
    manager=sub(doc,'mapViewDocks3D')
    web=json.loads((ROOT/'4_VISOR/datos.js').read_text(encoding='utf-8').removeprefix('window.QUITO_DATA=').strip().removesuffix(';'))
    with rasterio.open(DATA/'fabdem_30m.tif')as dem:
        for index,v in enumerate(web['views'],1):
            view=sub(manager,'view',name=f'{index:02d} {v["label"]}',isOpen='0',isDocked='1')
            settings=sub(view,'qgis3d')
            sub(settings,'origin',x=(bounds[0]+bounds[2])/2,y=(bounds[1]+bounds[3])/2,z='0')
            sub(settings,'extent',xMin=bounds[0],yMin=bounds[1],xMax=bounds[2],yMax=bounds[3],showIn2dView='0')
            sub(settings,'camera',**{'field-of-view':'45','projection-type':'1','camera-navigation-mode':'terrain-based-navigation','camera-movement-speed':'5'})
            sub(settings,'color',background='#e8eef0',selection='#ffcc48');srs(settings,'crs')
            terrain=sub(settings,'terrain',**{'terrain-rendering-enabled':'1','shading-enabled':'0','map-theme':next(iter(themes)),'show-labels':'0','layer':by_id['terreno']['qgis_id'],'resolution':'32','skirt-height':'10','exaggeration':'1','texture-size':'1024','max-terrain-error':'3','max-ground-error':'1','elevation-offset':'0'})
            sub(terrain,'generator',type='dem',layer=by_id['terreno']['qgis_id'],resolution='32',**{'skirt-height':'10'})
            selected=sub(terrain,'layers')
            for id in next(iter(themes.values())):sub(selected,'layer',id=by_id[id]['qgis_id'])
            e,n=v['target'];z=float(next(dem.sample([(e,n)]))[0])
            sub(view,'camera',xMap=e,yMap=n,zMap=z,dist=v['distance'],pitch='45',yaw='0')
    props=sub(doc,'properties');paths=sub(props,'Paths');sub(paths,'Absolute','false',type='bool')
    gui=sub(props,'Gui')
    for k,v in [('CanvasColorRedPart',232),('CanvasColorGreenPart',238),('CanvasColorBluePart',240)]:sub(gui,k,v,type='int')
    measure=sub(props,'Measure');sub(measure,'Ellipsoid','EPSG:7030',type='QString')
    sub(doc,'transformContext');sub(doc,'projectModels')
    E.indent(doc,space='  ')
    payload=b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE qgis PUBLIC "http://mrcc.com/qgis.dtd" "SYSTEM">\n'+E.tostring(doc,encoding='utf-8')
    (OUT/'quito_multicapa.qgs').write_bytes(payload)
    with zipfile.ZipFile(OUT/'quito_multicapa.qgz','w',zipfile.ZIP_DEFLATED)as z:z.writestr('quito_multicapa.qgs',payload)
    (OUT/'indice_proyecto.json').write_text(json.dumps({'layers':info,'themes':themes,'views':web['views'],'native_qgis_tested':False,'target_qgis':'3.44'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Proyecto: {len(info)} capas, {len(themes)} temas y {len(web["views"])} vistas 3D. Apertura nativa pendiente.',flush=True)


if __name__=='__main__':main()
