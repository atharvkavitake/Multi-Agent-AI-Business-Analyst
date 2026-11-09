/**
 * Multi-Agent BI Platform - Dashboard Controller
 */

let trendChart = null;
let categoryChart = null;
let regionChart = null;

async function initDashboard() {
    const datasetId = AppState.currentDatasetId;

    if (!datasetId) {
        document.getElementById("noDatasetAlert")?.classList.remove("d-none");
        document.getElementById("kpiSection")?.classList.add("opacity-50");
        return;
    }

    try {
        // Fetch deterministic profile first
        const profile = await API.getDatasetProfile(datasetId);
        renderDashboardData(profile);

        // Check if an analysis has already been executed for this dataset
        const analysisId = AppState.currentAnalysisId;
        if (analysisId) {
            try {
                const results = await API.getAnalysisResults(analysisId);
                if (results.trend_result && results.trend_result.overall_trajectory) {
                    const badge = document.getElementById("trendBadge");
                    if (badge) badge.innerText = results.trend_result.overall_trajectory;
                }
            } catch (e) {
                // Ignore if specific analysis expired
            }
        }
    } catch (error) {
        console.error("Dashboard data load error:", error);
        showToast("Unable to load dataset analytics. Please re-select dataset.", "danger");
    }
}

function renderDashboardData(profile) {
    const kpis = profile.kpis;

    // 1. Render KPI values
    const revEl = document.getElementById("kpiRevenue");
    const profEl = document.getElementById("kpiProfit");
    const marginEl = document.getElementById("kpiMargin");
    const txnsEl = document.getElementById("kpiTransactions");
    const aovEl = document.getElementById("kpiAovSub");

    if (revEl) revEl.innerText = formatCurrency(kpis.total_revenue);
    if (profEl) profEl.innerText = formatCurrency(kpis.total_profit);
    if (marginEl) marginEl.innerText = formatPct(kpis.profit_margin_pct);
    if (txnsEl) txnsEl.innerText = formatNumber(kpis.total_transactions);
    if (aovEl) aovEl.innerText = `AOV: ${formatCurrency(kpis.avg_transaction_value)}`;

    // 2. Render Category Doughnut Chart
    renderCategoryChart(profile.category_breakdown);

    // 3. Render Regional Bar Chart
    renderRegionChart(profile.region_breakdown);

    // 4. Render Outliers Table
    renderOutliersTable(profile.outliers);

    // 5. Render Trend Chart (Mock or extracted from period data)
    renderTrendChart();
}

