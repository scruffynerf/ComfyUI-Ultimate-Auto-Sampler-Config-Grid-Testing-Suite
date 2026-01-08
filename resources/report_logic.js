let activeData = fullManifest.items || [];
let meta = fullManifest.meta || {};
// Removed redundant filters
const filters = { sampler: new Set(), scheduler: new Set(), lora: new Set(), denoise: new Set() };

function init() {
    document.getElementById('meta-model').innerText = meta.model || "-";
    document.getElementById('meta-pos').innerText = meta.positive || "-";
    document.getElementById('meta-neg').innerText = meta.negative || "-";
    document.getElementById('meta-pos').title = meta.positive || "";
    document.getElementById('meta-neg').title = meta.negative || "";
    initFilters();
}

async function saveState() {
    try {
        await fetch('/config_tester/save_manifest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_name: document.getElementById('session-input').value, manifest: fullManifest })
        });
    } catch(e) { console.error("Save failed", e); }
}

async function loadSession() {
    const sess = document.getElementById('session-input').value;
    try {
        const r = await fetch(`/view?filename=manifest.json&type=output&subfolder=benchmarks/${sess}`);
        if(!r.ok) throw new Error("Session not found");
        const data = await r.json();
        fullManifest = data;
        activeData = fullManifest.items || [];
        meta = fullManifest.meta || {};
        init(); 
    } catch(e) { alert("Could not load session: " + e.message); }
}

function rejectItem(id) {
    const item = activeData.find(d => d.id === id);
    if(item) {
        item.rejected = true;
        saveState(); 
        applyFilters();
    }
}

function initFilters() {
    ['sampler', 'scheduler', 'denoise', 'lora'].forEach(key => {
        const unique = [...new Set(activeData.map(d => d[key]))].sort();
        const container = document.getElementById('filter-'+key);
        container.innerHTML = '';
        unique.forEach(val => {
            filters[key].add(val);
            const b = document.createElement('button');
            b.className = `filter-btn active ${key}`;
            let label = val;
            if(key === 'lora') {
                if (val === "None") label = "None";
                else if (val.includes(" + ")) label = "Stack";
                else if (val.length > 10) label = val.substring(0,8)+'...';
            }
            b.innerText = label;
            b.title = val;
            b.onclick = () => {
                if(filters[key].has(val)) { filters[key].delete(val); b.classList.remove('active'); } 
                else { filters[key].add(val); b.classList.add('active'); }
                applyFilters();
            };
            container.appendChild(b);
        });
    });
    applyFilters();
}

function applyFilters() {
    const visible = activeData.filter(d => 
        !d.rejected &&
        filters.sampler.has(d.sampler) && 
        filters.scheduler.has(d.scheduler) && 
        filters.denoise.has(d.denoise) &&
        filters.lora.has(d.lora)
    );
    
    const g = document.getElementById('grid'); g.innerHTML = '';
    visible.forEach(d => {
        const c = document.createElement('div'); c.className = 'card';
        
        let loraLine = "";
        let weightLine = ""; // Only used if specific weights exist in lora string
        
        if (d.lora === "None") {
            loraLine = `<div class="stat"><b>LoRA:</b> <span style="opacity:0.3">-</span></div>`;
        } else if (d.lora.includes(" + ")) {
            const count = d.lora.split(" + ").length;
            loraLine = `<div class="stat" title="${d.lora.replace(/ \+ /g, '\n')}"><b>LoRA:</b> <span style="color:var(--accent-lora)">Stack (${count})</span></div>`;
        } else {
            let cleanName = d.lora.length > 22 ? d.lora.substring(0,20)+'...' : d.lora;
            if(d.lora.includes(":")) {
                    const parts = d.lora.split(":");
                    cleanName = parts[0].length > 15 ? parts[0].substring(0,12)+'...' : parts[0];
                    // Only show weights if they are embedded in the string
                    weightLine = `<div class="stat"><b>Wt:</b> ${(parts[1]||1)} / ${(parts[2]||1)}</div>`;
            }
            loraLine = `<div class="stat" title="${d.lora}"><b>LoRA:</b> <span>${cleanName}</span></div>`;
        }

        c.innerHTML = `
            <div class="time-tag">${d.duration}s</div>
            <button class="reject-btn" onclick="rejectItem(${d.id})">✕</button>
            <button class="revise-btn" onclick="openM(${d.id})">REVISE</button>
            <img src="${d.file}" draggable="false" loading="lazy">
            <div class="info">
                <div class="stat"><b>Smp:</b> <span>${d.sampler} / ${d.scheduler}</span></div>
                <div class="stat"><b>Cfg:</b> ${d.cfg} &nbsp;&nbsp; <b>Steps:</b> ${d.steps}</div>
                <div class="stat"><b>Denoise:</b> <span style="color:var(--accent-denoise)">${d.denoise}</span></div>
                ${loraLine}
                ${weightLine}
            </div>`;
        g.appendChild(c);
    });
    
    updateJSONs(visible);
}

