/**
 * Multi-Agent BI Platform - Password Reset Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // Forgot Password Flow
    // -------------------------------------------------------------
    const forgotForm = document.getElementById("forgotPasswordForm");
    if (forgotForm) {
        const emailInput = document.getElementById("email");
        const submitBtn = document.getElementById("submitBtn");
        const authAlert = document.getElementById("authAlert");
        const authSuccess = document.getElementById("authSuccess");
        const devTokenCard = document.getElementById("devTokenCard");
        const devResetLink = document.getElementById("devResetLink");

        forgotForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlerts();

            const email = emailInput.value.trim();
            if (!email) {
                showError("Please enter your email address.");
                emailInput.focus();
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Sending...`;

            try {
                const response = await API.forgotPassword(email);
                showSuccess(response.message || "Instructions have been sent if this email is registered.");

                // Development mode support
                if (response.detail && response.detail.includes("Development reset token:")) {
                    const parts = response.detail.split("Development reset token:");
                    if (parts.length > 1) {
                        const token = parts[1].trim();
                        if (devTokenCard && devResetLink) {
                            devResetLink.href = `reset-password.html?token=${encodeURIComponent(token)}`;
                            devTokenCard.classList.remove("d-none");
                        }
                    }
                }
            } catch (err) {
                showError(err.message || "Unable to process password reset request. Please try again.");
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<i class="bi bi-send me-1"></i> Send Reset Instructions`;
            }
        });

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
            if (devTokenCard) {
                devTokenCard.classList.add("d-none");
            }
        }
    }

    // -------------------------------------------------------------
    // Reset Password Flow
    // -------------------------------------------------------------
    const resetForm = document.getElementById("resetPasswordForm");
    if (resetForm) {
        const newPasswordInput = document.getElementById("newPassword");
        const confirmPasswordInput = document.getElementById("confirmPassword");
        const submitBtn = document.getElementById("submitBtn");
        const authAlert = document.getElementById("authAlert");
        const authSuccess = document.getElementById("authSuccess");
        const strengthBar = document.getElementById("strengthProgressBar");
        const strengthText = document.getElementById("strengthText");
        const mismatchFeedback = document.getElementById("passwordMismatchFeedback");
        const toggleNewBtn = document.getElementById("toggleNewPasswordBtn");
        const toggleConfirmBtn = document.getElementById("toggleConfirmPasswordBtn");

        // Extract token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get("token");

        if (!token) {
            showError("Invalid or missing password recovery token. Please request a new link.");
            submitBtn.disabled = true;
            newPasswordInput.disabled = true;
            confirmPasswordInput.disabled = true;
        }

        // Visibility toggles
        setupToggle(toggleNewBtn, newPasswordInput);
        setupToggle(toggleConfirmBtn, confirmPasswordInput);

        // Password strength meter
        newPasswordInput.addEventListener("input", () => {
            const pwd = newPasswordInput.value;
            const strength = evaluatePasswordStrength(pwd);

            strengthBar.style.width = `${strength.percent}%`;
            strengthBar.className = `progress-bar ${strength.barClass}`;
            strengthText.textContent = strength.label;
            strengthText.className = `fw-semibold ${strength.textClass}`;
        });

        // Confirm password match check
        confirmPasswordInput.addEventListener("input", () => {
            if (confirmPasswordInput.value && newPasswordInput.value !== confirmPasswordInput.value) {
                mismatchFeedback.classList.remove("d-none");
            } else {
                mismatchFeedback.classList.add("d-none");
            }
        });

        // Submission
        resetForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlerts();

            if (!token) {
                showError("No valid reset token provided.");
                return;
            }

            const newPassword = newPasswordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            if (newPassword.length < 8) {
                showError("Password must be at least 8 characters long.");
                newPasswordInput.focus();
                return;
            }

            if (newPassword !== confirmPassword) {
                showError("Passwords do not match.");
                confirmPasswordInput.focus();
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Updating...`;

            try {
                const response = await API.resetPassword(token, newPassword, confirmPassword);
                showSuccess(response.message || "Password reset successfully! Redirecting to sign in...");
                setTimeout(() => {
                    window.location.href = "login.html?reset=1";
                }, 1500);
            } catch (err) {
                showError(err.message || "Failed to reset password. The link may have expired.");
                submitBtn.disabled = false;
                submitBtn.innerHTML = `<i class="bi bi-check-circle me-1"></i> Update Password`;
            }
        });

        function setupToggle(btn, input) {
            if (btn && input) {
                btn.addEventListener("click", () => {
                    const isPwd = input.getAttribute("type") === "password";
                    input.setAttribute("type", isPwd ? "text" : "password");
                    const icon = btn.querySelector("i");
                    if (icon) {
                        icon.className = isPwd ? "bi bi-eye-slash" : "bi bi-eye";
                    }
                });
            }
        }

        function evaluatePasswordStrength(password) {
            if (!password) {
                return { percent: 0, label: "None", barClass: "", textClass: "text-secondary" };
            }

            let score = 0;
            if (password.length >= 8) score += 1;
            if (password.length >= 12) score += 1;
            if (/[A-Z]/.test(password)) score += 1;
            if (/[0-9]/.test(password)) score += 1;
            if (/[^A-Za-z0-9]/.test(password)) score += 1;

            if (score <= 1) {
                return { percent: 25, label: "Weak", barClass: "bg-danger", textClass: "text-danger" };
            } else if (score <= 3) {
                return { percent: 55, label: "Medium", barClass: "bg-warning", textClass: "text-warning" };
            } else if (score === 4) {
                return { percent: 80, label: "Good", barClass: "bg-info", textClass: "text-info" };
            } else {
                return { percent: 100, label: "Strong", barClass: "bg-success", textClass: "text-success" };
            }
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
    }
});
