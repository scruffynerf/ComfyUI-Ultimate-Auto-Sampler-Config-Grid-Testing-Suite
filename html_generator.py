import os
import json

def get_html_template(title, manifest_data, node_id):
    # 1. Normalize Data
    if isinstance(manifest_data, list):
        manifest_data = {"items": manifest_data, "meta": {"model": "", "positive": "", "negative": ""}}
    
    json_str = json.dumps(manifest_data)

    # 2. Resolve File Paths
    current_dir = os.path.dirname(__file__)
    resource_dir = os.path.join(current_dir, "resources")
    
    path_html = os.path.join(resource_dir, "template.html")
    path_css = os.path.join(resource_dir, "report.css")      # <--- RENAMED
    path_js = os.path.join(resource_dir, "report_logic.js")  # <--- RENAMED

    # 3. Load Resources
    try:
        with open(path_html, "r", encoding="utf-8") as f: html_template = f.read()
        with open(path_css, "r", encoding="utf-8") as f: css_content = f.read()
        with open(path_js, "r", encoding="utf-8") as f: js_content = f.read()
    except FileNotFoundError as e:
        return f"<h1>Error: Resource files not found.</h1><p>{e}</p>"

    # 4. Inject Data
    final_html = html_template \
        .replace("__TITLE__", str(title)) \
        .replace("__NODE_ID__", str(node_id)) \
        .replace("__JSON_DATA__", json_str) \
        .replace("__CSS_CONTENT__", css_content) \
        .replace("__JS_CONTENT__", js_content)

    return final_html