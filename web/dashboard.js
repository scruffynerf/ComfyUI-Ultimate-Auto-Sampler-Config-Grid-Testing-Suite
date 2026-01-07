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

                // --- ADD LOAD BUTTON ---
                this.addWidget("button", "RELOAD / SHOW SESSION", null, () => {
                    const sessionWidget = node.widgets.find(w => w.name === "session_name");
                    if (sessionWidget) {
                        fetchSession(sessionWidget.value);
                    }
                });

                // --- CONTAINER ---
                const widget = {
                    type: "div",
                    name: "dashboard_container",
                    draw(ctx, node, widget_width, y, widget_height) {
                        // FIX: We need a larger safety buffer (26px) to account for the footer/border radius
                        // The 'y' value automatically adjusts if buttons above it move, 
                        // so we just need to subtract 'y' from the total node height.
                        const availableHeight = (node.size[1] - y) - 26;
                        
                        if (this.iframe) {
                            // Clamp height to minimum 100 to prevent errors when minimized
                            const safeHeight = Math.max(100, availableHeight);
                            
                            // Only update DOM if dimensions actually changed (performance)
                            if (this.iframe.style.height !== safeHeight + "px") {
                                this.iframe.style.height = safeHeight + "px";
                            }
                            if (this.iframe.style.width !== (widget_width - 20) + "px") {
                                this.iframe.style.width = (widget_width - 20) + "px";
                            }
                            
                            this.iframe.hidden = false;
                        }
                    },
                };

                // --- IFRAME ---
                const iframe = document.createElement("iframe");
                Object.assign(iframe.style, {
                    border: "none",
                    background: "#0b0b0b",
                    width: "100%",
                    height: "100%",
                    pointerEvents: "auto",
                    display: "block",
                    borderRadius: "0 0 4px 4px" // Rounded bottom corners only
                });

                this.iframe = iframe;
                this.addDOMWidget("dashboard_viewer", "iframe", iframe);

                // --- API CALL ---
                const fetchSession = async (sessionName) => {
                    try {
                        const response = await fetch("/config_tester/get_session_html", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ 
                                session_name: sessionName,
                                node_id: node.id 
                            })
                        });
                        if (response.ok) {
                            const html = await response.text();
                            iframe.srcdoc = html;
                        } else {
                            iframe.srcdoc = `<div style="color:#ccc; font-family:sans-serif; padding:20px; text-align:center;">
                                <h3>Session '${sessionName}' not found.</h3>
                                <p style="font-size:12px; color:#888">Check your Output/benchmarks folder.</p>
                            </div>`;
                        }
                    } catch (e) {
                        console.error(e);
                        iframe.srcdoc = `<div style="color:red; padding:20px;">Connection Error: ${e}</div>`;
                    }
                };

                this.onExecuted = function (message) {
                    if (message?.html) {
                        iframe.srcdoc = message.html[0];
                    }
                };
                
                // We rely on the draw() loop to handle resizing now, 
                // so onResize just needs to trigger a redraw.
                this.onResize = function (size) {
                   node.setDirtyCanvas(true, true);
                }

                // Default Size
                this.setSize([900, 750]);

                return r;
            };
        }
    },
});