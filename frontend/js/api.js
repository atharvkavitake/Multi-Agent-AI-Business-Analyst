/**
 * Multi-Agent BI Platform - REST API Client
 * Central communication layer connecting frontend UI with FastAPI backend.
 */

const API = {
    // Automatically use backend URL or fall back to localhost:8000 for local file:// previews
    BASE_URL: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? (window.location.port === "8000" ? "" : "http://127.0.0.1:8000")
        : (localStorage.getItem("bi_api_url") || ""),

    getEndpoint(path) {
        return `${this.BASE_URL}${path}`;
    },

    async request(path, options = {}) {
        const url = this.getEndpoint(path);
        const headers = options.headers || {};

        if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                let errorMsg = `Server error ${response.status}`;
                try {
                    const errorJson = await response.json();
                    errorMsg = errorJson.detail || errorJson.message || errorMsg;
                } catch (e) {
                    // Fallback to text
                }
                throw new Error(errorMsg);
            }

            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${path}:`, error);
            throw error;
        }
    },

    // Health
    async checkHealth() {
        return this.request("/health");
    },

    // Datasets
    async uploadDataset(file) {
        const formData = new FormData();
        formData.append("file", file);
        return this.request("/api/datasets/upload", {
            method: "POST",
            body: formData,
        });
    },

    async listDatasets() {
        return this.request("/api/datasets");
    },

    async getDataset(datasetId) {
        return this.request(`/api/datasets/${datasetId}`);
    },

    async getDatasetProfile(datasetId) {
        return this.request(`/api/datasets/${datasetId}/profile`);
    },

    async deleteDataset(datasetId) {
        return this.request(`/api/datasets/${datasetId}`, {
            method: "DELETE",
        });
    },

    // Multi-Agent Analysis
    async runAnalysis(datasetId) {
        return this.request(`/api/analysis/${datasetId}/run`, {
            method: "POST",
        });
    },

    async getAnalysisStatus(analysisId) {
        return this.request(`/api/analysis/${analysisId}/status`);
    },

    async getAnalysisResults(analysisId) {
        return this.request(`/api/analysis/${analysisId}/results`);
    },

    async getAnalysisInsights(analysisId) {
        return this.request(`/api/analysis/${analysisId}/insights`);
    },

    async listAnalysisHistory() {
        return this.request("/api/analysis/history");
    },

    async deleteAnalysis(analysisId) {
        return this.request(`/api/analysis/${analysisId}`, {
            method: "DELETE",
        });
    },
};