function updateJSONs(visible) {
    generateSmartJSON(visible, 'json-bar-good');
    const rejected = activeData.filter(d => d.rejected);
    generateSmartJSON(rejected, 'json-bar-bad');
}

function generateSmartJSON(dataset, targetId) {
    if(dataset.length === 0) { document.getElementById(targetId).innerText = "[]"; return; }
    
    // --- CLEANED UP: Removed str_model / str_clip from output ---
    let configs = dataset.map(d => ({
        sampler: [d.sampler], scheduler: [d.scheduler], steps: [d.steps],
        cfg: [d.cfg], denoise: [d.denoise], lora: [d.lora]
    }));

    let changed = true;
    while(changed) {
        changed = false;
        for(let i=0; i<configs.length; i++) {
            if(!configs[i]) continue;
            for(let j=i+1; j<configs.length; j++) {
                if(!configs[j]) continue;
                let diffKey = null; let match = true;
                // --- CLEANED UP: Removed keys from comparison list ---
                const keys = ['sampler', 'scheduler', 'steps', 'cfg', 'denoise', 'lora'];
                for(let k of keys) {
                    if(JSON.stringify(configs[i][k].sort()) !== JSON.stringify(configs[j][k].sort())) {
                        if(diffKey === null) diffKey = k; else { match = false; break; }
                    }
                }
                if(match && diffKey) {
                    const merged = [...new Set([...configs[i][diffKey], ...configs[j][diffKey]])];
                    merged.sort((a,b) => (typeof a==='number' && typeof b==='number') ? a-b : (a<b?-1:1));
                    configs[i][diffKey] = merged; configs[j] = null; changed = true; break;
                }
            }
            if(changed) break;
        }
        configs = configs.filter(c => c);
    }
    configs = configs.map(c => {
        let n = {}; for(let k in c) n[k] = c[k].length === 1 ? c[k][0] : c[k]; return n;
    });
    document.getElementById(targetId).innerText = JSON.stringify(configs, null, 2);
}

function selectJSON(id) {
    const r = document.createRange(); r.selectNode(document.getElementById(id));
    window.getSelection().removeAllRanges(); window.getSelection().addRange(r);
}
// --- INTERACTION LOGIC ---
let s = 1, px = 0, py = 0, sx = 0, sy = 0, down = false;
const vp = document.getElementById('viewport'); 
const cv = document.getElementById('canvas');
let lastDist = 0;

function upd() { cv.style.transform = `translate(${px}px, ${py}px) scale(${s})`; }

vp.onmousedown = (e) => { down = true; sx = e.clientX - px; sy = e.clientY - py; };
window.onmouseup = () => { down = false; };
window.onmousemove = (e) => { if(!down) return; px = e.clientX - sx; py = e.clientY - sy; upd(); };

// EXPONENTIAL ZOOM (WHEEL)
vp.onwheel = (e) => { 
    // FIX: Prevent "flicking" by ignoring scroll if user is dragging (panning)
    if(down) return; 

    e.preventDefault(); 
    const x = (e.clientX - px) / s, y = (e.clientY - py) / s; 
    const zoomFactor = Math.exp(-e.deltaY * 0.002);
    s *= zoomFactor;
    s = Math.min(Math.max(0.1, s), 100); 
    px = e.clientX - x * s; 
    py = e.clientY - y * s; 
    upd(); 
};

