import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "UltimateGrid.Dashboard",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "UltimateGridDashboard") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                this.resizable = true;
                const node = this;

                // --- HELPER: GET SESSION NAME ---
                const getSessionName = () => {
                    const w = node.widgets.find(w => w.name === "session_name");
                    return w ? w.value : null;
                };

                // --- LOAD BUTTON ---
                this.addWidget("button", "RELOAD / SHOW SESSION", null, () => {
                    const s = getSessionName();
                    if(s) fetchSession(s);
                });

                // --- DELETE BUTTON ---
                this.addWidget("button", "DELETE SESSION (Files)", null, async () => {
                    const s = getSessionName();
                    if (!s) return alert("No session name set.");
                    
                    if (confirm(`ARE YOU SURE?\n\nThis will PERMANENTLY delete the folder:\n/benchmarks/${s}\n\nand all images inside it.`)) {
                        try {
                            const resp = await fetch("/config_tester/delete_session", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ session_name: s })
                            });
                            
                            if (resp.ok) {
                                // alert("Session Deleted.");
                                node.iframe.srcdoc = "<h3 style='color:#888; text-align:center; padding:20px;'>Session Deleted.</h3>";
                            } else {
                                alert("Error: " + await resp.text());
                            }
                        } catch(e) { alert("Connection Error: " + e); }
                    }
                });

                // --- AUTO-UPDATE WIDGET LOGIC ---
                this.onExecuted = function (message) {
                    // 1. Load HTML
                    if (message?.html) {
                        node.iframe.srcdoc = message.html[0];
                    }
                    
                    // 2. Auto-Update Session Name Widget
                    if (message?.update_session_name && message.update_session_name[0]) {
                        const newName = message.update_session_name[0];
                        const w = node.widgets.find(w => w.name === "session_name");
                        if (w) {
                            w.value = newName;
                            // Trigger re-draw to show new text
                            node.setDirtyCanvas(true, true); 
                        }
                    }
                };

                // --- CONTAINER & IFRAME SETUP (Standard) ---
                const widget = {
                    type: "div",
                    name: "dashboard_container",
                    draw(ctx, node, widget_width, y, widget_height) {
                        const availableHeight = (node.size[1] - y) - 26;
                        if (this.iframe) {
                            const safeHeight = Math.max(100, availableHeight);
                            if (this.iframe.style.height !== safeHeight + "px") this.iframe.style.height = safeHeight + "px";
                            if (this.iframe.style.width !== (widget_width - 20) + "px") this.iframe.style.width = (widget_width - 20) + "px";
                            this.iframe.hidden = false;
                        }
                    },
                };

                const iframe = document.createElement("iframe");
                Object.assign(iframe.style, {
                    border: "none", background: "#0b0b0b", width: "100%", height: "100%",
                    display: "block", borderRadius: "0 0 4px 4px"
                });
                this.iframe = iframe;
                this.addDOMWidget("dashboard_viewer", "iframe", iframe);

                // --- API CALL (VIEW ONLY) ---
                const fetchSession = async (sessionName) => {
                    try {
                        const response = await fetch("/config_tester/get_session_html", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ session_name: sessionName, node_id: node.id })
                        });
                        if (response.ok) {
                            const html = await response.text();
                            iframe.srcdoc = html;
                        } else {
                            iframe.srcdoc = `<div style="color:#ccc; padding:20px; text-align:center;">Session '${sessionName}' not found.</div>`;
                        }
                    } catch (e) { console.error(e); }
                };

                // Use draw loop for resize logic
                this.onResize = function (size) { node.setDirtyCanvas(true, true); }
                this.setSize([900, 750]);

                return r;
            };
        }
    },
});