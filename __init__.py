import server
from aiohttp import web
import json
import os
import folder_paths
from .sampler_node import SamplerGridTester
from .dashboard_node import SamplerConfigDashboardViewer
from .html_generator import get_html_template

# --- API: SAVE MANIFEST ---
@server.PromptServer.instance.routes.post("/config_tester/save_manifest")
async def save_manifest(request):
    try:
        data = await request.json()
        session_name = data.get("session_name")
        manifest_data = data.get("manifest")
        
        if not session_name or not manifest_data:
            return web.Response(status=400, text="Missing session_name or manifest")

        base_dir = os.path.join(folder_paths.get_output_directory(), "benchmarks", session_name)
        os.makedirs(base_dir, exist_ok=True)
        manifest_path = os.path.join(base_dir, "manifest.json")

        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=4)
            
        return web.Response(status=200, text="Saved")
    except Exception as e:
        print(f"[ConfigTester] Error saving manifest: {e}")
        return web.Response(status=500, text=str(e))

# --- API: FETCH SESSION HTML ---
@server.PromptServer.instance.routes.post("/config_tester/get_session_html")
async def get_session_html(request):
    try:
        data = await request.json()
        session_name = data.get("session_name")
        node_id = data.get("node_id", "0") # Fallback ID

        base_dir = os.path.join(folder_paths.get_output_directory(), "benchmarks", session_name)
        manifest_path = os.path.join(base_dir, "manifest.json")

        if not os.path.exists(manifest_path):
             return web.Response(status=404, text=f"Session '{session_name}' not found.")

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Generate HTML on the fly
        html = get_html_template(session_name, manifest, node_id)
        return web.Response(status=200, text=html)

    except Exception as e:
        return web.Response(status=500, text=str(e))

# --- MAPPINGS ---
NODE_CLASS_MAPPINGS = {
    # It is often good practice to prefix your internal keys to avoid collisions
    "UltimateSamplerGrid": SamplerGridTester,
    "UltimateGridDashboard": SamplerConfigDashboardViewer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UltimateSamplerGrid": "Ultimate Sampler Grid (Generator)",
    "UltimateGridDashboard": "Ultimate Grid Dashboard (Viewer)"
}

WEB_DIRECTORY = "./web"