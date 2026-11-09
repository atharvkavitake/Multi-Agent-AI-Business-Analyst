/**
 * Multi-Agent BI Platform - Personalized Analysis History Controller
 */

let historyState = {
    page: 1,
    pageSize: 10,
    search: "",
    status: "all",
    sort: "newest",
    dateFrom: "",
    dateTo: "",
    totalPages: 1,
    totalCount: 0,
};

document.addEventListener("DOMContentLoaded", () => {
    // Enforce authentication guard
    if (!Auth.requireAuth()) {
        return;
    }

    // Attach filter listeners
    const applyBtn = document.getElementById("applyFiltersBtn");
    const resetBtn = document.getElementById("resetFiltersBtn");
    const searchInput = document.getElementById("historySearchInput");
    const statusSelect = document.getElementById("historyStatusFilter");
    const sortSelect = document.getElementById("historySortSelect");
    const dateFromInput = document.getElementById("historyDateFrom");
    const dateToInput = document.getElementById("historyDateTo");

    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");

    if (applyBtn) {
        applyBtn.addEventListener("click", () => {
            historyState.page = 1;
            readFiltersFromUI();
            loadHistory();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                historyState.page = 1;
                readFiltersFromUI();
                loadHistory();
            }
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            if (statusSelect) statusSelect.value = "all";
            if (sortSelect) sortSelect.value = "newest";
            if (dateFromInput) dateFromInput.value = "";
            if (dateToInput) dateToInput.value = "";

            historyState.page = 1;
            readFiltersFromUI();
            loadHistory();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (historyState.page > 1) {
                historyState.page--;
                loadHistory();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (historyState.page < historyState.totalPages) {
                historyState.page++;
                loadHistory();
            }
        });
    }

    // Initial load
    loadHistory();
});

function readFiltersFromUI() {
    const searchInput = document.getElementById("historySearchInput");
    const statusSelect = document.getElementById("historyStatusFilter");
    const sortSelect = document.getElementById("historySortSelect");
    const dateFromInput = document.getElementById("historyDateFrom");
    const dateToInput = document.getElementById("historyDateTo");

    historyState.search = searchInput ? searchInput.value.trim() : "";
    historyState.status = statusSelect ? statusSelect.value : "all";
    historyState.sort = sortSelect ? sortSelect.value : "newest";
    historyState.dateFrom = dateFromInput ? dateFromInput.value : "";
    historyState.dateTo = dateToInput ? dateToInput.value : "";
}

