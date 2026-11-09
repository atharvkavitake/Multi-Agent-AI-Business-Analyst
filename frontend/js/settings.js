/**
 * Multi-Agent BI Platform - Settings Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const apiUrlInput = document.getElementById("apiUrlInput");
    const saveBtn = document.getElementById("saveApiUrlBtn");

    if (apiUrlInput) {
        apiUrlInput.value = localStorage.getItem("bi_api_url") || "";
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", () => {
            const url = apiUrlInput.value.trim();
            if (url) {
                localStorage.setItem("bi_api_url", url);
                API.BASE_URL = url;
                showToast("API Endpoint URL saved: " + url, "success");
            } else {
                localStorage.removeItem("bi_api_url");
                API.BASE_URL = (window.location.port === "8000" ? "" : "http://127.0.0.1:8000");
                showToast("Reset to default API origin.", "info");
            }
            checkSystemHealth();
        });
    }

    checkSystemHealth();
});

async function checkSystemHealth() {
    const apiBadge = document.getElementById("healthApiBadge");
    const dbBadge = document.getElementById("healthDbBadge");
    const aiBadge = document.getElementById("healthAiBadge");

    try {
        const data = await API.checkHealth();
        if (apiBadge) {
            apiBadge.className = "badge-custom badge-success";
            apiBadge.innerText = "Online (v" + data.version + ")";
        }
        if (dbBadge) {
            const dbStatus = data.components?.database === "online";
            dbBadge.className = `badge-custom ${dbStatus ? 'badge-success' : 'badge-danger'}`;
            dbBadge.innerText = dbStatus ? "Online" : "Offline";
        }
        if (aiBadge) {
            const aiMode = data.components?.ai_service || "Active";
            aiBadge.className = "badge-custom badge-primary";
            aiBadge.innerText = aiMode === "configured" ? "Cloud LLM + Fallbacks" : "Deterministic Fallback";
        }
    } catch (error) {
        if (apiBadge) {
            apiBadge.className = "badge-custom badge-danger";
            apiBadge.innerText = "Unreachable";
        }
        if (dbBadge) {
            dbBadge.className = "badge-custom badge-warning";
            dbBadge.innerText = "Unknown";
        }
        if (aiBadge) {
            aiBadge.className = "badge-custom badge-warning";
            aiBadge.innerText = "Unknown";
        }
    }
}

