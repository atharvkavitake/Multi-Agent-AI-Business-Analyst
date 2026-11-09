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

        // Auto-attach Bearer token if available
        const token = (typeof Auth !== "undefined" && Auth.getToken) ? Auth.getToken() : localStorage.getItem("bi_access_token");
        if (token && !headers["Authorization"]) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: "include", // Supports HttpOnly cookies
            });

            if (!response.ok) {
                // Handle unauthorized session expiration
                if (response.status === 401 && typeof Auth !== "undefined" && Auth.isAuthenticated()) {
                    console.warn("[Auth] Session expired or unauthorized.");
                }

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

    // Health Check
    async checkHealth() {
        return this.request("/health");
    },

    // -------------------------------------------------------------
    // Authentication Endpoints
    // -------------------------------------------------------------
    async register(data) {
        return this.request("/api/auth/register", {
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    async login(data) {
        return this.request("/api/auth/login", {
            method: "POST",
            body: JSON.stringify(data),
        });
    },

    async guestLogin() {
        return this.request("/api/auth/guest", {
            method: "POST",
        });
    },

    async logout() {
        return this.request("/api/auth/logout", {
            method: "POST",
        });
    },

    async getMe() {
        return this.request("/api/auth/me");
    },

    async forgotPassword(email) {
        return this.request("/api/auth/forgot-password", {
            method: "POST",
            body: JSON.stringify({ email }),
        });
    },

    async resetPassword(token, newPassword, confirmPassword) {
        return this.request("/api/auth/reset-password", {
            method: "POST",
            body: JSON.stringify({
                token,
                new_password: newPassword,
                confirm_password: confirmPassword,
            }),
        });
    },

    // -------------------------------------------------------------
    // User Profile Endpoints
    // -------------------------------------------------------------
    async updateProfile(fullName) {
        return this.request("/api/users/me", {
            method: "PUT",
            body: JSON.stringify({ full_name: fullName }),
        });
    },

    async changePassword(currentPassword, newPassword, confirmPassword) {
        return this.request("/api/users/change-password", {
            method: "PUT",
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword,
            }),
        });
    },

    async deleteAccount(password) {
        return this.request("/api/users/me", {
            method: "DELETE",
            body: JSON.stringify({ password }),
        });
    },

    // -------------------------------------------------------------
    // Datasets Endpoints
    // -------------------------------------------------------------
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

    // -------------------------------------------------------------
    // Multi-Agent Analysis Endpoints
    // -------------------------------------------------------------
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

    // -------------------------------------------------------------
    // Personalized Analysis History Endpoints
    // -------------------------------------------------------------
    async listAnalysisHistory(params = {}) {
        const query = new URLSearchParams();
        if (params.search) query.append("search", params.search);
        if (params.status && params.status !== "all") query.append("status", params.status);
        if (params.date_from) query.append("date_from", params.date_from);
        if (params.date_to) query.append("date_to", params.date_to);
        if (params.sort) query.append("sort", params.sort);
        if (params.page) query.append("page", params.page);
        if (params.page_size) query.append("page_size", params.page_size);

        const qs = query.toString() ? `?${query.toString()}` : "";
        return this.request(`/api/history${qs}`);
    },

    async getAnalysisHistoryDetail(analysisId) {
        return this.request(`/api/history/${analysisId}`);
    },

    async deleteAnalysis(analysisId) {
        return this.request(`/api/history/${analysisId}`, {
            method: "DELETE",
        });
    },
};
