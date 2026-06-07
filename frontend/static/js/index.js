const OPS = {
  mongo: [
    { id:'login', title:'Login de usuario', method:'POST',
      desc:'Valida username y contraseÃ±a (findOne)', endpoint:'/api/mongo/login',
      params:[{key:'username',label:'Username',default:'VitoNava'},{key:'password',label:'ContraseÃ±a',default:'starvy123',type:'password'}],
      body:(p)=>({username:p.username,password:p.password}) },
    { id:'mis-resenas', title:'Mis reseÃ±as', method:'GET',
      desc:'ReseÃ±as del usuario con $lookup de restaurantes', endpoint:'/api/mongo/mis-resenas',
      params:[{key:'dni',label:'DNI usuario',default:'44000009'}] },
    { id:'mis-calificaciones', title:'Mis calificaciones', method:'GET',
      desc:'Calificaciones 1â€“5 estrellas del usuario', endpoint:'/api/mongo/mis-calificaciones',
      params:[{key:'dni',label:'DNI usuario',default:'44000009'}] },
    { id:'buscar-restaurantes', title:'Buscar restaurantes', method:'GET',
      desc:'Filtra por tipo, barrio y calificaciÃ³n mÃ­nima', endpoint:'/api/mongo/buscar-restaurantes',
      params:[{key:'tipo',label:'Tipo comida',default:''},{key:'barrio',label:'Barrio',default:''},{key:'min_calificacion',label:'Cal. mÃ­nima',default:'0'},{key:'dni',label:'DNI usuario',default:'44000009'}] },
    { id:'resenas-restaurante', title:'ReseÃ±as de restaurante', method:'GET',
      desc:'Lista reseÃ±as con username del autor ($lookup)', endpoint:'/api/mongo/resenas-restaurante',
      params:[{key:'restaurante_id',label:'Restaurante ID',default:'1'}] },
      { id:'insertar-resena', title:'Insertar reseÃ±a â­', method:'POST',
  desc:'CalificÃ¡ con estrellas y guardÃ¡ la reseÃ±a en MongoDB (insertOne)',
  endpoint:'/api/mongo/insertar-resena',
  params:[
    {key:'dni_usuario',label:'DNI',default:'44000001'},
    {key:'restaurante_id',label:'Rest. ID',default:'1'},
    {key:'puntaje',label:'CalificaciÃ³n',default:'5',type:'stars'},
    {key:'comentario',label:'Tu reseÃ±a',default:'Excelente lugar!'}
  ],
  body:(p)=>p },
  ],
  neo4j: [
    { id:'perfil', title:'Perfil social', method:'GET',
      desc:'Siguiendo, seguidores, visitas y reseÃ±as', endpoint:'/api/neo4j/perfil',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'siguiendo', title:'A quiÃ©n sigue', method:'GET',
      desc:'Usuarios con relaciÃ³n [:SIGUE] saliente', endpoint:'/api/neo4j/siguiendo',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'seguidores', title:'Seguidores', method:'GET',
      desc:'Usuarios con relaciÃ³n [:SIGUE] entrante', endpoint:'/api/neo4j/seguidores',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'buscar-usuarios', title:'Buscar usuarios', method:'GET',
      desc:'Busca por username, nombre o apellido', endpoint:'/api/neo4j/buscar-usuarios',
      params:[{key:'termino',label:'TÃ©rmino',default:'val'},{key:'dni',label:'DNI usuario',default:'44000009'}] },
    { id:'visitas-amigos', title:'Visitas de amigos', method:'GET',
      desc:'Restaurantes donde fueron las personas que seguÃ­s', endpoint:'/api/neo4j/visitas-amigos',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'recomendacion-colaborativa', title:'RecomendaciÃ³n colaborativa', method:'GET',
      desc:'Lugares â‰¥4â˜… por amigos que no visitaste', endpoint:'/api/neo4j/recomendacion-colaborativa',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'recomendacion-contenido', title:'RecomendaciÃ³n por contenido', method:'GET',
      desc:'Lugares similares a lo que te gustÃ³ antes', endpoint:'/api/neo4j/recomendacion-contenido',
      params:[{key:'username',label:'Username',default:'VitoNava'}] },
    { id:'seguir', title:'Seguir usuario', method:'POST',
      desc:'Crea relaciÃ³n [:SIGUE] con MERGE', endpoint:'/api/neo4j/seguir',
      params:[{key:'follower',label:'Yo (follower)',default:'VitoNava'},{key:'followed',label:'A seguir',default:'LuisRam'}],
      body:(p)=>p },
  ],
  cass: [
    { id:'promociones-restaurante', title:'Promociones activas', method:'GET',
      desc:'Promos activas de un restaurante (partition key)', endpoint:'/api/cassandra/promociones-restaurante',
      params:[{key:'restaurante_id',label:'Restaurante ID',default:'2'}] },
    { id:'promociones-fecha-barrio', title:'Promos por fecha y barrio', method:'GET',
      desc:'Promociones vigentes un dÃ­a y barrio especÃ­ficos', endpoint:'/api/cassandra/promociones-fecha-barrio',
      params:[{key:'dia',label:'Fecha (YYYY-MM-DD)',default:'2026-05-15'},{key:'barrio',label:'Barrio',default:'Palermo'}] },
    { id:'visitas-restaurante-dia', title:'Visitas por dÃ­a', method:'GET',
      desc:'Visitas registradas en un restaurante una fecha dada', endpoint:'/api/cassandra/visitas-restaurante-dia',
      params:[{key:'restaurante_id',label:'Restaurante ID',default:'1'},{key:'fecha',label:'Fecha (YYYY-MM-DD)',default:'2026-05-15'}] },
    { id:'insertar-visita', title:'Insertar visita', method:'POST',
      desc:'Registra nueva visita con timestamp automÃ¡tico (INSERT)', endpoint:'/api/cassandra/insertar-visita',
      params:[{key:'dni_usuario',label:'DNI',default:'44000001'},{key:'restaurante_id',label:'Rest. ID',default:'1'},{key:'plato_id',label:'Plato',default:'',type:'plato_select'},{key:'plato_nombre',type:'hidden',default:''},{key:'tipo_comida',type:'hidden',default:''},{key:'barrio',type:'hidden',default:''},{key:'monto',type:'hidden',default:''}],
      body:(p)=>p },
    { id:'metricas-dia', title:'MÃ©tricas del dÃ­a', method:'GET',
      desc:'Total visitas, ingresos y plato mÃ¡s pedido', endpoint:'/api/cassandra/metricas-dia',
      params:[{key:'restaurante_id',label:'Restaurante ID',default:'1'},{key:'fecha',label:'Fecha (YYYY-MM-DD)',default:'2026-05-15'}] },
  ],
  redis: [
    { id:'sesiones-activas', title:'Sesiones activas', method:'GET',
      desc:'Usuarios logueados ahora mismo (KEYS + GET + TTL)', endpoint:'/api/redis/sesiones-activas', params:[], special:'sessions' },
    { id:'verificar-sesion', title:'Verificar sesiÃ³n', method:'GET',
      desc:'Chequea si un usuario estÃ¡ logueado y cuÃ¡nto le queda', endpoint:'/api/redis/verificar-sesion',
      params:[{key:'user_id',label:'User ID (DNI)',default:'44000009'}], special:'session-single' },
    { id:'ranking-restaurantes', title:'Ranking restaurantes ðŸ†', method:'GET',
      desc:'Top N mÃ¡s visitados (ZREVRANGE Sorted Set)', endpoint:'/api/redis/ranking-restaurantes',
      params:[{key:'top',label:'Top N',default:'10'}] },
    { id:'ranking-tipos-comida', title:'Ranking tipos de comida ðŸ•', method:'GET',
      desc:'Top N tipos mÃ¡s pedidos (ZREVRANGE Sorted Set)', endpoint:'/api/redis/ranking-tipos-comida',
      params:[{key:'top',label:'Top N',default:'10'}] },
    { id:'ultimas-busquedas', title:'Ãšltimas bÃºsquedas', method:'GET',
      desc:'Historial reciente del usuario (LRANGE)', endpoint:'/api/redis/ultimas-busquedas',
      params:[{key:'user_id',label:'User ID (DNI)',default:'44000009'}] },
    { id:'registrar-busqueda', title:'Registrar bÃºsqueda', method:'POST',
      desc:'LPUSH + LTRIM: agrega al historial del usuario', endpoint:'/api/redis/registrar-busqueda',
      params:[{key:'user_id',label:'User ID',default:'44000009'},{key:'termino',label:'TÃ©rmino',default:'pizza'}],
      body:(p)=>p },
  ]
};

