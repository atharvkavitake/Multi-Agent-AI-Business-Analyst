/**
 * Multi-Agent BI Platform - Global Application State & Utilities
 */

const AppState = {
    currentDatasetId: localStorage.getItem("bi_active_dataset_id") || null,
    currentDatasetName: localStorage.getItem("bi_active_dataset_name") || null,
    currentAnalysisId: localStorage.getItem("bi_active_analysis_id") || null,

    setActiveDataset(id, name) {
        this.currentDatasetId = id;
        this.currentDatasetName = name;
        if (id) {
            localStorage.setItem("bi_active_dataset_id", id);
            localStorage.setItem("bi_active_dataset_name", name || "Dataset");
        } else {
            localStorage.removeItem("bi_active_dataset_id");
            localStorage.removeItem("bi_active_dataset_name");
        }
        this.updateSidebarActiveDataset();
    },

    setActiveAnalysis(analysisId) {
        this.currentAnalysisId = analysisId;
        if (analysisId) {
            localStorage.setItem("bi_active_analysis_id", analysisId);
        } else {
            localStorage.removeItem("bi_active_analysis_id");
        }
    },

    updateSidebarActiveDataset() {
        const pill = document.getElementById("activeDatasetIndicator");
        if (pill) {
            if (this.currentDatasetId && this.currentDatasetName) {
                pill.innerHTML = `<i class="bi bi-file-earmark-check-fill text-success"></i> <span>${this.currentDatasetName}</span>`;
                pill.title = `Active: ${this.currentDatasetName} (${this.currentDatasetId})`;
            } else {
                pill.innerHTML = `<i class="bi bi-circle text-muted"></i> <span>No dataset loaded</span>`;
                pill.title = "No active dataset loaded";
            }
        }
    },
};

// Theme Management (Light / Dark)
function initTheme() {
    const savedTheme = localStorage.getItem("bi_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);

    const toggleBtn = document.getElementById("themeToggleBtn");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-theme") || "light";
            const next = current === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", next);
            localStorage.setItem("bi_theme", next);
            updateThemeIcon(next);
            // Trigger Plotly / Chart.js re-theme if available
            window.dispatchEvent(new Event("themeChanged"));
        });
    }
}

function updateThemeIcon(theme) {
    const toggleBtn = document.getElementById("themeToggleBtn");
    if (toggleBtn) {
        toggleBtn.innerHTML = theme === "dark" 
            ? '<i class="bi bi-sun-fill text-warning"></i>' 
            : '<i class="bi bi-moon-stars-fill"></i>';
    }
}

// Toast Notifications
function showToast(message, type = "info") {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container-custom";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast-custom border-${type}`;

    let icon = "bi-info-circle-fill text-info";
    if (type === "success") icon = "bi-check-circle-fill text-success";
    if (type === "warning") icon = "bi-exclamation-triangle-fill text-warning";
    if (type === "danger") icon = "bi-x-circle-fill text-danger";

    toast.innerHTML = `
        <i class="bi ${icon} fs-5 flex-shrink-0"></i>
        <div class="flex-grow-1 small">${message}</div>
        <button type="button" class="btn-close btn-close-sm flex-shrink-0" style="font-size: 0.7rem;" aria-label="Close"></button>
    `;

    toast.querySelector(".btn-close").addEventListener("click", () => toast.remove());
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Formatting Helpers
function formatCurrency(val) {
    if (val === null || val === undefined) return "N/A";
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);
}

function formatNumber(val) {
    if (val === null || val === undefined) return "N/A";
    return new Intl.NumberFormat("en-US").format(val);
}

function formatPct(val) {
    if (val === null || val === undefined) return "N/A";
    return `${Number(val).toFixed(2)}%`;
}

// Mobile sidebar toggle with backdrop overlay
function initMobileSidebar() {
    const toggle = document.querySelector(".mobile-menu-toggle");
    const sidebar = document.querySelector(".app-sidebar");
    let backdrop = document.getElementById("sidebarBackdrop");
    
    if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.id = "sidebarBackdrop";
        backdrop.className = "sidebar-backdrop";
        document.body.appendChild(backdrop);
    }

    if (toggle && sidebar) {
        toggle.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = sidebar.classList.toggle("show");
            backdrop.classList.toggle("show", isOpen);
        });

        backdrop.addEventListener("click", () => {
            sidebar.classList.remove("show");
            backdrop.classList.remove("show");
        });

        // Close on ESC key
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && sidebar.classList.contains("show")) {
                sidebar.classList.remove("show");
                backdrop.classList.remove("show");
            }
        });
    }
}

// On DOM Loaded
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    AppState.updateSidebarActiveDataset();
    initMobileSidebar();
});