function renderCategoryChart(categories) {
    const canvas = document.getElementById("categoryChartCanvas");
    if (!canvas || !categories || categories.length === 0) return;

    if (categoryChart) categoryChart.destroy();

    const labels = categories.map(c => c.segment);
    const data = categories.map(c => c.revenue || 0);

    const colors = [
        "#4f46e5", "#06b6d4", "#f59e0b", "#10b981", "#ec4899", "#8b5cf6"
    ];

    categoryChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: document.documentElement.getAttribute("data-theme") === "dark" ? "#172033" : "#ffffff",
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: getComputedStyle(document.body).getPropertyValue("--text-secondary").trim(),
                        font: { family: "Inter", size: 12 },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${formatCurrency(ctx.raw)}`,
                    },
                },
            },
            cutout: "68%",
        },
    });
}

function renderRegionChart(regions) {
    const canvas = document.getElementById("regionChartCanvas");
    if (!canvas || !regions || regions.length === 0) return;

    if (regionChart) regionChart.destroy();

    const labels = regions.map(r => r.segment);
    const data = regions.map(r => r.revenue || 0);

    regionChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Revenue",
                data,
                backgroundColor: "rgba(79, 70, 229, 0.8)",
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`,
                        color: getComputedStyle(document.body).getPropertyValue("--text-muted").trim(),
                    },
                    grid: { color: "rgba(148, 163, 184, 0.1)" },
                },
                x: {
                    ticks: { color: getComputedStyle(document.body).getPropertyValue("--text-muted").trim() },
                    grid: { display: false },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Revenue: ${formatCurrency(ctx.raw)}`,
                    },
                },
            },
        },
    });
}

function renderTrendChart() {
    const canvas = document.getElementById("trendChartCanvas");
    if (!canvas) return;

    if (trendChart) trendChart.destroy();

    // Default 11-month distribution from sample data
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"];
    const revenues = [5899.98, 5219.96, 6110.00, 20389.99, 4105.00, 5849.00, 3090.00, 3920.00, 9960.00, 6837.00, 4974.00];
    const profits = [1729.98, 1449.96, 1770.00, 5689.99, 1175.00, 1679.00, 980.00, 1090.00, 2890.00, 187.00, 1504.00];

    trendChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: months,
            datasets: [
                {
                    label: "Revenue",
                    data: revenues,
                    borderColor: "#4f46e5",
                    backgroundColor: "rgba(79, 70, 229, 0.1)",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                },
                {
                    label: "Profit",
                    data: profits,
                    borderColor: "#10b981",
                    backgroundColor: "transparent",
                    borderDash: [5, 5],
                    tension: 0.35,
                    borderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`,
                        color: getComputedStyle(document.body).getPropertyValue("--text-muted").trim(),
                    },
                    grid: { color: "rgba(148, 163, 184, 0.1)" },
                },
                x: {
                    ticks: { color: getComputedStyle(document.body).getPropertyValue("--text-muted").trim() },
                    grid: { display: false },
                },
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: getComputedStyle(document.body).getPropertyValue("--text-secondary").trim(),
                        font: { family: "Inter" },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`,
                    },
                },
            },
        },
    });
}

function renderOutliersTable(outliers) {
    const tbody = document.getElementById("outlierTableBody");
    const countBadge = document.getElementById("outlierCountBadge");
    if (!tbody) return;

    if (!outliers || outliers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No outliers detected in dataset.</td></tr>`;
        if (countBadge) countBadge.innerText = "0 Flagged";
        return;
    }

    if (countBadge) countBadge.innerText = `${outliers.length} Flagged`;

    tbody.innerHTML = outliers.slice(0, 5).map(o => {
        let badgeClass = "badge-warning";
        if (o.severity === "Extreme") badgeClass = "badge-danger";
        if (o.severity === "Mild") badgeClass = "badge-primary";

        return `
            <tr>
                <td class="fw-semibold">#${o.row_index}</td>
                <td><span class="badge bg-secondary-subtle text-secondary">${o.primary_metric}</span></td>
                <td class="fw-bold">${formatCurrency(o.metric_value)}</td>
                <td><small class="text-secondary">${o.detection_method}</small></td>
                <td><span class="badge-custom ${badgeClass}">${o.severity}</span></td>
            </tr>
        `;
    }).join("");
}

// Wire up "Run Analysis" button
document.addEventListener("DOMContentLoaded", () => {
    if (window.Auth && !Auth.requireAuth()) return;
    initDashboard();

    const runBtn = document.getElementById("runAnalysisBtn");
    if (runBtn) {
        runBtn.addEventListener("click", async () => {
            const datasetId = AppState.currentDatasetId;
            if (!datasetId) {
                showToast("Please upload or select a dataset first.", "warning");
                return;
            }

            try {
                runBtn.disabled = true;
                runBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Orchestrating Agents...`;
                showToast("Launching 7 Specialized AI Agents...", "info");

                const result = await API.runAnalysis(datasetId);
                AppState.setActiveAnalysis(result.analysis_id);

                showToast(`Analysis completed in ${result.total_execution_time_seconds}s!`, "success");
                window.location.href = "insights.html";
            } catch (error) {
                console.error("Run analysis failed:", error);
                showToast(`Analysis failed: ${error.message}`, "danger");
            } finally {
                runBtn.disabled = false;
                runBtn.innerHTML = `<i class="bi bi-play-circle-fill"></i> Run Analysis`;
            }
        });
    }

    // Load Sample Dataset shortcut button
    const loadSampleBtn = document.getElementById("loadSampleDatasetBtn");
    if (loadSampleBtn) {
        loadSampleBtn.addEventListener("click", async () => {
            try {
                // Fetch datasets list or redirect to upload
                window.location.href = "upload.html";
            } catch (e) {
                window.location.href = "upload.html";
            }
        });
    }

    // Re-render charts on theme toggle
    window.addEventListener("themeChanged", () => {
        if (categoryChart) categoryChart.update();
        if (regionChart) regionChart.update();
        if (trendChart) trendChart.update();
    });
});