const DB_META = {
  mongo: {label:'MongoDB',   color:'#00ed64'},
  neo4j: {label:'Neo4j',     color:'#4184c4'},
  cass:  {label:'Cassandra', color:'#e56c18'},
  redis: {label:'Redis',     color:'#dc382d'}
};

let currentDB=null, currentOp=null, loading=false, queryCount=0;
let platosLoadTimer=null, platosRestauranteCargado=null;
let currentRows=[], currentSpecial=null, currentView='table', lastParams={}, resultsMax=false;
let currentGraphData=null;
let sidebarCollapsed=false;

function toggleSidebar(){
  sidebarCollapsed = !sidebarCollapsed;
  document.getElementById('layout').classList.toggle('sidebar-collapsed', sidebarCollapsed);
  setTimeout(()=>{
    if(currentRows.length && currentDB === 'neo4j' && currentView === 'graph') renderResults(currentRows, currentSpecial);
  }, 260);
}
function hexToRgb(hex){ const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16); return `${r},${g},${b}`; }
function escHtml(str){ return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function formatDateValue(key, val){
  if(val === null || val === undefined) return val;
  if(/fecha|date|dia/i.test(String(key)) && typeof val === 'string'){
    const m = val.match(/^(\d{4}-\d{2}-\d{2})/);
    if(m) return m[1];
  }
  return val;
}
function toggleResultsMax(){
  resultsMax = !resultsMax;
  const main = document.querySelector('.main');
  main.classList.toggle('results-max', resultsMax);
  const btn = document.getElementById('expand-results');
  if(btn) btn.textContent = resultsMax ? 'â†™ Reducir' : 'â›¶ Ampliar';
  if(currentRows.length && currentDB === 'neo4j' && currentView === 'graph') renderResults(currentRows, currentSpecial);
}
function initResizableResults(){
  const split = document.getElementById('content-split');
  const handle = document.getElementById('splitter');
  if(!split || !handle) return;
  let active = false;

  const begin = (clientY, e)=>{
    if(resultsMax) return;
    active = true;
    document.body.classList.add('resizing');
    if(e) e.preventDefault();
  };
  const move = (clientY)=>{
    if(!active) return;
    const rect = split.getBoundingClientRect();
    let top = clientY - rect.top;
    const minTop = 85;
    const minBottom = 260;
    top = Math.max(minTop, Math.min(top, rect.height - minBottom));
    split.style.gridTemplateRows = `${top}px 8px minmax(${minBottom}px, 1fr)`;
    if(currentRows.length && currentDB === 'neo4j' && currentView === 'graph') {
      window.clearTimeout(window.__graphResizeTimer);
      window.__graphResizeTimer = window.setTimeout(()=>renderResults(currentRows, currentSpecial), 80);
    }
  };
  const stop = ()=>{
    if(active){ active = false; document.body.classList.remove('resizing'); }
  };

  handle.addEventListener('pointerdown', e=>{ handle.setPointerCapture?.(e.pointerId); begin(e.clientY, e); });
  window.addEventListener('pointermove', e=>move(e.clientY));
  window.addEventListener('pointerup', stop);
  handle.addEventListener('mousedown', e=>begin(e.clientY, e));
  window.addEventListener('mousemove', e=>move(e.clientY));
  window.addEventListener('mouseup', stop);
}


function selectDB(db){
  currentDB=db; currentOp=null; currentRows=[]; currentView='table'; currentGraphData=null;
  if(resultsMax) toggleResultsMax();
  document.querySelectorAll('.db-btn').forEach(b=>b.classList.remove('active'));
  document.querySelector(`.db-btn.${db}`).classList.add('active');
  const meta=DB_META[db];
  const badge=document.getElementById('badge-db');
  badge.textContent=meta.label;
  badge.style.background=`rgba(${hexToRgb(meta.color)},.13)`;
  badge.style.color=meta.color;
  badge.style.borderColor=`rgba(${hexToRgb(meta.color)},.3)`;
  document.getElementById('stat-db').textContent=meta.label;
  const panel=document.getElementById('ops-panel');
  panel.innerHTML='<div class="ops-title">Operaciones</div>';
  OPS[db].forEach(op=>{
    const card=document.createElement('div');
    card.className='op-card'; card.id=`op-${op.id}`;
    card.innerHTML=`<span class="op-method ${op.method==='GET'?'method-get':'method-post'}">${op.method}</span>
      <div class="op-card-title">${op.title}</div>
      <div class="op-card-desc">${op.desc}</div>`;
    card.onclick=()=>selectOp(op);
    panel.appendChild(card);
  });
  resetMain();
}

function selectOp(op){
  currentOp=op; 
  currentRows=[]; 
  currentView='table'; 
  currentGraphData=null;
  platosRestauranteCargado=null;

  document.querySelectorAll('.op-card').forEach(c=>c.classList.remove('active'));
  document.getElementById(`op-${op.id}`).classList.add('active');

  const bar=document.getElementById('params-bar');
  bar.innerHTML='';

  op.params.forEach(p=>{
    if(p.type === 'hidden'){
      const hidden=document.createElement('input');
      hidden.type='hidden';
      hidden.id=`param-${p.key}`;
      hidden.value=p.default||'';
      bar.appendChild(hidden);
      return;
    }

    const g=document.createElement('div'); 
    g.className='param-group';

    const lbl=document.createElement('label'); 
    lbl.textContent=p.label+':';

    g.appendChild(lbl);

    if(p.type === 'stars' || p.key === 'puntaje'){
      const wrap=document.createElement('div');
      wrap.className='star-param';

      const hidden=document.createElement('input');
      hidden.type='hidden';
      hidden.id=`param-${p.key}`;
      hidden.value=p.default || '5';

      const valueText=document.createElement('span');
      valueText.className='star-value';
      valueText.textContent=`${hidden.value}/5`;

      function pintarEstrellas(valor){
        wrap.querySelectorAll('.star-btn').forEach(btn=>{
          const n=Number(btn.dataset.value);
          btn.classList.toggle('active', n <= Number(valor));
        });
        valueText.textContent=`${valor}/5`;
      }

      for(let i=1; i<=5; i++){
        const star=document.createElement('button');
        star.type='button';
        star.className='star-btn';
        star.dataset.value=i;
        star.innerHTML='â˜…';
        star.title=`${i} estrella${i>1?'s':''}`;

        star.onclick=()=>{
          hidden.value=String(i);
          pintarEstrellas(i);
        };

        wrap.appendChild(star);
      }

      wrap.appendChild(hidden);
      wrap.appendChild(valueText);
      g.appendChild(wrap);

      setTimeout(()=>pintarEstrellas(hidden.value), 0);
    } else if(p.type === 'plato_select') {
      const sel=document.createElement('select');
      sel.id=`param-${p.key}`;
      sel.innerHTML='<option value="">Cargando platos...</option>';
      sel.addEventListener('change',()=>sincronizarPlatoSeleccionado(sel));
      g.appendChild(sel);
    } else {
      const inp=document.createElement('input');
      inp.type=p.type||'text'; 
      inp.value=p.default||'';
      inp.id=`param-${p.key}`; 
      inp.placeholder=p.default||'';
      inp.addEventListener('keydown',e=>{if(e.key==='Enter')runOp();});
      if(op.id === 'insertar-visita' && p.key === 'restaurante_id'){
        inp.addEventListener('input',programarCargaPlatosDeRestaurante);
        inp.addEventListener('change',cargarPlatosDeRestaurante);
        inp.addEventListener('blur',cargarPlatosDeRestaurante);
      }
      g.appendChild(inp);
    }

    bar.appendChild(g);
  });

  const btn=document.createElement('button');
  btn.className='run-btn'; 
  btn.id='run-btn';
  btn.innerHTML='â–¶ Ejecutar'; 
  btn.onclick=runOp;

  bar.appendChild(btn);

  setQueryPlaceholder();
  setResultsEmpty();

  if(op.id === 'insertar-visita'){
    cargarPlatosDeRestaurante();
  }
}

async function cargarPlatosDeRestaurante(){
  if(currentOp?.id !== 'insertar-visita') return;

  const restauranteInput=document.getElementById('param-restaurante_id');
  const platoSelect=document.getElementById('param-plato_id');
  if(!restauranteInput || !platoSelect) return;

  const restauranteId=restauranteInput.value || '1';
  platoSelect.disabled=true;
  platoSelect.innerHTML='<option value="">Cargando platos...</option>';
  actualizarBotonInsertarVisita(false);

  try{
    const response=await fetch(`/api/mongo/platos-restaurante?restaurante_id=${encodeURIComponent(restauranteId)}`);
    const data=await response.json();
    const platos=data.resultado || [];

    if(!platos.length){
      platoSelect.innerHTML='<option value="">Restaurante inexistente o sin platos</option>';
      platosRestauranteCargado=String(restauranteId);
      sincronizarPlatoSeleccionado(platoSelect);
      actualizarBotonInsertarVisita(false);
      return;
    }

    platoSelect.innerHTML=platos.map(plato=>{
      const precio=plato.precio ?? '';
      const label=`${plato.plato_nombre}${precio!=='' ? ' - $'+precio : ''}`;
      return `<option value="${escHtml(plato.plato_id)}"
        data-nombre="${escHtml(plato.plato_nombre || '')}"
        data-tipo="${escHtml(plato.tipo_comida || '')}"
        data-barrio="${escHtml(plato.barrio || '')}"
        data-precio="${escHtml(precio)}">${escHtml(label)}</option>`;
    }).join('');

    platoSelect.disabled=false;
    platosRestauranteCargado=String(restauranteId);
    sincronizarPlatoSeleccionado(platoSelect);
    actualizarBotonInsertarVisita(true);
  }catch(e){
    platoSelect.innerHTML='<option value="">No se pudieron cargar platos</option>';
    platosRestauranteCargado=null;
    sincronizarPlatoSeleccionado(platoSelect);
    actualizarBotonInsertarVisita(false);
  }
}

function programarCargaPlatosDeRestaurante(){
  clearTimeout(platosLoadTimer);
  platosLoadTimer=setTimeout(cargarPlatosDeRestaurante, 300);
}

function setParamValue(key, value){
  const el=document.getElementById(`param-${key}`);
  if(el) el.value=value ?? '';
}

function sincronizarPlatoSeleccionado(select){
  const opt=select?.selectedOptions?.[0];
  setParamValue('plato_nombre', opt?.dataset?.nombre || '');
  setParamValue('tipo_comida', opt?.dataset?.tipo || '');
  setParamValue('barrio', opt?.dataset?.barrio || '');
  setParamValue('monto', opt?.dataset?.precio || '');
  actualizarBotonInsertarVisita(Boolean(select?.value));
}

function actualizarBotonInsertarVisita(habilitado){
  if(currentOp?.id !== 'insertar-visita') return;
  const btn=document.getElementById('run-btn');
  if(!btn || loading) return;
  btn.disabled=!habilitado;
}

async function runOp(){
  if(!currentOp||loading)return;
  loading=true;
  const btn=document.getElementById('run-btn');
  if(btn){btn.disabled=true;btn.innerHTML='<div class="spinner"></div> Ejecutando...';}

  if(currentOp.id === 'insertar-visita'){
    clearTimeout(platosLoadTimer);
    const restauranteActual=document.getElementById('param-restaurante_id')?.value || '';
    const platoActual=document.getElementById('param-plato_id')?.value || '';
    if(platosRestauranteCargado !== String(restauranteActual) || !platoActual){
      await cargarPlatosDeRestaurante();
    }

    if(!document.getElementById('param-plato_id')?.value){
      loading=false;
      if(btn){btn.disabled=true;btn.innerHTML='â–¶ Ejecutar';}
      renderError('SeleccionÃ¡ un restaurante existente con platos disponibles antes de insertar la visita.');
      return;
    }
  }

  const params={};
  currentOp.params.forEach(p=>{const el=document.getElementById(`param-${p.key}`);if(el)params[p.key]=el.value;});
  lastParams=params;
  const t0=Date.now();
  try{
    let response;
    if(currentOp.method==='POST'){
      const body=currentOp.body?currentOp.body(params):params;
      response=await fetch(currentOp.endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }else{
      const qs=new URLSearchParams(params).toString();
      response=await fetch(`${currentOp.endpoint}${qs?'?'+qs:''}`);
    }
    const data=await response.json();
    currentGraphData = data.grafo || null;
    const ms=Date.now()-t0;
    document.getElementById('exec-time').textContent=`â± ${ms}ms`;
    renderQuery(data.query,data.lenguaje);
    if(data.error){ renderError(data.error); }
    else{ renderResults(data.resultado||[], currentOp.special); }
    queryCount++;
    document.getElementById('stat-queries').textContent=queryCount;
    const lastStr=currentOp.title.replace(/[â­ðŸ†ðŸ•âœï¸]/g,'').trim();
    document.getElementById('stat-last').textContent=lastStr.slice(0,13)+(lastStr.length>13?'â€¦':'');
  }catch(err){
    currentGraphData = null;
    renderError('No se pudo conectar con Flask. VerificÃ¡ que python app.py estÃ© corriendo en la terminal.');
  }finally{
    loading=false;
    if(btn){
      btn.disabled=false;
      btn.innerHTML='â–¶ Ejecutar';
      if(currentOp?.id === 'insertar-visita'){
        actualizarBotonInsertarVisita(Boolean(document.getElementById('param-plato_id')?.value));
      }
    }
  }
}

function setQueryPlaceholder(){
  const langMap={mongo:'javascript',neo4j:'cypher',cass:'sql',redis:'redis'};
  setLangPill(langMap[currentDB]||'plaintext');
  document.getElementById('query-code').innerHTML=`<div class="state-empty"><span class="icon">â³</span>PresionÃ¡ <strong>Ejecutar</strong> para ver la query</div>`;
  document.getElementById('exec-time').textContent='';
}
function setResultsEmpty(){
  document.getElementById('count-pill').style.display='none';
  const toggle=document.getElementById('view-toggle'); if(toggle) toggle.style.display='none';
  document.getElementById('results-body').innerHTML=`<div class="state-empty"><span class="icon">ðŸ“‹</span>Los resultados aparecerÃ¡n acÃ¡</div>`;
}
function resetMain(){
  document.getElementById('params-bar').innerHTML='<span style="color:var(--muted);font-size:13px;font-weight:600;">â† SeleccionÃ¡ una operaciÃ³n del panel</span>';
  document.getElementById('query-code').innerHTML=`<div class="welcome"><div class="welcome-logo">â­</div><h2>ElegÃ­ una operaciÃ³n</h2><p>HacÃ© clic en cualquier operaciÃ³n del panel para ver la query que se ejecuta en la base de datos.</p></div>`;
  document.getElementById('lang-pill').textContent='';
  document.getElementById('lang-pill').className='lang-pill';
  document.getElementById('exec-time').textContent='';
  setResultsEmpty();
}
function setLangPill(lang){
  const pill=document.getElementById('lang-pill');
  const labels={javascript:'MQL',cypher:'Cypher',sql:'CQL',redis:'Redis CLI',plaintext:''};
  pill.textContent=labels[lang]||lang;
  pill.className=`lang-pill lang-${lang}`;
}
function renderQuery(queryText, lang) {
  setLangPill(lang);
  const langMap = { cypher:'plaintext', sql:'sql', redis:'bash', javascript:'javascript' };
  const hlLang = langMap[lang] || 'plaintext';
  const safeQuery = queryText || '';
  let highlighted;
  try {
    highlighted = hlLang === 'plaintext'
      ? escHtml(safeQuery)
      : hljs.highlight(safeQuery, { language: hlLang, ignoreIllegals: true }).value;
  } catch (e) {
    highlighted = escHtml(safeQuery);
  }
  document.getElementById('query-code').innerHTML=`<pre><code class="hljs language-${hlLang}">${highlighted}</code></pre>`;
}
function renderError(msg){
  document.getElementById('count-pill').style.display='none';
  const toggle=document.getElementById('view-toggle'); if(toggle) toggle.style.display='none';
  document.getElementById('results-body').innerHTML=`<div class="error-box">âŒ ${escHtml(msg)}</div>`;
}

function renderResults(rows, special){
  currentRows = rows || [];
  currentSpecial = special || null;

  const pill=document.getElementById('count-pill');
  pill.textContent=`${currentRows.length} resultado${currentRows.length!==1?'s':''}`;
  pill.style.display='';

  const toggle=document.getElementById('view-toggle');
  const canGraph = currentDB === 'neo4j' && currentRows.length > 0 && !currentSpecial;
  if(toggle){
    toggle.style.display = canGraph ? 'flex' : 'none';
    document.getElementById('view-table').classList.toggle('active', currentView === 'table');
    document.getElementById('view-graph').classList.toggle('active', currentView === 'graph');
  }

  if(!currentRows.length){
    document.getElementById('results-body').innerHTML=`<div class="state-empty"><span class="icon">ðŸ”</span>Sin resultados para estos parÃ¡metros<br><span style="font-size:11px;margin-top:4px;">ProbÃ¡ con otros valores</span></div>`;
    return;
  }

  if(currentSpecial==='sessions'||currentSpecial==='session-single') renderSessionCards(currentRows);
  else if(currentDB === 'redis' && (currentOp?.id || '').startsWith('ranking-')) renderRedisRanking(currentRows);
  else if(currentDB === 'redis' && (currentOp?.id || '') === 'ultimas-busquedas') renderSearchCards(currentRows);
  else if(currentDB === 'cass') renderCassandraCards(currentRows);
  else if(canGraph && currentView === 'graph') renderGraphResults(currentRows);
  else renderTableResults(currentRows);
}

function setResultsView(view){
  currentView = view;
  document.getElementById('view-table').classList.toggle('active', view === 'table');
  document.getElementById('view-graph').classList.toggle('active', view === 'graph');
  renderResults(currentRows, currentSpecial);
}

function renderSessionCards(rows){
  const body=document.getElementById('results-body');
  const TTL_MAX=3600;
  let html='<div class="session-grid">';
  rows.forEach((row,i)=>{
    const token=row.token||'â€”';
    const ttl=row.ttl_segundos||0;
    const activa=row.sesion_activa!==false && token!=='â€”' && token!=='sin sesion';
    const usuario=row.usuario||'Usuario';
    const min=Math.floor(ttl/60), seg=ttl%60;
    const pct=Math.min(100,Math.round((ttl/TTL_MAX)*100));
    const tokenCorto=token.length>20?token.slice(0,8)+'â€¦'+token.slice(-8):token;
    html+=`<div class="session-card ${activa?'active-session':''}" style="animation-delay:${i*60}ms">
      <div class="session-top">
        <div class="session-avatar">ðŸ‘¤</div>
        <div>
          <div class="session-username">Usuario ${escHtml(String(usuario).slice(0,12))}</div>
          <div class="session-status">${activa?'ðŸŸ¢ SesiÃ³n activa':'ðŸ”´ Sin sesiÃ³n'}</div>
        </div>
      </div>
      <div class="session-info">
        <div class="session-row"><span class="session-label">ðŸ”‘ Token</span><span class="session-val">${escHtml(tokenCorto)}</span></div>
        <div class="session-row"><span class="session-label">â³ Tiempo restante</span><span class="session-val">${activa?`${min}min ${seg}seg`:'Expirada'}</span></div>
      </div>
      ${activa?`<div class="ttl-bar-wrap"><div class="ttl-bar-bg"><div class="ttl-bar" style="width:${pct}%"></div></div></div>`:''}
    </div>`;
  });
  html+='</div>';
  body.innerHTML=html;
}


function renderRedisRanking(rows){
  const body=document.getElementById('results-body');
  const isFood = currentOp?.id === 'ranking-tipos-comida';
  const nameKey = isFood ? 'tipo_comida' : 'restaurante';
  const scoreKey = isFood ? 'pedidos' : 'visitas';
  const label = isFood ? 'pedidos' : 'visitas';
  const medals = ['ðŸ¥‡','ðŸ¥ˆ','ðŸ¥‰'];
  const podiumClass = {1:'first', 2:'second', 3:'third'};

  // Siempre dibujamos los 3 lugares del podio. Orden visual: 2Â° | 1Â° | 3Â°
  const byPosition = {};
  rows.forEach((row, idx)=>{
    const pos = Number(row.posicion || idx + 1);
    if(pos <= 3) byPosition[pos] = row;
  });

  let html = '<div class="redis-ranking-wrap">';
  html += '<div class="redis-podium">';

  [2,1,3].forEach((pos, visualIdx)=>{
    const row = byPosition[pos];
    const cls = podiumClass[pos] || '';
    if(row){
      html += `<article class="podium-card ${cls}" style="animation-delay:${visualIdx*70}ms">
        <div class="podium-position">#${pos}</div>
        <div class="podium-rank">${medals[pos-1]}</div>
        <div class="podium-title">${escHtml(row[nameKey] || 'â€”')}</div>
        <div class="podium-score">${escHtml(row[scoreKey] ?? 0)} ${label}</div>
      </article>`;
    } else {
      html += `<article class="podium-card ${cls} empty" style="animation-delay:${visualIdx*70}ms">
        <div class="podium-position">#${pos}</div>
        <div class="podium-rank">${medals[pos-1]}</div>
        <div class="podium-empty-title">TodavÃ­a no hay datos para este puesto</div>
        <div class="podium-score">0 ${label}</div>
      </article>`;
    }
  });

  html += '</div>';

  const rest = rows.filter((row, idx)=>Number(row.posicion || idx + 1) > 3);
  if(rest.length){
    html += '<div class="redis-list-title">Resto del ranking</div>';
    html += '<div class="redis-list">';
    rest.forEach((row,i)=>{
      const pos = Number(row.posicion || i + 4);
      html += `<div class="redis-rank-row" style="animation-delay:${i*40}ms">
        <div class="redis-rank-num">#${escHtml(pos)}</div>
        <div class="redis-rank-name">${escHtml(row[nameKey] || 'â€”')}</div>
        <div class="redis-rank-score">${escHtml(row[scoreKey] ?? 0)} ${label}</div>
      </div>`;
    });
    html += '</div>';
  }

  html += '</div>';
  body.innerHTML = html;
}

function renderSearchCards(rows){
  const body=document.getElementById('results-body');
  let html='<div class="search-timeline">';
  rows.forEach((row,i)=>{
    html += `<div class="search-card" style="animation-delay:${i*45}ms"><span>#${escHtml(row.posicion || i+1)} bÃºsqueda reciente</span><strong>${escHtml(row.termino || 'â€”')}</strong></div>`;
  });
  html+='</div>';
  body.innerHTML=html;
}

function cassLabel(key){
  return String(key).replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
}
function cassTitle(row){
  return row.titulo || row.plato_nombre || row.tipo_comida || row.restaurante || `Registro ${row.promocion_id || row.visita_id || row.restaurante_id || ''}`;
}
function cassBadge(row){
  if(row.descuento !== undefined) return `${row.descuento}% OFF`;
  if(row.cantidad_vendida !== undefined) return `${row.cantidad_vendida} vendidos`;
  if(row.monto !== undefined) return `$${row.monto}`;
  if(row.estado) return row.estado;
  return 'Cassandra';
}
function cassSubtitle(row){
  const parts=[];
  if(row.barrio) parts.push(row.barrio);
  if(row.tipo_comida) parts.push(row.tipo_comida);
  if(row.fecha) parts.push(formatDateValue('fecha', row.fecha));
  if(row.fecha_inicio || row.fecha_fin) parts.push(`${formatDateValue('fecha_inicio', row.fecha_inicio || '')} â†’ ${formatDateValue('fecha_fin', row.fecha_fin || '')}`);
  if(row.restaurante_id !== undefined) parts.push(`Rest. #${row.restaurante_id}`);
  return parts.filter(Boolean).join(' Â· ') || 'Modelo por consulta';
}
function renderCassandraCards(rows){
  const body=document.getElementById('results-body');
  let html='<div class="cass-grid">';
  rows.forEach((row,i)=>{
    const entries = Object.entries(row).map(([k,v]) => [k, formatDateValue(k,v)]);
    const minis = entries.filter(([k]) => ['estado','fecha','fecha_inicio','fecha_fin','dia_vigencia','descuento','monto','cantidad_vendida','total_ingresos','dni_usuario','restaurante_id'].includes(k)).slice(0,4);
    html += `<article class="cass-card" style="animation-delay:${i*45}ms">
      <div class="cass-top">
        <div>
          <h3 class="cass-title">${escHtml(cassTitle(row))}</h3>
          <div class="cass-subtitle">${escHtml(cassSubtitle(row))}</div>
        </div>
        <span class="cass-badge">${escHtml(cassBadge(row))}</span>
      </div>`;
    if(row.descripcion){ html += `<p style="color:var(--text);font-size:13px;line-height:1.45;margin:8px 0 10px;">${escHtml(row.descripcion)}</p>`; }
    if(minis.length){
      html += '<div class="cass-metrics">';
      minis.forEach(([k,v])=>{ html += `<div class="cass-mini"><span>${escHtml(cassLabel(k))}</span><strong>${escHtml(v ?? 'â€”')}</strong></div>`; });
      html += '</div>';
    }
    html += `<details class="cass-details"><summary>Ver detalle completo</summary>`;
    entries.forEach(([k,v])=>{
      html += `<div class="cass-detail-row"><span>${escHtml(cassLabel(k))}</span><span>${escHtml(v ?? 'â€”')}</span></div>`;
    });
    html += `</details></article>`;
  });
  html += '</div>';
  body.innerHTML=html;
}

function renderTableResults(rows){
  const body=document.getElementById('results-body');
  const keys=Object.keys(rows[0]);
  let html=`<table class="results-table"><thead><tr>`;
  keys.forEach(k=>{html+=`<th>${escHtml(k)}</th>`;});
  html+=`</tr></thead><tbody>`;
  rows.forEach((row,i)=>{
    html+=`<tr style="animation-delay:${i*35}ms">`;
    keys.forEach(k=>{
      let val=row[k];
      val = formatDateValue(k, val);
      if(val===null||val===undefined)val='â€”';
      if(k==='puntaje'&&typeof val==='number'){
        const s='â˜…'.repeat(val)+'â˜†'.repeat(5-val);
        html+=`<td><span class="stars">${s}</span> <span style="color:var(--muted);font-size:11px;">(${val})</span></td>`;
      }else if(Array.isArray(val)){
        html+=`<td>${formatArrayCell(val)}</td>`;
      }else if(typeof val==='boolean'){
        html+=`<td><span style="color:${val?'var(--brand)':'#ef4444'};font-weight:700;">${val?'âœ“ SÃ­':'âœ— No'}</span></td>`;
      }else if(k==='posicion'){
        const medals=['ðŸ¥‡','ðŸ¥ˆ','ðŸ¥‰'];
        html+=`<td style="font-weight:700;">${medals[val-1]||('#'+val)}</td>`;
      }else if(k==='ttl_segundos'&&typeof val==='number'){
        const m=Math.floor(val/60),s=val%60;
        html+=`<td style="font-family:'JetBrains Mono',monospace;font-size:11px;">${m}min ${s}seg</td>`;
      }else if(k==='token'&&String(val).length>20){
        const t=String(val);
        html+=`<td style="font-family:'JetBrains Mono',monospace;font-size:11px;">${escHtml(t.slice(0,8))}â€¦${escHtml(t.slice(-8))}</td>`;
      }else{
        html+=`<td>${escHtml(String(val))}</td>`;
      }
    });
    html+='</tr>';
  });
  html+='</tbody></table>';
  body.innerHTML=html;
}

function formatArrayCell(values){
  if(!values.length) return '<span style="color:var(--muted);">—</span>';
  const visible = values.slice(0, 4).map(value => {
    const label = formatComplexValue(value);
    return `<code class="inline">${escHtml(label)}</code>`;
  });
  if(values.length > 4){
    visible.push(`<code class="inline">+${values.length - 4} más</code>`);
  }
  return visible.join(' ');
}

function formatComplexValue(value){
  if(value === null || value === undefined) return '—';
  if(typeof value !== 'object') return String(value);

  if(value.plato_nombre || value.nombre){
    const nombre = value.plato_nombre || value.nombre;
    const precio = value.precio !== undefined ? ` - $${value.precio}` : '';
    return `${nombre}${precio}`;
  }

  if(value.restaurante) return String(value.restaurante);
  if(value.username) return String(value.username);
  if(value.tipo_comida) return String(value.tipo_comida);

  return Object.entries(value)
    .slice(0, 3)
    .map(([key, val]) => `${key}: ${val}`)
    .join(', ');
}

function addNode(graph, id, label, type='user', sub=''){
  if(!id || graph.nodeMap.has(id)) return;
  graph.nodeMap.set(id, { id, label:String(label), type, sub:String(sub||'') });
}
function addLink(graph, source, target, label=''){
  if(!source || !target || source === target) return;
  const key = `${source}->${target}:${label}`;
  if(graph.linkSet.has(key)) return;
  graph.linkSet.add(key);
  graph.links.push({source, target, label});
}
function getParamValue(key, fallback='VitoNava'){
  return lastParams[key] || fallback;
}
function buildGraphFromRows(rows){
  if(currentGraphData && Array.isArray(currentGraphData.nodes) && Array.isArray(currentGraphData.links)){
    return {
      nodes: currentGraphData.nodes.map(n=>({...n})),
      links: currentGraphData.links.map(l=>({...l}))
    };
  }
  const graph = { nodeMap:new Map(), linkSet:new Set(), links:[] };
  const opId = currentOp?.id || '';
  const username = getParamValue('username', rows[0]?.username || getParamValue('follower','VitoNava'));
  const centerId = `user:${username}`;

  if(['perfil','siguiendo','seguidores','visitas-amigos','recomendacion-colaborativa','recomendacion-contenido'].includes(opId)){
    addNode(graph, centerId, username, 'user', 'usuario actual');
  }

  if(opId === 'perfil'){
    const r = rows[0] || {};
    const siguiendoLista = r.siguiendo_usuarios || r.siguiendo_detalle || [];
    const seguidoresLista = r.seguidores_usuarios || r.seguidores_detalle || [];
    const visitasLista = r.visitas_restaurantes || r.visitas_detalle || [];
    const resenasLista = r.resenas_restaurantes || r.resenas_detalle || [];

    siguiendoLista.forEach(u=>{
      const uname = u.username || u.nombre || u;
      const id = `user:${uname}`;
      addNode(graph, id, uname, 'user', u.nombre || 'seguido');
      addLink(graph, centerId, id, 'SIGUE');
    });
    seguidoresLista.forEach(u=>{
      const uname = u.username || u.nombre || u;
      const id = `user:${uname}`;
      addNode(graph, id, uname, 'user', u.nombre || 'seguidor');
      addLink(graph, id, centerId, 'SIGUE');
    });
    visitasLista.forEach(v=>{
      const rest = v.restaurante || v.nombre || v;
      const id = `rest:${rest}`;
      addNode(graph, id, rest, 'restaurant', `${v.tipo_comida || ''} ${v.barrio ? 'Â· '+v.barrio : ''}`.trim());
      addLink(graph, centerId, id, v.fecha ? `VISITÃ“ ${formatDateValue('fecha', v.fecha)}` : 'VISITÃ“');
    });
    resenasLista.forEach(c=>{
      const rest = c.restaurante || c.nombre || c;
      const id = `rest:${rest}`;
      addNode(graph, id, rest, 'restaurant', c.puntaje ? `â˜… ${c.puntaje}` : 'calificado');
      addLink(graph, centerId, id, c.puntaje ? `CALIFICÃ“ ${c.puntaje}` : 'CALIFICÃ“');
    });

    if(graph.nodeMap.size <= 1){
      [['siguiendo','SIGUE A'],['seguidores','LO SIGUEN'],['visitas','VISITÃ“'],['resenas','CALIFICÃ“']].forEach(([k,label])=>{
        const id=`metric:${k}`;
        addNode(graph, id, `${label}\n${r[k] ?? 0}`, 'metric', 'sin detalle');
        addLink(graph, centerId, id, k.toUpperCase());
      });
    }
  } else if(opId === 'siguiendo'){
    rows.forEach(r=>{
      const id=`user:${r.username}`;
      addNode(graph, id, r.username, 'user', r.nombre || 'usuario');
      addLink(graph, centerId, id, 'SIGUE');
    });
  } else if(opId === 'seguidores'){
    rows.forEach(r=>{
      const id=`user:${r.username}`;
      addNode(graph, id, r.username, 'user', r.nombre || 'usuario');
      addLink(graph, id, centerId, 'SIGUE');
    });
  } else if(opId === 'buscar-usuarios'){
    const term = getParamValue('termino', 'bÃºsqueda');
    const searchId = `search:${term}`;
    addNode(graph, searchId, `BÃºsqueda\n${term}`, 'search', 'filtro');
    rows.forEach(r=>{
      const id=`user:${r.username}`;
      addNode(graph, id, r.username, 'user', `${r.nombre || ''} ${r.apellido || ''}`.trim());
      addLink(graph, searchId, id, 'MATCH');
    });
  } else if(opId === 'visitas-amigos'){
    rows.forEach(r=>{
      const amigoId=`user:${r.amigo}`;
      const restId=`rest:${r.restaurante}`;
      addNode(graph, amigoId, r.amigo, 'user', 'amigo');
      addNode(graph, restId, r.restaurante, 'restaurant', r.fecha || 'restaurante');
      addLink(graph, centerId, amigoId, 'SIGUE');
      addLink(graph, amigoId, restId, 'VISITÃ“');
    });
  } else if(opId === 'recomendacion-colaborativa'){
    rows.forEach(r=>{
      const restId=`rest:${r.restaurante}`;
      addNode(graph, restId, r.restaurante, 'restaurant', `${r.tipo_comida || ''} Â· ${r.barrio || ''}`);
      addLink(graph, centerId, restId, 'RECOMENDADO');
      (r.amigos || []).forEach(a=>{
        const amigoId=`user:${a}`;
        addNode(graph, amigoId, a, 'user', 'amigo');
        addLink(graph, centerId, amigoId, 'SIGUE');
        addLink(graph, amigoId, restId, `â˜… ${r.puntaje_amigos ?? ''}`.trim());
      });
    });
  } else if(opId === 'recomendacion-contenido'){
    rows.forEach(r=>{
      const restId=`rest:${r.restaurante}`;
      addNode(graph, restId, r.restaurante, 'restaurant', `${r.tipo_comida || ''} Â· ${r.barrio || ''}`);
      addLink(graph, centerId, restId, 'SIMILAR');
      (r.basado_en || []).forEach(base=>{
        const baseId=`content:${base}`;
        addNode(graph, baseId, base, 'content', 'gustado antes');
        addLink(graph, baseId, restId, 'MISMO TIPO/ZONA');
      });
    });
  } else if(opId === 'seguir'){
    rows.forEach(r=>{
      const aId=`user:${r.de}`;
      const bId=`user:${r.a}`;
      addNode(graph, aId, r.de, 'user', 'origen');
      addNode(graph, bId, r.a, 'user', 'destino');
      addLink(graph, aId, bId, 'SIGUE');
    });
  }

  return { nodes:Array.from(graph.nodeMap.values()).slice(0, 40), links:graph.links.slice(0, 60) };
}

function nodeClass(type){
  if(type === 'restaurant') return 'node-restaurant';
  if(type === 'metric') return 'node-metric';
  if(type === 'search') return 'node-search';
  if(type === 'content') return 'node-content';
  return 'node-user';
}
function shorten(str, max=18){
  str=String(str||'');
  return str.length>max ? str.slice(0,max-1)+'â€¦' : str;
}
function renderGraphResults(rows){
  const body=document.getElementById('results-body');
  const graph=buildGraphFromRows(rows);
  if(!graph.nodes.length){ renderTableResults(rows); return; }

  const w=Math.max(720, body.clientWidth - 260);
  const h=Math.max(360, body.clientHeight - 8);
  const cx=w/2, cy=h/2;
  const centerIndex = graph.nodes.findIndex(n => n.sub === 'usuario actual');
  const center = centerIndex >= 0 ? graph.nodes.splice(centerIndex,1)[0] : graph.nodes.shift();
  const placed=[center, ...graph.nodes];
  const radius=Math.min(w,h)*0.34;
  const positions={ [center.id]: {x:cx, y:cy} };

  graph.nodes.forEach((n,i)=>{
    const angle=(Math.PI*2*i)/Math.max(1,graph.nodes.length) - Math.PI/2;
    const jitter = (i%2)*26;
    positions[n.id]={x:cx+Math.cos(angle)*(radius+jitter), y:cy+Math.sin(angle)*(radius+jitter)};
  });

  let svg=`<svg class="graph-canvas" viewBox="0 0 ${w} ${h}" role="img" aria-label="VisualizaciÃ³n de grafo Neo4j">`;
  svg+=`<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="rgba(126,184,164,.65)" /></marker></defs>`;

  graph.links.forEach(l=>{
    const a=positions[l.source], b=positions[l.target];
    if(!a||!b) return;
    const mx=(a.x+b.x)/2, my=(a.y+b.y)/2;
    svg+=`<line class="graph-link" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" marker-end="url(#arrow)"></line>`;
    svg+=`<text class="graph-link-label" x="${mx}" y="${my-5}" text-anchor="middle">${escHtml(l.label)}</text>`;
  });

  placed.forEach(n=>{
    const p=positions[n.id];
    const isCenter=n.id===center.id;
    const r=isCenter?34:28;
    svg+=`<g class="graph-node ${nodeClass(n.type)}" data-id="${escHtml(n.id)}" data-label="${escHtml(n.label)}" data-type="${escHtml(n.type)}" data-sub="${escHtml(n.sub)}" transform="translate(${p.x},${p.y})">`;
    svg+=`<circle r="${r}"></circle>`;
    const lines=String(n.label).split('\n');
    if(lines.length>1){
      svg+=`<text class="graph-node-label" text-anchor="middle" y="-3">${escHtml(shorten(lines[0],14))}</text>`;
      svg+=`<text class="graph-node-sub" text-anchor="middle" y="12">${escHtml(shorten(lines[1],14))}</text>`;
    } else {
      svg+=`<text class="graph-node-label" text-anchor="middle" y="4">${escHtml(shorten(n.label,16))}</text>`;
    }
    svg+=`</g>`;
  });
  svg+='</svg>';

  body.innerHTML=`<div class="graph-shell">${svg}<aside class="graph-side" id="graph-info"><h3>Grafo Neo4j</h3><p>Esta vista muestra entidades reales devueltas por Neo4j como nodos y relaciones. TocÃ¡ un nodo para ver su detalle.</p><br><p><strong>Nodos:</strong> usuarios reales, restaurantes y recomendaciones.<br><strong>Flechas:</strong> SIGUE, VISITÃ“, CALIFICÃ“ o recomendaciÃ³n.</p></aside></div>`;

  document.querySelectorAll('.graph-node').forEach(node=>{
    node.addEventListener('click',()=>{
      document.getElementById('graph-info').innerHTML=`
        <h3>Detalle del nodo</h3>
        <div class="graph-kv"><span>Nombre</span><span>${escHtml(node.dataset.label)}</span></div>
        <div class="graph-kv"><span>Tipo</span><span>${escHtml(node.dataset.type)}</span></div>
        <div class="graph-kv"><span>Dato</span><span>${escHtml(node.dataset.sub || 'â€”')}</span></div>
        <p style="margin-top:10px;">OperaciÃ³n activa: <strong>${escHtml(currentOp?.title || 'Neo4j')}</strong></p>`;
    });
  });
}


document.addEventListener('DOMContentLoaded', ()=>{
  initResizableResults();
  selectDB('mongo');
});
