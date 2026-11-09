/**
 * Multi-Agent BI Platform - Authentication Manager & Navigation Guards
 */

const Auth = {
    TOKEN_KEY: "bi_access_token",
    USER_KEY: "bi_user_data",

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY) || "";
    },

    getUser() {
        try {
            const raw = localStorage.getItem(this.USER_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    setSession(token, user) {
        if (token) localStorage.setItem(this.TOKEN_KEY, token);
        if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        this.renderSidebarUserProfile();
    },

    async logout() {
        try {
            await fetch((window.API_BASE_URL || "") + "/api/auth/logout", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${this.getToken()}`,
                },
            });
        } catch (e) {
            // Ignore network errors during logout
        } finally {
            localStorage.removeItem(this.TOKEN_KEY);
            localStorage.removeItem(this.USER_KEY);
            localStorage.removeItem("bi_active_dataset_id");
            localStorage.removeItem("bi_active_dataset_name");
            localStorage.removeItem("bi_active_analysis_id");
            window.location.href = "login.html";
        }
    },

    requireAuth() {
        if (!this.isAuthenticated()) {
            const currentPath = window.location.pathname.split("/").pop();
            if (currentPath && currentPath !== "login.html" && currentPath !== "signup.html" && currentPath !== "forgot-password.html" && currentPath !== "reset-password.html" && currentPath !== "index.html") {
                sessionStorage.setItem("redirect_after_login", window.location.href);
            }
            window.location.href = "login.html";
            return false;
        }
        return true;
    },

    redirectIfAuthenticated() {
        if (this.isAuthenticated()) {
            const target = sessionStorage.getItem("redirect_after_login") || "dashboard.html";
            sessionStorage.removeItem("redirect_after_login");
            window.location.href = target;
            return true;
        }
        return false;
    },

    renderSidebarUserProfile() {
        const user = this.getUser();
        const profileBox = document.getElementById("sidebarUserProfile");
        if (!profileBox) return;

        if (user && this.isAuthenticated()) {
            const name = user.full_name || user.username || "Analyst";
            const email = user.email || "user@enterprise.com";
            const initial = name.charAt(0).toUpperCase();

            profileBox.innerHTML = `
                <a href="profile.html" class="sidebar-user-avatar" title="View Profile">
                    ${initial}
                </a>
                <div class="sidebar-user-meta">
                    <div class="sidebar-user-name" title="${name}">${name}</div>
                    <div class="sidebar-user-email" title="${email}">${email}</div>
                </div>
                <button id="sidebarLogoutBtn" class="sidebar-logout-btn" title="Log Out" aria-label="Log Out">
                    <i class="bi bi-box-arrow-right"></i>
                </button>
            `;

            const logoutBtn = document.getElementById("sidebarLogoutBtn");
            if (logoutBtn) {
                logoutBtn.addEventListener("click", () => this.logout());
            }
        } else {
            profileBox.innerHTML = `
                <div class="d-flex align-items-center justify-content-between w-100">
                    <a href="login.html" class="btn btn-sm btn-outline-primary w-100">
                        <i class="bi bi-box-arrow-in-right"></i> Sign In
                    </a>
                </div>
            `;
        }
    },
};

// Auto-run on DOM ready for authenticated pages
document.addEventListener("DOMContentLoaded", () => {
    Auth.renderSidebarUserProfile();
});
