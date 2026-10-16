import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';

const D=window.QUITO_DATA;
const $=id=>document.getElementById(id);
const fmt=(v,d=2)=>v===null||v===undefined?'Sin dato':Number(v).toLocaleString('es-EC',{maximumFractionDigits:d});
const safe=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function fail(error){$('error').hidden=false;$('error').textContent='No se pudo abrir la escena 3D. '+error.message+' Abre ABRIR_VISOR.py; no abras index.html directamente. Comprueba que la aceleración gráfica del navegador esté habilitada.';$('status').textContent='La escena necesita revisión';console.error(error);}
window.addEventListener('error',e=>fail(e.error||new Error(e.message)));
window.addEventListener('unhandledrejection',e=>fail(e.reason instanceof Error?e.reason:new Error(String(e.reason))));

try{start();}catch(error){fail(error);}

function start(){
  if(!D)throw new Error('Faltan los datos geoespaciales locales.');
  const host=$('scene');
  const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.setClearColor('#e8eef0');
  renderer.outputColorSpace=THREE.SRGBColorSpace;host.prepend(renderer.domElement);
  const scene=new THREE.Scene();
  const camera=new THREE.PerspectiveCamera(42,1,.05,600);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;controls.dampingFactor=.09;controls.maxPolarAngle=Math.PI*.48;
  controls.minDistance=.7;controls.maxDistance=260;
  scene.add(new THREE.HemisphereLight(0xffffff,0x80949d,2.4));
  const sun=new THREE.DirectionalLight(0xffffff,2.0);sun.position.set(-50,80,30);scene.add(sun);
  const group=new THREE.Group();scene.add(group);
  const origin=[(D.bounds[0]+D.bounds[2])/2,(D.bounds[1]+D.bounds[3])/2];
  let vertical=1.5,currentMesh=null,base=null,overlay=null,selected=null,activeLayer='terreno',textureRequest=0;
  const lineGroups={boundaries:new THREE.Group(),rivers:new THREE.Group(),routes:new THREE.Group(),reports:new THREE.Group(),selection:new THREE.Group()};
  Object.values(lineGroups).forEach(g=>group.add(g));
  const geometries=new Map(),textures=new Map(),loader=new THREE.TextureLoader();
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
  $('resolution').textContent=D.analysis_note;$('weather-note').textContent=D.weather_note;
  function getTexture(path){
    if(!textures.has(path))textures.set(path,loader.loadAsync(path).then(t=>{t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t;}));
    return textures.get(path);
  }
  function valid(mesh,i){return Boolean(mesh.valid[i>>3]&(1<<(i&7)));}
  function geometry(mesh){
    if(geometries.has(mesh.id))return geometries.get(mesh.id);
    const p=new Float32Array(mesh.width*mesh.height*3),uv=new Float32Array(mesh.width*mesh.height*2),idx=[];
    const [xmin,ymin,xmax,ymax]=mesh.bounds;
    for(let r=0;r<mesh.height;r++)for(let c=0;c<mesh.width;c++){
      const i=r*mesh.width+c,e=xmin+(xmax-xmin)*c/(mesh.width-1),n=ymax-(ymax-ymin)*r/(mesh.height-1);
      p.set([(e-origin[0])/1000,mesh.elevations[i]/1000,(origin[1]-n)/1000],i*3);
      uv.set([(e-D.bounds[0])/(D.bounds[2]-D.bounds[0]),(n-D.bounds[1])/(D.bounds[3]-D.bounds[1])],i*2);
      if(r<mesh.height-1&&c<mesh.width-1){const b=i+1,d=i+mesh.width,f=d+1;if(valid(mesh,i)&&valid(mesh,d)&&valid(mesh,b))idx.push(i,d,b);if(valid(mesh,b)&&valid(mesh,d)&&valid(mesh,f))idx.push(b,d,f);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p,3));g.setAttribute('uv',new THREE.BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();geometries.set(mesh.id,g);return g;
  }
  function height(e,n){
    let m=currentMesh;
    const inside=a=>e>=a.bounds[0]&&e<=a.bounds[2]&&n>=a.bounds[1]&&n<=a.bounds[3];
    if(!inside(m))m=D.meshes[0];
    const c=THREE.MathUtils.clamp((e-m.bounds[0])/(m.bounds[2]-m.bounds[0])*(m.width-1),0,m.width-1),r=THREE.MathUtils.clamp((m.bounds[3]-n)/(m.bounds[3]-m.bounds[1])*(m.height-1),0,m.height-1);
    const c0=Math.floor(c),r0=Math.floor(r),c1=Math.min(c0+1,m.width-1),r1=Math.min(r0+1,m.height-1),u=c-c0,v=r-r0;
    return (1-v)*((1-u)*m.elevations[r0*m.width+c0]+u*m.elevations[r0*m.width+c1])+v*((1-u)*m.elevations[r1*m.width+c0]+u*m.elevations[r1*m.width+c1]);
  }
  function xyz(e,n,lift=15){return new THREE.Vector3((e-origin[0])/1000,(height(e,n)+lift)/1000,(origin[1]-n)/1000);}
  function clear(g){while(g.children.length){const o=g.children[0];g.remove(o);o.geometry?.dispose();if(o.material&&!o.userData.sharedMaterial)o.material.dispose();}}
  function line(paths,color,opacity=.6){
    const points=[];
    const visible=(e,n)=>e>=currentMesh.bounds[0]&&e<=currentMesh.bounds[2]&&n>=currentMesh.bounds[1]&&n<=currentMesh.bounds[3];
    for(const coords of paths){for(let k=1;k<coords.length;k++){
      const a=coords[k-1],b=coords[k],length=Math.hypot(b[0]-a[0],b[1]-a[1]),steps=Math.max(1,Math.ceil(length/120));
      for(let s=0;s<steps;s++){const u=s/steps,v=(s+1)/steps,ea=a[0]+(b[0]-a[0])*u,na=a[1]+(b[1]-a[1])*u,eb=a[0]+(b[0]-a[0])*v,nb=a[1]+(b[1]-a[1])*v;if(visible(ea,na)&&visible(eb,nb))points.push(...xyz(ea,na).toArray(),...xyz(eb,nb).toArray());}
    }}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points,3));
    return new THREE.LineSegments(g,new THREE.LineBasicMaterial({color,transparent:true,opacity,depthWrite:false}));
  }
  function rings(feature){const g=feature.geometry;return g.type==='Polygon'?g.coordinates:g.type==='MultiPolygon'?g.coordinates.flat():[];}
  function redrawLines(){
    Object.values(lineGroups).forEach(clear);
    lineGroups.boundaries.add(line(D.parishes.flatMap(rings),'#455f6a',.46));
    lineGroups.rivers.add(line([...D.vectors.rios,...D.vectors.quebradas],'#227cac',.85));
    lineGroups.routes.add(line(D.vectors.rutas_potenciales,'#6e45a2',.85));
    const positions=D.reports.filter(([e,n])=>e>=currentMesh.bounds[0]&&e<=currentMesh.bounds[2]&&n>=currentMesh.bounds[1]&&n<=currentMesh.bounds[3]).flatMap(([e,n])=>xyz(e,n,40).toArray());
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    lineGroups.reports.add(new THREE.Points(g,new THREE.PointsMaterial({color:'#e25823',size:.16,sizeAttenuation:true,depthWrite:false})));
    if(selected)lineGroups.selection.add(line(rings(selected),'#ffcc48',1));
    ['boundaries','rivers','routes','reports'].forEach(id=>lineGroups[id].visible=$(id).checked);
  }
  async function setLayer(id){
    activeLayer=id;const request=++textureRequest;const info=D.layers.find(l=>l.id===id);
    $('layer-note').textContent=info.source+'. '+(info.note||'');
    if(info.categorical){$('legend').innerHTML=info.categorical.map(e=>`<span class="legend-category"><span class="swatch" style="background:${e.color}"></span>${safe(e.label)}</span>`).join('');}
    else{const factor=(id==='susceptibilidad'||id==='ancla')?.01:1;const unit=factor===.01?'percentil (0–100)':info.unit;$('legend').innerHTML=`<img alt="Escala de colores" src="${info.legend}"><div class="legend-range"><span>${fmt(info.low*factor)}</span><span>${safe(unit)}</span><span>${fmt(info.high*factor)}</span></div>`;}
    const texture=await getTexture(info.texture);if(request!==textureRequest)return;
    base.material.map=texture;base.material.needsUpdate=true;
    $('status').textContent='Escena 3D lista · '+D.parishes.length+' parroquias';
  }
  async function view(id){
    const settings=D.views.find(v=>v.id===id);currentMesh=D.meshes.find(m=>m.id===settings.mesh);
    if(base){group.remove(base);group.remove(overlay);base.material.dispose();overlay.material.dispose();}
    const g=geometry(currentMesh);
    base=new THREE.Mesh(g,new THREE.MeshLambertMaterial({transparent:true,side:THREE.DoubleSide}));group.add(base);
    overlay=new THREE.Mesh(g,new THREE.MeshBasicMaterial({transparent:true,opacity:Number($('overlay-opacity').value),depthWrite:false,polygonOffset:true,polygonOffsetFactor:-3,polygonOffsetUnits:-3,side:THREE.DoubleSide}));
    overlay.visible=$('built').checked;overlay.renderOrder=2;group.add(overlay);
    getTexture(D.layers.find(l=>l.id==='decil').texture).then(t=>{overlay.material.map=t;overlay.material.needsUpdate=true;});
    group.scale.y=vertical;redrawLines();
    const [e,n]=settings.target,center=xyz(e,n,0);center.y*=vertical;
    const distance=settings.distance/1000;
    controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(distance*.24,distance*.70,distance*.70));controls.update();
    document.querySelectorAll('#views button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===id)));
    $('view-label').textContent=settings.label+' · malla '+currentMesh.spacing_approx_m+' m';await setLayer(activeLayer);
  }
  const groups=[...new Set(D.layers.map(l=>l.group))];
  for(const groupName of groups){const g=document.createElement('optgroup');g.label=groupName;for(const l of D.layers.filter(l=>l.group===groupName)){const o=document.createElement('option');o.value=l.id;o.textContent=l.name;g.append(o);}$('layer').append(g);}
  for(const v of D.views){const b=document.createElement('button');b.textContent=v.label;b.dataset.view=v.id;b.type='button';b.addEventListener('click',()=>view(v.id));$('views').append(b);}
  const sorted=[...D.parishes].sort((a,b)=>a.properties.nombre.localeCompare(b.properties.nombre,'es'));
  for(const p of sorted){const o=document.createElement('option');o.value=p.properties.parroquia;o.textContent=p.properties.nombre;$('parish').append(o);}
  function choose(p,move=false){
    selected=p;$('parish').value=p?.properties.parroquia||'';
    clear(lineGroups.selection);if(p)lineGroups.selection.add(line(rings(p),'#ffcc48',1));
    if(!p){$('detail').textContent='Fuera de las parroquias con información.';return;}
    const a=p.properties;
    $('detail').innerHTML=`<h3>${safe(a.nombre)}</h3><dl><dt>Personas con NBI</dt><dd>${fmt(a.pc_pnbi)} %</dd><dt>Saneamiento · viviendas</dt><dd>${fmt(a.pc_SH)} %</dd><dt>Agua limitada · viviendas</dt><dd>${fmt(a.pc_FSA)} %</dd><dt>Hacinamiento · hogares</dt><dd>${fmt(a.pc_HAC)} %</dd><dt>Construido válido</dt><dd>${fmt(a.construido_ha)} ha</dd><dt>Decil seleccionado</dt><dd>${fmt(a.prioritario_red_residual_ha)} ha</dd><dt>Superficie × lluvia</dt><dd>${fmt(a.area_prioritaria_ponderada_humedad_ha)} ha pond.</dd><dt>Índice NBI</dt><dd>${fmt(a.indice_NBI_ha_ponderadas)} ha pond.</dd><dt>Orden por NBI</dt><dd>${fmt(a.ranking_NBI,0)}</dd><dt>Selección entre modelos</dt><dd>${a.selecciones_NBI_de_6}/6</dd></dl><p class="note">Censo 2022 e integración congelada. Carencias no sumables. Las áreas ponderadas no son inundación ni personas afectadas.</p>`;
    if(move){const coords=rings(p).flat();const xs=coords.map(c=>c[0]),ys=coords.map(c=>c[1]);const e=(Math.min(...xs)+Math.max(...xs))/2,n=(Math.min(...ys)+Math.max(...ys))/2;const needUrban=e>=765000&&e<=805000&&n>=9960000&&n<=10008000;
      view(needUrban?'urbano':'distrito').then(()=>{const point=xyz(e,n,0);point.y*=vertical;controls.target.copy(point);camera.position.copy(point).add(new THREE.Vector3(7,14,16));controls.update();});}
  }
  function inRing(e,n,ring){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if(((yi>n)!==(yj>n))&&(e<(xj-xi)*(n-yi)/(yj-yi)+xi))inside=!inside;}return inside;}
  function contains(p,e,n){const polygons=p.geometry.type==='Polygon'?[p.geometry.coordinates]:p.geometry.coordinates;return polygons.some(poly=>inRing(e,n,poly[0])&&!poly.slice(1).some(r=>inRing(e,n,r)));}
  let down=null;
  renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
  renderer.domElement.addEventListener('pointerup',e=>{
    if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
    const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
    raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObject(base)[0];if(!hit)return;
    const east=origin[0]+hit.point.x*1000,north=origin[1]-hit.point.z*1000;
    $('coordinate').textContent=`E ${fmt(east,0)} m · N ${fmt(north,0)} m · cota malla ≈ ${fmt(hit.point.y*1000/vertical,0)} m`;
    choose(D.parishes.find(p=>contains(p,east,north))||null);
  });
  $('layer').addEventListener('change',()=>setLayer($('layer').value));
  $('parish').addEventListener('change',()=>choose(D.parishes.find(p=>p.properties.parroquia===$('parish').value)||null,true));
  $('built').addEventListener('change',()=>overlay.visible=$('built').checked);
  ['boundaries','rivers','routes','reports'].forEach(id=>$(id).addEventListener('change',()=>lineGroups[id].visible=$(id).checked));
  $('overlay-opacity').addEventListener('input',()=>{overlay.material.opacity=Number($('overlay-opacity').value);$('opacity-value').textContent=Math.round(overlay.material.opacity*100)+' %';});
  function setVertical(value){const ratio=value/vertical;vertical=value;group.scale.y=value;controls.target.y*=ratio;$('vertical').value=value;$('vertical-value').textContent=value.toFixed(1)+'× · sólo visual';controls.update();}
  $('vertical').addEventListener('input',()=>setVertical(Number($('vertical').value)));
  $('true-scale').addEventListener('click',()=>setVertical(1));
  $('north').addEventListener('click',()=>{const distance=camera.position.distanceTo(controls.target);camera.position.copy(controls.target).add(new THREE.Vector3(0,distance*.70,distance*.72));controls.update();});
  $('snapshot').addEventListener('click',()=>{renderer.render(scene,camera);const a=document.createElement('a');a.download='quito_3d_exploracion.png';a.href=renderer.domElement.toDataURL('image/png');a.click();});
  $('toggle-panel').addEventListener('click',()=>{document.body.classList.toggle('panel-hidden');$('toggle-panel').setAttribute('aria-expanded',String(!document.body.classList.contains('panel-hidden')));resize();});
  if(window.innerWidth<800)document.body.classList.add('panel-hidden');
  function resize(){const w=host.clientWidth,h=host.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);}
  new ResizeObserver(resize).observe(host);resize();
  const northPoint=new THREE.Vector3(),centerPoint=new THREE.Vector3();
  function frame(){requestAnimationFrame(frame);controls.update();
    centerPoint.copy(controls.target).project(camera);northPoint.copy(controls.target);northPoint.z-=2;northPoint.project(camera);
    const angle=Math.atan2(northPoint.x-centerPoint.x,northPoint.y-centerPoint.y)*180/Math.PI;
    $('north-arrow').style.transform=`rotate(${angle}deg)`;
    renderer.render(scene,camera);}frame();view('urbano');
}
