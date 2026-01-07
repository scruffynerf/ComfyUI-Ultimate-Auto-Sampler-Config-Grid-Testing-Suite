import re
import os
import json
import folder_paths
from .html_generator import get_html_template

class SamplerConfigDashboardViewer:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "session_name": ("STRING", {"default": "my_session"}),
            },
            "optional": {
                "dashboard_html": ("STRING", {"forceInput": True}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ()
    FUNCTION = "view"
    OUTPUT_NODE = True
    CATEGORY = "sampling/testing"

    def view(self, session_name, unique_id, dashboard_html=None):
        # 1. If we have a fresh generation from the sampler, use it.
        if dashboard_html:
            return {"ui": {"html": [dashboard_html]}}
        
        # --- sanitize ---
        if session_name:
            session_name = re.sub(r'[^\w\-]', '', session_name)
            

        # 2. Otherwise, load from disk (View Mode)
        base_dir = os.path.join(folder_paths.get_output_directory(), "benchmarks", session_name)
        manifest_path = os.path.join(base_dir, "manifest.json")
        
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                html = get_html_template(session_name, manifest, unique_id)
                return {"ui": {"html": [html]}}
            except Exception as e:
                return {"ui": {"html": [f"Error loading session: {e}"]}}
        
        return {"ui": {"html": ["<h3>No session found. Check the session name or generate a new grid.</h3>"]}}