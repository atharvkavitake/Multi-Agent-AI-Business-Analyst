/**
 * Multi-Agent BI Platform - Insights Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
    initTabs();

    let analysisId = AppState.currentAnalysisId;
    const datasetId = AppState.currentDatasetId;

    if (!analysisId && datasetId) {
        // If analysis hasn't been run yet, trigger it automatically
        try {
            showToast("Running multi-agent analysis on active dataset...", "info");
            const result = await API.runAnalysis(datasetId);
            analysisId = result.analysis_id;
            AppState.setActiveAnalysis(analysisId);
        } catch (e) {
            console.error("Auto-analysis error:", e);
            showToast("Unable to run analysis: " + e.message, "danger");
            return;
        }
    }

    if (!analysisId) {
        showToast("No active analysis found. Please upload a dataset first.", "warning");
        return;
    }

    try {
        const state = await API.getAnalysisResults(analysisId);
        renderAllInsights(state);
    } catch (error) {
        console.error("Failed to load analysis state:", error);
        showToast("Failed to retrieve agent insights: " + error.message, "danger");
    }
});

function initTabs() {
    const tabs = document.querySelectorAll(".tab-btn-custom");
    tabs.forEach(btn => {
        btn.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            btn.classList.add("active");

            const targetId = btn.getAttribute("data-tab");
            document.querySelectorAll(".tab-content-panel").forEach(panel => {
                panel.classList.add("d-none");
            });

            const activePanel = document.getElementById(targetId);
            if (activePanel) activePanel.classList.remove("d-none");
        });
    });
}

function renderAllInsights(state) {
    // 1. Overview Tab
    if (state.report_result) {
        document.getElementById("overviewTitle").innerText = state.report_result.report_title;
        document.getElementById("overviewTimestamp").innerText = state.report_result.generated_at;
        document.getElementById("overviewBrief").innerText = state.report_result.executive_brief;
    }

    if (state.strategy_result) {
        const oppsList = document.getElementById("overviewOpportunitiesList");
        if (oppsList && state.strategy_result.business_opportunities) {
            oppsList.innerHTML = state.strategy_result.business_opportunities.map(opp => `
                <li class="d-flex align-items-start gap-2">
                    <i class="bi bi-arrow-right-short text-success fs-5"></i>
                    <span>${opp}</span>
                </li>
            `).join("");
        }

        const risksList = document.getElementById("overviewRisksList");
        if (risksList && state.strategy_result.business_risks) {
            risksList.innerHTML = state.strategy_result.business_risks.map(r => `
                <li class="d-flex align-items-start gap-2">
                    <i class="bi bi-arrow-right-short text-danger fs-5"></i>
                    <span>${r}</span>
                </li>
            `).join("");
        }

        // 2. Strategy Tab (Agent 5)
        document.getElementById("strategyFocusSummary").innerText = state.strategy_result.strategic_focus_summary;
        const stratContainer = document.getElementById("strategyCardsContainer");
        if (stratContainer && state.strategy_result.recommendations) {
            stratContainer.innerHTML = state.strategy_result.recommendations.map(r => {
                let pClass = "priority-p2";
                if (r.priority.includes("P1")) pClass = "priority-p1";
                if (r.priority.includes("P3")) pClass = "priority-p3";

                return `
                    <div class="strategy-card ${pClass}">
                        <div class="strategy-header">
                            <div>
                                <span class="badge bg-secondary-subtle text-secondary small me-2">${r.id}</span>
                                <span class="strategy-title">${r.title}</span>
                            </div>
                            <div class="d-flex gap-2">
                                <span class="badge-custom badge-primary">${r.priority}</span>
                                <span class="badge bg-light text-dark border">${r.category}</span>
                            </div>
                        </div>
                        <div class="strategy-evidence">
                            <strong><i class="bi bi-clipboard-data"></i> Supporting Evidence:</strong> ${r.supporting_evidence}
                        </div>
                        <div class="strategy-action mt-2">
                            <strong><i class="bi bi-play-circle text-primary"></i> Actionable Next Step:</strong> ${r.suggested_action}
                        </div>
                        <div class="d-flex gap-3 text-muted small mt-3">
                            <span>Business Impact: <strong>${r.business_impact}</strong></span>
                            <span>Feasibility: <strong>${r.feasibility}</strong></span>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    // 3. Business Analyst Tab (Agent 2)
    if (state.analyst_result) {
        document.getElementById("analystKpiSummary").innerText = state.analyst_result.executive_kpi_summary;

        const revList = document.getElementById("analystRevDrivers");
        if (revList && state.analyst_result.top_revenue_drivers) {
            revList.innerHTML = state.analyst_result.top_revenue_drivers.map(d => `
                <li class="p-2 border rounded bg-base small"><i class="bi bi-check-circle text-success me-2"></i>${d}</li>
            `).join("");
        }

        const profList = document.getElementById("analystProfDrivers");
        if (profList && state.analyst_result.profitability_drivers) {
            profList.innerHTML = state.analyst_result.profitability_drivers.map(d => `
                <li class="p-2 border rounded bg-base small"><i class="bi bi-graph-up text-primary me-2"></i>${d}</li>
            `).join("");
        }
    }

    // 4. Trend Tab (Agent 3)
    if (state.trend_result) {
        document.getElementById("trendCoverageText").innerText = state.trend_result.temporal_coverage;
        document.getElementById("trendTrajectoryText").innerText = state.trend_result.overall_trajectory;

        const growthList = document.getElementById("trendGrowthList");
        if (growthList && state.trend_result.growth_periods) {
            growthList.innerHTML = state.trend_result.growth_periods.map(g => `
                <li class="p-2 border rounded bg-base small"><i class="bi bi-arrow-up-right text-success me-2"></i>${g}</li>
            `).join("");
        }

        const declineList = document.getElementById("trendDeclineList");
        if (declineList && state.trend_result.decline_periods) {
            declineList.innerHTML = state.trend_result.decline_periods.length > 0 
                ? state.trend_result.decline_periods.map(d => `<li class="p-2 border rounded bg-base small"><i class="bi bi-arrow-down-right text-danger me-2"></i>${d}</li>`).join("")
                : `<li class="text-muted small">No significant contraction periods identified.</li>`;
        }
    }

    // 5. Anomalies Tab (Agent 4)
    if (state.anomaly_result) {
        document.getElementById("anomalyRiskSummary").innerText = state.anomaly_result.systemic_risk_summary;

        const anomContainer = document.getElementById("anomalyCardsContainer");
        if (anomContainer && state.anomaly_result.high_impact_anomalies) {
            anomContainer.innerHTML = state.anomaly_result.high_impact_anomalies.map(a => `
                <div class="card-custom p-3 mb-3 border-start border-4 ${a.severity === 'Extreme' ? 'border-danger' : 'border-warning'}">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-bold">Row #${a.row_index} | ${a.metric} = ${formatCurrency(a.value)}</span>
                        <span class="badge-custom ${a.severity === 'Extreme' ? 'badge-danger' : 'badge-warning'}">${a.severity}</span>
                    </div>
                    <p class="small text-secondary mb-1"><strong>Explanation:</strong> ${a.explanation}</p>
                    <p class="small text-muted mb-0"><strong>Business Context:</strong> ${a.business_context}</p>
                </div>
            `).join("");
        }
    }

    // 6. Profiling Tab (Agent 1)
    if (state.profiling_result) {
        document.getElementById("profilingDomain").innerText = state.profiling_result.inferred_domain;
        document.getElementById("profilingQuality").innerText = state.profiling_result.data_quality_assessment;

        const metricsList = document.getElementById("profilingMetricsList");
        if (metricsList && state.profiling_result.potential_business_metrics) {
            metricsList.innerHTML = state.profiling_result.potential_business_metrics.map(m => `
                <li><i class="bi bi-dot fs-5 text-primary"></i> ${m}</li>
            `).join("");
        }
    }
}

