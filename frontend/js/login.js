/**
 * Multi-Agent BI Platform - Login Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    // Redirect if already authenticated
    if (Auth.redirectIfAuthenticated()) {
        return;
    }

    const form = document.getElementById("loginForm");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const rememberMeCheckbox = document.getElementById("rememberMe");
    const submitBtn = document.getElementById("submitBtn");
    const guestBtn = document.getElementById("guestBtn");
    const togglePasswordBtn = document.getElementById("togglePasswordBtn");
    const authAlert = document.getElementById("authAlert");
    const authSuccess = document.getElementById("authSuccess");

    // Check query params for notification flags
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("registered") === "1") {
        showSuccess("Account created successfully! Please sign in with your credentials.");
    } else if (urlParams.get("reset") === "1") {
        showSuccess("Password reset successfully! You can now log in with your new password.");
    }

    // Toggle password visibility
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener("click", () => {
            const isPassword = passwordInput.getAttribute("type") === "password";
            passwordInput.setAttribute("type", isPassword ? "text" : "password");
            const icon = togglePasswordBtn.querySelector("i");
            if (icon) {
                icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
            }
        });
    }

    // Submit handler
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlerts();

            const email = emailInput.value.trim();
            const password = passwordInput.value;
            const rememberMe = rememberMeCheckbox ? rememberMeCheckbox.checked : false;

            if (!email) {
                showError("Please enter your email address.");
                emailInput.focus();
                return;
            }

            if (!password) {
                showError("Please enter your password.");
                passwordInput.focus();
                return;
            }

            setLoading(true);

            try {
                const response = await API.login({
                    email,
                    password,
                    remember_me: rememberMe,
                });

                if (response && response.access_token) {
                    Auth.setSession(response.access_token, response.user);
                    
                    const redirectUrl = sessionStorage.getItem("redirect_after_login") || "dashboard.html";
                    sessionStorage.removeItem("redirect_after_login");
                    window.location.href = redirectUrl;
                } else {
                    showError("Invalid response from server. Please try again.");
                }
            } catch (err) {
                showError(err.message || "Failed to sign in. Please verify your credentials.");
            } finally {
                setLoading(false);
            }
        });
    }

    // Guest instant demo handler
    if (guestBtn) {
        guestBtn.addEventListener("click", async () => {
            clearAlerts();
            guestBtn.disabled = true;
            const originalGuestText = guestBtn.innerHTML;
            guestBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Preparing Guest Session...`;

            try {
                const response = await API.guestLogin();
                if (response && response.access_token) {
                    Auth.setSession(response.access_token, response.user);
                    window.location.href = "dashboard.html";
                } else {
                    showError("Failed to initiate guest session.");
                    guestBtn.disabled = false;
                    guestBtn.innerHTML = originalGuestText;
                }
            } catch (err) {
                showError(err.message || "Unable to start guest session.");
                guestBtn.disabled = false;
                guestBtn.innerHTML = originalGuestText;
            }
        });
    }

    function showError(msg) {
        if (authAlert) {
            authAlert.textContent = msg;
            authAlert.classList.remove("d-none");
        }
    }

    function showSuccess(msg) {
        if (authSuccess) {
            authSuccess.textContent = msg;
            authSuccess.classList.remove("d-none");
        }
    }

    function clearAlerts() {
        if (authAlert) {
            authAlert.textContent = "";
            authAlert.classList.add("d-none");
        }
        if (authSuccess) {
            authSuccess.textContent = "";
            authSuccess.classList.add("d-none");
        }
    }

    function setLoading(isLoading) {
        if (submitBtn) {
            submitBtn.disabled = isLoading;
            submitBtn.innerHTML = isLoading
                ? `<span class="spinner-border spinner-border-sm me-2"></span> Signing in...`
                : `<i class="bi bi-box-arrow-in-right me-1"></i> Sign In`;
        }
        if (guestBtn) {
            guestBtn.disabled = isLoading;
        }
    }
});