async function loadHistory() {
    const tbody = document.getElementById("historyTableBody");
    const countBadge = document.getElementById("historyCount");
    const emptyState = document.getElementById("historyEmptyState");
    const tableContainer = tbody ? tbody.closest(".table-responsive") : null;
    const paginationSummary = document.getElementById("paginationSummary");
    const pageIndicator = document.getElementById("pageIndicator");
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");

    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center text-muted py-5">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                Loading personal analysis history...
            </td>
        </tr>
    `;

    try {
        const response = await API.listAnalysisHistory({
            search: historyState.search,
            status: historyState.status,
            sort: historyState.sort,
            date_from: historyState.dateFrom,
            date_to: historyState.dateTo,
            page: historyState.page,
            page_size: historyState.pageSize,
        });

        // Handle both paginated response object and raw arrays gracefully
        let items = [];
        let totalCount = 0;
        let totalPages = 1;
        let currentPage = 1;

        if (response && Array.isArray(response.items)) {
            items = response.items;
            totalCount = response.total_count ?? items.length;
            totalPages = response.total_pages ?? 1;
            currentPage = response.page ?? 1;
        } else if (Array.isArray(response)) {
            items = response;
            totalCount = items.length;
            totalPages = 1;
            currentPage = 1;
        }

        historyState.totalCount = totalCount;
        historyState.totalPages = Math.max(1, totalPages);
        historyState.page = currentPage;

        if (countBadge) countBadge.innerText = `${totalCount} ${totalCount === 1 ? 'Session' : 'Sessions'}`;

        if (items.length === 0) {
            tbody.innerHTML = "";
            if (tableContainer) tableContainer.classList.add("d-none");
            if (emptyState) emptyState.classList.remove("d-none");
            if (paginationSummary) paginationSummary.innerText = "Showing 0 of 0 sessions";
            if (pageIndicator) pageIndicator.innerText = `Page 1 of 1`;
            if (prevBtn) prevBtn.disabled = true;
            if (nextBtn) nextBtn.disabled = true;
            return;
        }

        if (tableContainer) tableContainer.classList.remove("d-none");
        if (emptyState) emptyState.classList.add("d-none");

        // Render table rows
        tbody.innerHTML = items.map(item => {
            let statusBadge = "badge-success";
            let statusLabel = "Completed";
            if (item.status === "degraded") {
                statusBadge = "badge-warning";
                statusLabel = "Degraded";
            } else if (item.status === "running") {
                statusBadge = "badge-primary";
                statusLabel = "Running";
            } else if (item.status === "failed") {
                statusBadge = "badge-danger";
                statusLabel = "Failed";
            }

            const formattedDate = formatDate(item.created_at);
            const shapeStr = (item.row_count || item.column_count)
                ? `${(item.row_count || 0).toLocaleString()} × ${item.column_count || 0}`
                : "Dynamic";

            const rev = item.total_revenue != null ? formatCurrency(item.total_revenue) : "--";
            const prof = item.total_profit != null ? formatCurrency(item.total_profit) : "--";
            const margin = item.profit_margin_pct != null ? `${item.profit_margin_pct.toFixed(1)}%` : "--";

            return `
                <tr>
                    <td>
                        <div class="fw-bold text-truncate" style="max-width: 220px;" title="${escapeHtml(item.dataset_name)}">
                            ${escapeHtml(item.dataset_name)}
                        </div>
                        <div class="small text-muted font-monospace text-truncate" style="max-width: 200px;">
                            ${item.analysis_id.substring(0, 8)}...
                        </div>
                    </td>
                    <td>
                        <div class="small fw-semibold">${formattedDate.date}</div>
                        <div class="small text-muted">${formattedDate.time}</div>
                    </td>
                    <td>
                        <span class="badge bg-light text-secondary border">
                            <i class="bi bi-grid-3x3 me-1"></i> ${shapeStr}
                        </span>
                    </td>
                    <td><span class="badge-custom ${statusBadge}">${statusLabel}</span></td>
                    <td class="fw-semibold">${rev}</td>
                    <td class="text-success fw-semibold">${prof}</td>
                    <td>${margin}</td>
                    <td>
                        <div class="d-flex align-items-center gap-1">
                            <button class="btn btn-sm btn-primary-custom py-1 px-2" title="Inspect Dashboard" onclick="inspectAnalysis('${item.analysis_id}', '${item.dataset_id || ''}', '${escapeHtml(item.dataset_name)}')">
                                <i class="bi bi-speedometer2"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-custom py-1 px-2" title="View AI Insights" onclick="inspectInsights('${item.analysis_id}', '${item.dataset_id || ''}', '${escapeHtml(item.dataset_name)}')">
                                <i class="bi bi-stars text-primary"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-custom py-1 px-2" title="Download PDF Report" onclick="downloadReport('${item.analysis_id}')">
                                <i class="bi bi-file-earmark-pdf text-danger"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger py-1 px-2" title="Delete Session" onclick="deleteHistorySession('${item.analysis_id}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        // Update pagination controls
        const startIdx = (historyState.page - 1) * historyState.pageSize + 1;
        const endIdx = Math.min(startIdx + items.length - 1, totalCount);
        if (paginationSummary) {
            paginationSummary.innerText = `Showing ${startIdx} to ${endIdx} of ${totalCount} sessions`;
        }
        if (pageIndicator) {
            pageIndicator.innerText = `Page ${historyState.page} of ${historyState.totalPages}`;
        }
        if (prevBtn) prevBtn.disabled = (historyState.page <= 1);
        if (nextBtn) nextBtn.disabled = (historyState.page >= historyState.totalPages);

    } catch (error) {
        console.error("Load history error:", error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger py-4">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i> Failed to load history: ${error.message}
                </td>
            </tr>
        `;
    }
}

// Global action handlers
window.inspectAnalysis = function(analysisId, datasetId, datasetName) {
    if (window.AppState) {
        AppState.setActiveAnalysis(analysisId);
        if (datasetId) {
            AppState.setActiveDataset(datasetId, datasetName);
        }
    } else {
        localStorage.setItem("bi_active_analysis_id", analysisId);
        if (datasetId) {
            localStorage.setItem("bi_active_dataset_id", datasetId);
            localStorage.setItem("bi_active_dataset_name", datasetName);
        }
    }
    window.location.href = "dashboard.html";
};

window.inspectInsights = function(analysisId, datasetId, datasetName) {
    if (window.AppState) {
        AppState.setActiveAnalysis(analysisId);
        if (datasetId) {
            AppState.setActiveDataset(datasetId, datasetName);
        }
    } else {
        localStorage.setItem("bi_active_analysis_id", analysisId);
        if (datasetId) {
            localStorage.setItem("bi_active_dataset_id", datasetId);
            localStorage.setItem("bi_active_dataset_name", datasetName);
        }
    }
    window.location.href = "insights.html";
};

window.downloadReport = async function(analysisId) {
    try {
        if (window.showToast) showToast("Generating & downloading PDF report...", "info");
        await API.downloadReportPdf(analysisId);
    } catch (err) {
        if (window.showToast) {
            showToast("Failed to download report: " + err.message, "danger");
        } else {
            alert("Failed to download report: " + err.message);
        }
    }
};

window.deleteHistorySession = async function(analysisId) {
    if (!confirm("Are you sure you want to permanently delete this analysis session?")) return;

    try {
        await API.deleteAnalysis(analysisId);
        if (window.showToast) showToast("Analysis session deleted successfully.", "success");
        loadHistory();
    } catch (error) {
        if (window.showToast) {
            showToast("Failed to delete session: " + error.message, "danger");
        } else {
            alert("Failed to delete session: " + error.message);
        }
    }
};

function formatDate(isoStr) {
    if (!isoStr) return { date: "--", time: "" };
    try {
        const d = new Date(isoStr);
        return {
            date: d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }),
            time: d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }),
        };
    } catch {
        return { date: isoStr, time: "" };
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
