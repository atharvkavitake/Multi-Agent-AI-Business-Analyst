/**
 * Multi-Agent BI Platform - History Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();

    const refreshBtn = document.getElementById("refreshHistoryBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            loadHistory();
            showToast("History refreshed.", "info");
        });
    }
});

async function loadHistory() {
    const tbody = document.getElementById("historyTableBody");
    const countBadge = document.getElementById("historyCount");
    if (!tbody) return;

    try {
        const history = await API.listAnalysisHistory();

        if (countBadge) countBadge.innerText = `${history.length} Sessions`;

        if (!history || history.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        No previous analysis sessions recorded. Upload a dataset and click "Run Analysis"!
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = history.map(item => {
            let statusBadge = "badge-success";
            if (item.status === "degraded") statusBadge = "badge-warning";
            if (item.status === "running") statusBadge = "badge-primary";
            if (item.status === "failed") statusBadge = "badge-danger";

            return `
                <tr>
                    <td class="fw-bold">${item.dataset_name}</td>
                    <td><code class="small text-secondary">${item.analysis_id.substring(0, 8)}...</code></td>
                    <td><span class="badge-custom ${statusBadge}">${item.status}</span></td>
                    <td class="fw-semibold">${formatCurrency(item.total_revenue)}</td>
                    <td class="text-success fw-semibold">${formatCurrency(item.total_profit)}</td>
                    <td>${formatPct(item.profit_margin_pct)}</td>
                    <td><small class="text-secondary">${item.total_execution_time_seconds}s</small></td>
                    <td>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-primary-custom py-1 px-2" onclick="inspectAnalysis('${item.analysis_id}', '${item.dataset_id}', '${item.dataset_name}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-danger py-1 px-2" onclick="deleteHistorySession('${item.analysis_id}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (error) {
        console.error("Load history error:", error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger py-4">
                    Failed to load history: ${error.message}
                </td>
            </tr>
        `;
    }
}

window.inspectAnalysis = function(analysisId, datasetId, datasetName) {
    AppState.setActiveAnalysis(analysisId);
    if (datasetId) {
        AppState.setActiveDataset(datasetId, datasetName);
    }
    window.location.href = "insights.html";
};

window.deleteHistorySession = async function(analysisId) {
    if (!confirm("Are you sure you want to delete this analysis session?")) return;

    try {
        await API.deleteAnalysis(analysisId);
        showToast("Analysis session deleted.", "success");
        loadHistory();
    } catch (error) {
        showToast("Failed to delete session: " + error.message, "danger");
    }
};
