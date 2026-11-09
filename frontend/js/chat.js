/**
 * Multi-Agent BI Platform - Chat Controller
 */

let chatCharts = {};

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const clearBtn = document.getElementById("clearChatBtn");
    const promptPills = document.querySelectorAll(".chat-prompt-pill");

    // Click handler for prompt pills
    promptPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const query = pill.getAttribute("data-query");
            if (query) {
                if (chatInput) chatInput.value = query;
                submitQuery(query);
            }
        });
    });

    if (chatForm) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (text) {
                submitQuery(text);
                chatInput.value = "";
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            if (chatMessages) {
                chatMessages.innerHTML = `
                    <div class="chat-bubble chat-bubble-ai">
                        <div class="fw-bold mb-1 text-primary d-flex align-items-center gap-2">
                            <i class="bi bi-robot"></i> Business Query Agent
                        </div>
                        <p class="mb-0">Chat history cleared. How can I assist you with your dataset?</p>
                    </div>
                `;
            }
        });
    }

    async function submitQuery(queryText) {
        const analysisId = AppState.currentAnalysisId;
        const datasetId = AppState.currentDatasetId;

        if (!datasetId) {
            showToast("Please upload a dataset first.", "warning");
            return;
        }

        // Append User Bubble
        appendUserMessage(queryText);

        // Append Loading AI Bubble
        const loadingId = "loadingBubble_" + Date.now();
        appendLoadingMessage(loadingId);

        try {
            let activeAnalysisId = analysisId;
            if (!activeAnalysisId) {
                // Run analysis automatically if not yet executed
                const analysisResult = await API.runAnalysis(datasetId);
                activeAnalysisId = analysisResult.analysis_id;
                AppState.setActiveAnalysis(activeAnalysisId);
            }

            // Post query to backend
            const response = await API.request(`/api/analysis/${activeAnalysisId}/chat`, {
                method: "POST",
                body: JSON.stringify({ question: queryText }),
            });

            // Remove loading bubble and append structured AI answer
            removeLoadingMessage(loadingId);
            appendAIMessage(response);
        } catch (error) {
            console.error("Chat error:", error);
            removeLoadingMessage(loadingId);
            appendErrorMessage(error.message);
        }
    }

    function appendUserMessage(text) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble chat-bubble-user";
        bubble.innerText = text;
        chatMessages.appendChild(bubble);
        scrollToBottom();
    }

    function appendLoadingMessage(id) {
        const bubble = document.createElement("div");
        bubble.id = id;
        bubble.className = "chat-bubble chat-bubble-ai";
        bubble.innerHTML = `
            <div class="d-flex align-items-center gap-2 text-secondary">
                <span class="spinner-border spinner-border-sm text-primary"></span>
                <span>Synthesizing safe analytical query plan...</span>
            </div>
        `;
        chatMessages.appendChild(bubble);
        scrollToBottom();
    }

    function removeLoadingMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function appendErrorMessage(errorMsg) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble chat-bubble-ai border-danger";
        bubble.innerHTML = `
            <div class="text-danger fw-bold mb-1"><i class="bi bi-exclamation-triangle-fill"></i> Error</div>
            <p class="mb-0 text-secondary small">${errorMsg}</p>
        `;
        chatMessages.appendChild(bubble);
        scrollToBottom();
    }

    function appendAIMessage(data) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble chat-bubble-ai";

        let html = `
            <div class="fw-bold mb-1 text-primary d-flex align-items-center justify-content-between">
                <span><i class="bi bi-robot"></i> Business Query Agent</span>
                <span class="badge bg-secondary-subtle text-secondary small fw-normal">${data.query_plan ? data.query_plan.intent : 'Result'}</span>
            </div>
            <div class="mb-3">${formatMarkdown(data.answer_text)}</div>
        `;

        // Render Evidence Table if present
        if (data.evidence_table && data.evidence_table.length > 0) {
            const cols = Object.keys(data.evidence_table[0]);
            html += `
                <div class="table-responsive my-2 rounded border">
                    <table class="table-custom mb-0">
                        <thead>
                            <tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>
                        </thead>
                        <tbody>
                            ${data.evidence_table.map(row => `
                                <tr>${cols.map(c => `<td>${row[c] !== null && row[c] !== undefined ? row[c] : '—'}</td>`).join("")}</tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Render Inline Chart Canvas if chart config is present
        let chartCanvasId = null;
        if (data.chart_config && data.chart_config.labels && data.chart_config.labels.length > 0) {
            chartCanvasId = "chatChart_" + Date.now();
            html += `
                <div class="my-3 p-2 bg-base rounded border" style="height: 240px;">
                    <canvas id="${chartCanvasId}"></canvas>
                </div>
            `;
        }

        bubble.innerHTML = html;
        chatMessages.appendChild(bubble);
        scrollToBottom();

        // Initialize Chart.js if canvas exists
        if (chartCanvasId && data.chart_config) {
            const canvas = document.getElementById(chartCanvasId);
            if (canvas) {
                const cfg = data.chart_config;
                new Chart(canvas, {
                    type: cfg.type || "bar",
                    data: {
                        labels: cfg.labels,
                        datasets: cfg.datasets.map(d => ({
                            ...d,
                            backgroundColor: "rgba(79, 70, 229, 0.75)",
                            borderRadius: 6,
                        })),
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            title: { display: !!cfg.title, text: cfg.title },
                        },
                    },
                });
            }
        }
    }

    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function formatMarkdown(text) {
        if (!text) return "";
        // Replace bold **text** with <strong>text</strong>
        return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    }
});
