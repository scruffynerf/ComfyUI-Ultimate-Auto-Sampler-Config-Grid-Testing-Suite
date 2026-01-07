import json

def get_html_template(title, manifest_data, node_id):
    # Ensure backward compatibility if manifest is just a list
    if isinstance(manifest_data, list):
        manifest_data = {"items": manifest_data, "meta": {"model": "", "positive": "", "negative": ""}}
    
    json_str = json.dumps(manifest_data)

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    :root {{ --bg: #0b0b0b; --card: #141414; --accent: #00d1b2; --accent-sch: #3e8ed0; --accent-lora: #d0873e; --danger: #ff3860; --text: #e0e0e0; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }}
    
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
    
    .action-btn {{ background: #2a2a2a; color: #fff; border: 1px solid #444; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 11px; }}
    .action-btn:hover {{ background: #444; }}

    /* VIEWPORT */
    #viewport {{ flex-grow: 1; overflow: hidden; position: relative; background: radial-gradient(#222 1px, transparent 1px); background-size: 30px 30px; cursor: grab; }}
    #viewport:active {{ cursor: grabbing; }}
    #canvas {{ transform-origin: 0 0; position: absolute; padding: 100px; transition: transform 0.1s; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; width: 100vw; }}
    
    /* CARDS */
    .card {{ background: var(--card); border: 1px solid #222; border-radius: 8px; overflow: hidden; position: relative; box-shadow: 0 4px 10px rgba(0,0,0,0.5); transition: transform 0.1s; }}
    .card:hover {{ transform: scale(1.02); border-color: #555; z-index: 5; }}
    .card img {{ width: 100%; display: block; }}
    
    .time-tag {{ position: absolute; bottom: 100px; right: 5px; background: rgba(0,0,0,0.8); color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; pointer-events: none; }}
    
    .revise-btn {{ position: absolute; top: 5px; right: 5px; background: var(--accent); color: #000; border: none; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px; cursor: pointer; opacity: 0; transition: 0.2s; }}
    .reject-btn {{ position: absolute; top: 5px; left: 5px; background: var(--danger); color: #fff; border: none; width: 20px; height: 20px; border-radius: 50%; font-weight: bold; font-size: 12px; cursor: pointer; opacity: 0; transition: 0.2s; display:flex; align-items:center; justify-content:center; }}
    .card:hover .revise-btn, .card:hover .reject-btn {{ opacity: 1; }}
    
    .info {{ padding: 10px; font-size: 10px; line-height: 1.4; color: #ccc; }}
    .stat {{ display: flex; justify-content: space-between; border-bottom: 1px solid #222; padding-bottom: 2px; margin-bottom: 2px; }}
    .stat b {{ color: var(--accent); font-weight: 600; }}

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
    .field input {{ background: #000; border: 1px solid #333; color: #fff; padding: 6px; font-size: 12px; }}
    
    .reel-wrap {{ margin-top: 20px; height: 30%; display: flex; flex-direction: column; gap: 5px; }}
    .reel {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; height: 100%; align-items: center; }}
    .reel img {{ height: 90%; border-radius: 6px; cursor: pointer; border: 2px solid transparent; }}
    .reel img:hover {{ transform: scale(1.05); border-color: var(--accent); }}
    
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
    const filters = {{ sampler: new Set(), scheduler: new Set(), lora: new Set() }};

    // --- INIT ---
    function init() {{
        document.getElementById('meta-model').innerText = meta.model || "-";
        document.getElementById('meta-pos').innerText = meta.positive || "-";
        document.getElementById('meta-neg').innerText = meta.negative || "-";
        document.getElementById('meta-pos').title = meta.positive || "";
        document.getElementById('meta-neg').title = meta.negative || "";
        initFilters();
    }}

    // --- SERVER SYNC ---
    async function saveState() {{
        // Save back to server
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
        // Try to fetch manifest for new session
        try {{
            const r = await fetch(`/view?filename=manifest.json&type=output&subfolder=benchmarks/${{sess}}`);
            if(!r.ok) throw new Error("Session not found");
            const data = await r.json();
            
            // RELOAD STATE
            fullManifest = data;
            activeData = fullManifest.items || [];
            meta = fullManifest.meta || {{}};
            init(); // Re-init UI
            
        }} catch(e) {{ alert("Could not load session: " + e.message); }}
    }}

    // --- REJECTION LOGIC ---
    function rejectItem(id) {{
        const item = activeData.find(d => d.id === id);
        if(item) {{
            item.rejected = true;
            saveState(); // Persist change
            applyFilters();
        }}
    }}
    
    // --- FILTERS ---
    function initFilters() {{
        ['sampler', 'scheduler', 'lora'].forEach(key => {{
            const unique = [...new Set(activeData.map(d => d[key]))].sort();
            const container = document.getElementById('filter-'+key);
            container.innerHTML = '';
            unique.forEach(val => {{
                filters[key].add(val);
                const b = document.createElement('button');
                b.className = `filter-btn active ${{key}}`;
                let label = val;
                if(key === 'lora' && val.length > 15 && val !== "None") label = val.substring(0,12)+'...';
                b.innerText = label;
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
        // Filter: Match toggles AND Not Rejected
        const visible = activeData.filter(d => 
            !d.rejected &&
            filters.sampler.has(d.sampler) && 
            filters.scheduler.has(d.scheduler) && 
            filters.lora.has(d.lora)
        );
        
        // Render Good Grid
        const g = document.getElementById('grid'); g.innerHTML = '';
        visible.forEach(d => {{
            const c = document.createElement('div'); c.className = 'card';
            let loraName = d.lora.length > 20 ? d.lora.substring(0,18)+'...' : d.lora;
            if(d.lora === "None") loraName = "-";
            c.innerHTML = `
                <div class="time-tag">${{d.duration}}s</div>
                <button class="reject-btn" onclick="rejectItem(${{d.id}})">✕</button>
                <button class="revise-btn" onclick="openM(${{d.id}})">REVISE</button>
                <img src="${{d.file}}" draggable="false" loading="lazy">
                <div class="info">
                    <div class="stat"><b>${{d.sampler}}</b><span>${{d.scheduler}}</span></div>
                    <div class="stat"><b>Steps:</b> ${{d.steps}} <b>CFG:</b> ${{d.cfg}}</div>
                    <div class="stat"><b>LoRA:</b> <span title="${{d.lora}}">${{loraName}}</span></div>
                    <div class="stat"><b>Wt:</b> ${{d.str_model}} / ${{d.str_clip}}</div>
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
            cfg: [d.cfg], lora: [d.lora], str_model: [d.str_model], str_clip: [d.str_clip]
        }}));

        let changed = true;
        while(changed) {{
            changed = false;
            for(let i=0; i<configs.length; i++) {{
                if(!configs[i]) continue;
                for(let j=i+1; j<configs.length; j++) {{
                    if(!configs[j]) continue;
                    let diffKey = null; let match = true;
                    const keys = ['sampler', 'scheduler', 'steps', 'cfg', 'lora', 'str_model', 'str_clip'];
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

    // --- VIEWPORT / MODAL logic same as before (omitted for brevity, keep existing) ---
    // (Include the existing viewport mouse logic and openM/closeM/triggerGen here)
    // ...
    let s = 1, px = 0, py = 0, sx = 0, sy = 0, down = false;
    const vp = document.getElementById('viewport'); const cv = document.getElementById('canvas');
    vp.onmousedown = (e) => {{ down = true; sx = e.clientX - px; sy = e.clientY - py; }};
    window.onmouseup = () => {{ down = false; }};
    window.onmousemove = (e) => {{ if(!down) return; px = e.clientX - sx; py = e.clientY - sy; upd(); }};
    vp.onwheel = (e) => {{ e.preventDefault(); const x = (e.clientX - px) / s, y = (e.clientY - py) / s; s += -e.deltaY * 0.001; s = Math.min(Math.max(.1, s), 4); px = e.clientX - x * s; py = e.clientY - y * s; upd(); }};
    function upd() {{ cv.style.transform = `translate(${{px}}px, ${{py}}px) scale(${{s}})`; }}

    function openM(id) {{
        const d = activeData.find(x => x.id === id);
        document.getElementById('m-img').src = d.file;
        ['smp','sch','stp','cfg','lor','wm','wc'].forEach((k, i) => {{
            const keys = ['sampler','scheduler','steps','cfg','lora','str_model','str_clip'];
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
                }} else alert("Error: widget not found");
            }} else alert("Error: node not found");
        }} catch(e) {{ alert("Connection Error: " + e); }}
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