// KEYBOARD PANNING (ARROWS)
window.addEventListener('keydown', (e) => {
    // Safety: Don't pan if typing in a text box
    if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") return;

    const step = 50; // Pixels per keypress
    switch(e.key) {
        case "ArrowUp":    py += step; break;
        case "ArrowDown":  py -= step; break;
        case "ArrowLeft":  px += step; break;
        case "ArrowRight": px -= step; break;
        default: return; // Exit if not an arrow key
    }
    upd();
});

// PINCH ZOOM (TOUCH)
vp.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
        down = true;
        sx = e.touches[0].clientX - px;
        sy = e.touches[0].clientY - py;
    } else if (e.touches.length === 2) {
        down = false;
        lastDist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
    }
}, {passive: false});

vp.addEventListener('touchmove', (e) => {
    e.preventDefault();
    if (e.touches.length === 1 && down) {
        px = e.touches[0].clientX - sx;
        py = e.touches[0].clientY - sy;
        upd();
    } else if (e.touches.length === 2) {
        const dist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
        
        if (lastDist > 0) {
            const zoomFactor = dist / lastDist;
            const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
            const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
            const wx = (cx - px) / s;
            const wy = (cy - py) / s;

            s *= zoomFactor;
            s = Math.min(Math.max(0.1, s), 100); 
            
            px = cx - wx * s;
            py = cy - wy * s;
        }
        
        lastDist = dist;
        upd();
    }
}, {passive: false});

vp.addEventListener('touchend', () => { down = false; });

// MODAL & LOGIC
function openM(id) {
    const d = activeData.find(x => x.id === id);
    document.getElementById('m-img').src = d.file;
    ['smp','sch','stp','cfg','den','lor'].forEach((k, i) => {
        const keys = ['sampler','scheduler','steps','cfg','denoise','lora'];
        document.getElementById('f-'+k).value = d[keys[i]];
    });
    const r = document.getElementById('reel'); r.innerHTML = '';
    activeData.forEach(x => {
        if(x.rejected) return;
        const i = document.createElement('img'); i.src = x.file; i.onclick = () => openM(x.id); 
        if(x.id === id) i.style.borderColor = "var(--accent)";
        r.appendChild(i);
    });
    document.getElementById('modal').style.display = 'flex';
}
function closeM() { document.getElementById('modal').style.display = 'none'; }

async function triggerGen() {
    const newCfg = [{
        sampler: document.getElementById('f-smp').value,
        scheduler: document.getElementById('f-sch').value,
        steps: parseInt(document.getElementById('f-stp').value),
        cfg: parseFloat(document.getElementById('f-cfg').value),
        denoise: parseFloat(document.getElementById('f-den').value),
        lora: document.getElementById('f-lor').value
    }];
    const jsonStr = JSON.stringify(newCfg, null, 2);
    try {
        const graph = window.parent.app.graph;
        let node = graph.getNodeById(parseInt(TARGET_NODE_ID));
        if(!node) node = graph._nodes.find(n => n.type === "UltimateSamplerGrid");
        if(node) {
            const widget = node.widgets.find(w => w.name === "configs_json");
            if(widget) {
                widget.value = jsonStr;
                window.parent.app.queuePrompt(0);
                const b = event.target; b.innerText = "QUEUED!";
                setTimeout(() => { closeM(); b.innerText = "GENERATE NEW"; }, 1000);
            }
        }
    } catch(e) { alert("Error: " + e); }
}

function toggleSort() {
    const b = document.getElementById('sort-btn');
    if(b.innerText.includes('Newest')) { activeData.sort((a,b)=>a.duration - b.duration); b.innerText = "Sort: Fastest"; }
    else { activeData.sort((a,b)=>b.id - a.id); b.innerText = "Sort: Newest"; }
    applyFilters();
}

init();