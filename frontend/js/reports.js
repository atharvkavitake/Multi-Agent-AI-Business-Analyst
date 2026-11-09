/**
 * Multi-Agent BI Platform - Reports Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
    const analysisId = AppState.currentAnalysisId;
    const downloadBtn = document.getElementById("downloadPdfBtn");

    if (!analysisId) {
        showToast("No active analysis found. Please run an analysis first.", "warning");
        return;
    }

    try {
        const state = await API.getAnalysisResults(analysisId);
        renderReportPreview(state);
    } catch (error) {
        console.error("Failed to load report data:", error);
        showToast("Error loading report: " + error.message, "danger");
    }

    if (downloadBtn) {
        downloadBtn.addEventListener("click", () => {
            if (!analysisId) {
                showToast("No active analysis to download.", "warning");
                return;
            }
            // Trigger PDF download from backend endpoint
            const downloadUrl = API.getEndpoint(`/api/analysis/${analysisId}/report`);
            window.open(downloadUrl, "_blank");
        });
    }
});

function renderReportPreview(state) {
    const rep = state.report_result;
    const kpis = state.deterministic_payload.kpis;

    if (rep) {
        document.getElementById("repTitle").innerText = rep.report_title;
        document.getElementById("repDate").innerText = rep.generated_at;
        document.getElementById("repBrief").innerText = rep.executive_brief;

        const takeawaysList = document.getElementById("repTakeawaysList");
        if (takeawaysList && rep.strategic_takeaways) {
            takeawaysList.innerHTML = rep.strategic_takeaways.map(t => `
                <li class="p-2 border rounded bg-base small d-flex align-items-center gap-2">
                    <i class="bi bi-arrow-right-circle text-primary"></i> ${t}
                </li>
            `).join("");
        }
    }

    // KPIs
    document.getElementById("repRev").innerText = formatCurrency(kpis.total_revenue);
    document.getElementById("repProf").innerText = formatCurrency(kpis.total_profit);
    document.getElementById("repMargin").innerText = formatPct(kpis.profit_margin_pct);

    // Strategy Recommendations
    const recsContainer = document.getElementById("repRecommendations");
    if (recsContainer && state.strategy_result && state.strategy_result.recommendations) {
        recsContainer.innerHTML = state.strategy_result.recommendations.map(r => `
            <div class="p-3 mb-3 border rounded bg-base">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="text-primary">${r.id}: ${r.title}</strong>
                    <span class="badge bg-secondary-subtle text-secondary small">${r.priority}</span>
                </div>
                <p class="small text-secondary mb-1"><strong>Evidence:</strong> ${r.supporting_evidence}</p>
                <p class="small text-dark mb-0"><strong>Recommended Action:</strong> ${r.suggested_action}</p>
            </div>
        `).join("");
    }
}
