import json

def get_html_template(title, manifest_data, node_id):
    if isinstance(manifest_data, list):
        manifest_data = {"items": manifest_data, "meta": {"model": "", "positive": "", "negative": ""}}
    
    json_str = json.dumps(manifest_data)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    :root {{ --bg: #0b0b0b; --card: #141414; --accent: #00d1b2; --accent-sch: #3e8ed0; --accent-lora: #d0873e; --accent-denoise: #d03e3e; --danger: #ff3860; --text: #e0e0e0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; overflow: hidden; height: 100vh; display: flex; flex-direction: column; touch-action: none; }}
    
    /* HEADER INFO */
    #header {{ background: #111; border-bottom: 1px solid #333; padding: 10px 15px; display: flex; gap: 20px; font-size: 11px; align-items: flex-start; }}
    .meta-box {{ display: flex; flex-direction: column; gap: 2px; flex: 1; }}
    .meta-label {{ color: #666; font-weight: bold; text-transform: uppercase; font-size: 9px; }}
    .meta-val {{ color: #ccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; }}
    
    /* TOOLBAR */
    #toolbar {{ padding: 6px 15px; background: #181818; border-bottom: 1px solid #222; display: flex; gap: 15px; flex-wrap: wrap; z-index: 10; align-items: center; min-height: 36px; box-shadow: 0 2px 10px rgba(0,0,0,0.5); }}
    
    .session-ctrl {{ display: flex; gap: 5px; background: #222; padding: 3px; border-radius: 4px; border: 1px solid #333; }}
    .session-input {{ background: transparent; border: none; color: white; font-size: 11px; width: 100px; padding-left: 5px; }}
    
    .filter-group {{ display: flex; gap: 4px; align-items: center; }}
    .filter-label {{ font-size: 10px; font-weight: 700; color: #555; text-transform: uppercase; margin-right: 4px; }}
    .filter-btn {{ background: #222; border: 1px solid #333; color: #666; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px; transition: 0.1s; }}
    .filter-btn.active.sampler {{ background: var(--accent); color: #000; font-weight: 700; }}
    .filter-btn.active.scheduler {{ background: var(--accent-sch); color: #000; font-weight: 700; }}
    .filter-btn.active.lora {{ background: var(--accent-lora); color: #000; font-weight: 700; }}
    .filter-btn.active.denoise {{ background: var(--accent-denoise); color: #fff; font-weight: 700; }}
    
    .action-btn {{ background: #2a2a2a; color: #fff; border: 1px solid #444; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 11px; }}
    .action-btn:hover {{ background: #444; }}

    /* VIEWPORT */
    #viewport {{ flex-grow: 1; overflow: hidden; position: relative; background: radial-gradient(#222 1px, transparent 1px); background-size: 30px 30px; cursor: grab; touch-action: none; }}
    #viewport:active {{ cursor: grabbing; }}
    #canvas {{ transform-origin: 0 0; position: absolute; padding: 100px; transition: transform 0.05s linear; will-change: transform; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; width: 100vw; }}
    
    /* CARDS */
    .card {{ background: var(--card); border: 1px solid #222; border-radius: 8px; overflow: hidden; position: relative; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
    .card img {{ width: 100%; display: block; }}
    
    .time-tag {{ position: absolute; bottom: 100px; right: 5px; background: rgba(0,0,0,0.8); color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; pointer-events: none; }}
    
    .revise-btn {{ position: absolute; top: 5px; right: 5px; background: var(--accent); color: #000; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px; cursor: pointer; opacity: 0.8; transition: 0.2s; }}
    .reject-btn {{ position: absolute; top: 5px; left: 5px; background: var(--danger); color: #fff; border: none; width: 24px; height: 24px; border-radius: 50%; font-weight: bold; font-size: 14px; cursor: pointer; opacity: 0.8; transition: 0.2s; display:flex; align-items:center; justify-content:center; }}
    .card:hover .revise-btn, .card:hover .reject-btn {{ opacity: 1; }}
    
    .info {{ padding: 10px; font-size: 10px; line-height: 1.4; color: #ccc; }}
    .stat {{ display: flex; justify-content: space-between; border-bottom: 1px solid #222; padding-bottom: 2px; margin-bottom: 2px; }}
    .stat b {{ color: #888; font-weight: 600; margin-right:5px; }}
    .stat span {{ text-align:right; color: #eee; }}

    /* JSON BARS */
    .json-container {{ display:flex; flex-direction:column; }}
    .json-bar {{ height: 60px; padding: 10px; font-family: 'Consolas', monospace; font-size: 11px; overflow: auto; white-space: pre-wrap; cursor: text; border-top: 1px solid #333; }}
    #json-bar-good {{ background: #080808; color: #6a9955; }}
    #json-bar-bad {{ background: #150505; color: #ff6b6b; height: 40px; border-top: 1px solid #500; }}
    
    .bar-label {{ font-size:9px; font-weight:bold; opacity:0.5; margin-bottom:4px; text-transform:uppercase; }}

    /* MODAL */
    #modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; padding: 20px; }}
    .modal-main {{ display: flex; gap: 20px; height: 60%; width: 100%; }}
    .preview {{ flex: 2; display: flex; justify-content: center; background: #000; border-radius: 8px; overflow: hidden; }}
    .preview img {{ height: 100%; width: auto; object-fit: contain; }}
    .controls {{ flex: 1; background: #111; padding: 20px; border-radius: 8px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; }}
    .field {{ display: flex; flex-direction: column; gap: 4px; }}
    .field label {{ color: #888; font-size: 10px; font-weight: bold; text-transform: uppercase; }}
    .field input {{ background: #000; border: 1px solid #333; color: #fff; padding: 8px; font-size: 14px; }}
    
    .reel-wrap {{ margin-top: 20px; height: 30%; display: flex; flex-direction: column; gap: 5px; }}
    .reel {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; height: 100%; align-items: center; }}
    .reel img {{ height: 90%; border-radius: 6px; cursor: pointer; border: 2px solid transparent; }}
    .reel img:hover {{ transform: scale(1.05); border-color: var(--accent); }}
    
    @media (max-width: 800px) {{
        .modal-main {{ flex-direction: column; height: auto; }}
        .preview {{ height: 300px; flex: none; }}
    }}
</style>
</head>
<body>

<div id="header">
    <div class="meta-box"><div class="meta-label">Model</div><div class="meta-val" id="meta-model"></div></div>
    <div class="meta-box"><div class="meta-label">Positive</div><div class="meta-val" id="meta-pos"></div></div>
    <div class="meta-box"><div class="meta-label">Negative</div><div class="meta-val" id="meta-neg"></div></div>
</div>

<div id="toolbar">
    <div class="session-ctrl">
        <input id="session-input" class="session-input" value="{title}">
        <button class="action-btn" onclick="loadSession()">LOAD</button>
    </div>

    <div style="width:1px; height:20px; background:#333; margin:0 5px;"></div>
    <button class="action-btn" onclick="toggleSort()" id="sort-btn">Sort: Newest</button>
    
    <div style="width:1px; height:20px; background:#333; margin:0 5px;"></div>
    <div class="filter-group"><span class="filter-label">Smp</span><div id="filter-sampler" style="display:flex; gap:2px;"></div></div>
    <div class="filter-group"><span class="filter-label">Sch</span><div id="filter-scheduler" style="display:flex; gap:2px;"></div></div>
    <div class="filter-group"><span class="filter-label">Den</span><div id="filter-denoise" style="display:flex; gap:2px;"></div></div>
    <div class="filter-group"><span class="filter-label">LoRA</span><div id="filter-lora" style="display:flex; gap:2px;"></div></div>
    
    <div style="flex-grow:1"></div>
</div>

<div id="viewport">
    <div id="canvas"><div class="grid" id="grid"></div></div>
</div>

<div class="json-container">
    <div id="json-bar-good" class="json-bar" title="ACCEPTED CONFIGS" onclick="selectJSON('json-bar-good')">[]</div>
    <div id="json-bar-bad" class="json-bar" title="REJECTED CONFIGS" onclick="selectJSON('json-bar-bad')">[]</div>
</div>

<div id="modal">
    <div class="modal-main">
        <div class="preview"><img id="m-img" src=""></div>
        <div class="controls">
            <h2 style="margin:0 0 10px 0; color:#fff;">Revise & Generate</h2>
            <div class="field"><label>Sampler</label><input id="f-smp"></div>
            <div class="field"><label>Scheduler</label><input id="f-sch"></div>
            <div class="field"><label>Steps</label><input id="f-stp" type="number"></div>
            <div class="field"><label>CFG</label><input id="f-cfg" type="number" step="0.5"></div>
            <div class="field"><label>Denoise</label><input id="f-den" type="number" step="0.05"></div>
            <div class="field"><label>LoRA</label><input id="f-lor"></div>
            <div class="field"><label>Model Wt</label><input id="f-wm" type="number" step="0.1"></div>
            <div class="field"><label>Clip Wt</label><input id="f-wc" type="number" step="0.1"></div>
            <div style="margin-top:auto; display:flex; gap:10px;">
                <button class="action-btn" style="flex:2; background:var(--accent); color:#000; border:none; height:36px; font-weight:800" onclick="triggerGen()">GENERATE NEW</button>
                <button class="action-btn" style="flex:1" onclick="closeM()">CANCEL</button>
            </div>
        </div>
    </div>
    <div class="reel-wrap">
        <div style="font-size:10px; font-weight:bold; color:#666;">RELATED VARIANTS</div>
        <div class="reel" id="reel"></div>
    </div>
</div>

<script>
    let fullManifest = {json_str};
    let activeData = fullManifest.items || [];
    let meta = fullManifest.meta || {{}};
    const TARGET_NODE_ID = "{node_id}"; 
    const filters = {{ sampler: new Set(), scheduler: new Set(), lora: new Set(), denoise: new Set() }};

    function init() {{
        document.getElementById('meta-model').innerText = meta.model || "-";
        document.getElementById('meta-pos').innerText = meta.positive || "-";
        document.getElementById('meta-neg').innerText = meta.negative || "-";
        document.getElementById('meta-pos').title = meta.positive || "";
        document.getElementById('meta-neg').title = meta.negative || "";
        initFilters();
    }}

    async function saveState() {{
        try {{
            await fetch('/config_tester/save_manifest', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ session_name: document.getElementById('session-input').value, manifest: fullManifest }})
            }});
        }} catch(e) {{ console.error("Save failed", e); }}
    }}

    async function loadSession() {{
        const sess = document.getElementById('session-input').value;
        try {{
            const r = await fetch(`/view?filename=manifest.json&type=output&subfolder=benchmarks/${{sess}}`);
            if(!r.ok) throw new Error("Session not found");
            const data = await r.json();
            fullManifest = data;
            activeData = fullManifest.items || [];
            meta = fullManifest.meta || {{}};
            init(); 
        }} catch(e) {{ alert("Could not load session: " + e.message); }}
    }}

    function rejectItem(id) {{
        const item = activeData.find(d => d.id === id);
        if(item) {{
            item.rejected = true;
            saveState(); 
            applyFilters();
        }}
    }}
    
    function initFilters() {{
        ['sampler', 'scheduler', 'denoise', 'lora'].forEach(key => {{
            const unique = [...new Set(activeData.map(d => d[key]))].sort();
            const container = document.getElementById('filter-'+key);
            container.innerHTML = '';
            unique.forEach(val => {{
                filters[key].add(val);
                const b = document.createElement('button');
                b.className = `filter-btn active ${{key}}`;
                let label = val;
                if(key === 'lora') {{
                    if (val === "None") label = "None";
                    else if (val.includes(" + ")) label = "Stack";
                    else if (val.length > 10) label = val.substring(0,8)+'...';
                }}
                b.innerText = label;
                b.title = val; // Tooltip shows full value
                b.onclick = () => {{
                    if(filters[key].has(val)) {{ filters[key].delete(val); b.classList.remove('active'); }} 
                    else {{ filters[key].add(val); b.classList.add('active'); }}
                    applyFilters();
                }};
                container.appendChild(b);
            }});
        }});
        applyFilters();
    }}

    function applyFilters() {{
        const visible = activeData.filter(d => 
            !d.rejected &&
            filters.sampler.has(d.sampler) && 
            filters.scheduler.has(d.scheduler) && 
            filters.denoise.has(d.denoise) &&
            filters.lora.has(d.lora)
        );
        
        const g = document.getElementById('grid'); g.innerHTML = '';
        visible.forEach(d => {{
            const c = document.createElement('div'); c.className = 'card';
            
            // --- SMART LORA DISPLAY ---
            let loraLine = "";
            let weightLine = "";
            
            if (d.lora === "None") {{
                loraLine = `<div class="stat"><b>LoRA:</b> <span style="opacity:0.3">-</span></div>`;
            }} else if (d.lora.includes(" + ")) {{
                // Stack Mode
                const count = d.lora.split(" + ").length;
                loraLine = `<div class="stat" title="${{d.lora.replace(/ \+ /g, '\\n')}}"><b>LoRA:</b> <span style="color:var(--accent-lora)">Stack (${{count}})</span></div>`;
                weightLine = `<div class="stat"><b style="opacity:0.5">Weights:</b> <span style="font-size:9px; opacity:0.7">Mixed (See Tooltip)</span></div>`;
            }} else {{
                // Single Mode
                let cleanName = d.lora.length > 22 ? d.lora.substring(0,20)+'...' : d.lora;
                // Check if name has embedded weights
                if(d.lora.includes(":")) {{
                     const parts = d.lora.split(":");
                     cleanName = parts[0].length > 15 ? parts[0].substring(0,12)+'...' : parts[0];
                     weightLine = `<div class="stat"><b>Wt:</b> ${{(parts[1]||1)}} / ${{(parts[2]||1)}}</div>`;
                }} else {{
                     weightLine = `<div class="stat"><b>Wt:</b> ${{d.str_model}} / ${{d.str_clip}}</div>`;
                }}
                loraLine = `<div class="stat" title="${{d.lora}}"><b>LoRA:</b> <span>${{cleanName}}</span></div>`;
            }}

            c.innerHTML = `
                <div class="time-tag">${{d.duration}}s</div>
                <button class="reject-btn" onclick="rejectItem(${{d.id}})">✕</button>
                <button class="revise-btn" onclick="openM(${{d.id}})">REVISE</button>
                <img src="${{d.file}}" draggable="false" loading="lazy">
                <div class="info">
                    <div class="stat"><b>Smp:</b> <span>${{d.sampler}} / ${{d.scheduler}}</span></div>
                    <div class="stat"><b>Cfg:</b> ${{d.cfg}} &nbsp;&nbsp; <b>Steps:</b> ${{d.steps}}</div>
                    <div class="stat"><b>Denoise:</b> <span style="color:var(--accent-denoise)">${{d.denoise}}</span></div>
                    ${{loraLine}}
                    ${{weightLine}}
                </div>`;
            g.appendChild(c);
        }});
        
        updateJSONs(visible);
    }}

    function updateJSONs(visible) {{
        generateSmartJSON(visible, 'json-bar-good');
        const rejected = activeData.filter(d => d.rejected);
        generateSmartJSON(rejected, 'json-bar-bad');
    }}

    function generateSmartJSON(dataset, targetId) {{
        if(dataset.length === 0) {{ document.getElementById(targetId).innerText = "[]"; return; }}
        let configs = dataset.map(d => ({{
            sampler: [d.sampler], scheduler: [d.scheduler], steps: [d.steps],
            cfg: [d.cfg], denoise: [d.denoise], lora: [d.lora], str_model: [d.str_model], str_clip: [d.str_clip]
        }}));

        let changed = true;
        while(changed) {{
            changed = false;
            for(let i=0; i<configs.length; i++) {{
                if(!configs[i]) continue;
                for(let j=i+1; j<configs.length; j++) {{
                    if(!configs[j]) continue;
                    let diffKey = null; let match = true;
                    const keys = ['sampler', 'scheduler', 'steps', 'cfg', 'denoise', 'lora', 'str_model', 'str_clip'];
                    for(let k of keys) {{
                        if(JSON.stringify(configs[i][k].sort()) !== JSON.stringify(configs[j][k].sort())) {{
                            if(diffKey === null) diffKey = k; else {{ match = false; break; }}
                        }}
                    }}
                    if(match && diffKey) {{
                        const merged = [...new Set([...configs[i][diffKey], ...configs[j][diffKey]])];
                        merged.sort((a,b) => (typeof a==='number' && typeof b==='number') ? a-b : (a<b?-1:1));
                        configs[i][diffKey] = merged; configs[j] = null; changed = true; break;
                    }}
                }}
                if(changed) break;
            }}
            configs = configs.filter(c => c);
        }}
        configs = configs.map(c => {{
            let n = {{}}; for(let k in c) n[k] = c[k].length === 1 ? c[k][0] : c[k]; return n;
        }});
        document.getElementById(targetId).innerText = JSON.stringify(configs, null, 2);
    }}

    function selectJSON(id) {{
        const r = document.createRange(); r.selectNode(document.getElementById(id));
        window.getSelection().removeAllRanges(); window.getSelection().addRange(r);
    }}

    // --- INTERACTION LOGIC (EXPONENTIAL ZOOM) ---
    let s = 1, px = 0, py = 0, sx = 0, sy = 0, down = false;
    const vp = document.getElementById('viewport'); 
    const cv = document.getElementById('canvas');
    let lastDist = 0;

    function upd() {{ cv.style.transform = `translate(${{px}}px, ${{py}}px) scale(${{s}})`; }}

    vp.onmousedown = (e) => {{ down = true; sx = e.clientX - px; sy = e.clientY - py; }};
    window.onmouseup = () => {{ down = false; }};
    window.onmousemove = (e) => {{ if(!down) return; px = e.clientX - sx; py = e.clientY - sy; upd(); }};

    // --- NEW: EXPONENTIAL ZOOM (WHEEL) ---
    vp.onwheel = (e) => {{ 
        e.preventDefault(); 
        const x = (e.clientX - px) / s, y = (e.clientY - py) / s; 
        
        // Use multiplication for exponential zoom feeling
        // Adjust sensitivity (0.002) as needed
        const zoomFactor = Math.exp(-e.deltaY * 0.002);
        s *= zoomFactor;
        
        // Clamp to 100x max
        s = Math.min(Math.max(0.1, s), 100); 

        px = e.clientX - x * s; 
        py = e.clientY - y * s; 
        upd(); 
    }};

    // --- NEW: PINCH ZOOM (TOUCH) ---
    vp.addEventListener('touchstart', (e) => {{
        if (e.touches.length === 1) {{
            down = true;
            sx = e.touches[0].clientX - px;
            sy = e.touches[0].clientY - py;
        }} else if (e.touches.length === 2) {{
            down = false;
            lastDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
        }}
    }}, {{passive: false}});

    vp.addEventListener('touchmove', (e) => {{
        e.preventDefault();
        if (e.touches.length === 1 && down) {{
            px = e.touches[0].clientX - sx;
            py = e.touches[0].clientY - sy;
            upd();
        }} else if (e.touches.length === 2) {{
            const dist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            
            // Calculate ratio for smooth pinch zoom
            if (lastDist > 0) {{
                const zoomFactor = dist / lastDist;
                
                const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
                const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
                const wx = (cx - px) / s;
                const wy = (cy - py) / s;

                s *= zoomFactor;
                s = Math.min(Math.max(0.1, s), 100); // 100x Limit
                
                px = cx - wx * s;
                py = cy - wy * s;
            }}
            
            lastDist = dist;
            upd();
        }}
    }}, {{passive: false}});

    vp.addEventListener('touchend', () => {{ down = false; }});

    // --- MODAL & LOGIC ---
    function openM(id) {{
        const d = activeData.find(x => x.id === id);
        document.getElementById('m-img').src = d.file;
        ['smp','sch','stp','cfg','den','lor','wm','wc'].forEach((k, i) => {{
            const keys = ['sampler','scheduler','steps','cfg','denoise','lora','str_model','str_clip'];
            document.getElementById('f-'+k).value = d[keys[i]];
        }});
        const r = document.getElementById('reel'); r.innerHTML = '';
        activeData.forEach(x => {{
            if(x.rejected) return;
            const i = document.createElement('img'); i.src = x.file; i.onclick = () => openM(x.id); 
            if(x.id === id) i.style.borderColor = "var(--accent)";
            r.appendChild(i);
        }});
        document.getElementById('modal').style.display = 'flex';
    }}
    function closeM() {{ document.getElementById('modal').style.display = 'none'; }}
    async function triggerGen() {{
        const newCfg = [{{
            sampler: document.getElementById('f-smp').value,
            scheduler: document.getElementById('f-sch').value,
            steps: parseInt(document.getElementById('f-stp').value),
            cfg: parseFloat(document.getElementById('f-cfg').value),
            denoise: parseFloat(document.getElementById('f-den').value),
            lora: document.getElementById('f-lor').value,
            str_model: parseFloat(document.getElementById('f-wm').value),
            str_clip: parseFloat(document.getElementById('f-wc').value)
        }}];
        const jsonStr = JSON.stringify(newCfg, null, 2);
        try {{
            const graph = window.parent.app.graph;
            let node = graph.getNodeById(parseInt(TARGET_NODE_ID));
            if(!node) node = graph._nodes.find(n => n.type === "UltimateSamplerGrid");
            if(node) {{
                const widget = node.widgets.find(w => w.name === "configs_json");
                if(widget) {{
                    widget.value = jsonStr;
                    window.parent.app.queuePrompt(0);
                    const b = event.target; b.innerText = "QUEUED!";
                    setTimeout(() => {{ closeM(); b.innerText = "GENERATE NEW"; }}, 1000);
                }}
            }}
        }} catch(e) {{ alert("Error: " + e); }}
    }}
    function toggleSort() {{
        const b = document.getElementById('sort-btn');
        if(b.innerText.includes('Newest')) {{ activeData.sort((a,b)=>a.duration - b.duration); b.innerText = "Sort: Fastest"; }}
        else {{ activeData.sort((a,b)=>b.id - a.id); b.innerText = "Sort: Newest"; }}
        applyFilters();
    }}

    init();
</script>
</body>
</html>
"""