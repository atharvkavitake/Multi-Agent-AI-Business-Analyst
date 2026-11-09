/**
 * Multi-Agent BI Platform - Sign Up Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    // Redirect if already logged in
    if (Auth.redirectIfAuthenticated()) return;

    const form = document.getElementById("signupForm");
    const fullNameInput = document.getElementById("fullName");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirmPassword");
    const alertBox = document.getElementById("authAlert");
    const submitBtn = document.getElementById("submitBtn");

    const togglePasswordBtn = document.getElementById("togglePasswordBtn");
    const toggleConfirmPasswordBtn = document.getElementById("toggleConfirmPasswordBtn");

    const strengthFill = document.getElementById("strengthFill");
    const strengthLabel = document.getElementById("strengthLabel");
    const mismatchHint = document.getElementById("passwordMismatchHint");

    // Toggle Password Visibility
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener("click", () => {
            const isPassword = passwordInput.type === "password";
            passwordInput.type = isPassword ? "text" : "password";
            togglePasswordBtn.innerHTML = isPassword ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        });
    }

    if (toggleConfirmPasswordBtn && confirmPasswordInput) {
        toggleConfirmPasswordBtn.addEventListener("click", () => {
            const isPassword = confirmPasswordInput.type === "password";
            confirmPasswordInput.type = isPassword ? "text" : "password";
            toggleConfirmPasswordBtn.innerHTML = isPassword ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        });
    }

    // Password Strength Meter
    if (passwordInput && strengthFill && strengthLabel) {
        passwordInput.addEventListener("input", () => {
            const val = passwordInput.value;
            const score = calculatePasswordStrength(val);

            if (!val) {
                strengthFill.style.width = "0%";
                strengthFill.style.backgroundColor = "transparent";
                strengthLabel.innerText = "Enter password";
                strengthLabel.style.color = "var(--text-muted)";
                return;
            }

            if (score <= 1) {
                strengthFill.style.width = "25%";
                strengthFill.style.backgroundColor = "var(--danger)";
                strengthLabel.innerText = "Weak";
                strengthLabel.style.color = "var(--danger)";
            } else if (score === 2) {
                strengthFill.style.width = "50%";
                strengthFill.style.backgroundColor = "var(--warning)";
                strengthLabel.innerText = "Fair";
                strengthLabel.style.color = "var(--warning)";
            } else if (score === 3) {
                strengthFill.style.width = "75%";
                strengthFill.style.backgroundColor = "var(--info)";
                strengthLabel.innerText = "Good";
                strengthLabel.style.color = "var(--info)";
            } else {
                strengthFill.style.width = "100%";
                strengthFill.style.backgroundColor = "var(--success)";
                strengthLabel.innerText = "Strong";
                strengthLabel.style.color = "var(--success)";
            }

            checkPasswordMatch();
        });
    }

    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener("input", checkPasswordMatch);
    }

    function checkPasswordMatch() {
        if (!confirmPasswordInput.value) {
            mismatchHint.classList.add("d-none");
            return;
        }
        if (passwordInput.value !== confirmPasswordInput.value) {
            mismatchHint.classList.remove("d-none");
        } else {
            mismatchHint.classList.add("d-none");
        }
    }

    function calculatePasswordStrength(pw) {
        let score = 0;
        if (pw.length >= 8) score += 1;
        if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score += 1;
        if (/\d/.test(pw)) score += 1;
        if (/[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/`~]/.test(pw)) score += 1;
        return score;
    }

    // Form Submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        alertBox.classList.add("d-none");

        const fullName = fullNameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Frontend validation
        if (!fullName) {
            showAlert("Please enter your full name.");
            return;
        }
        if (!email) {
            showAlert("Please enter a valid email address.");
            return;
        }
        if (password.length < 8) {
            showAlert("Password must be at least 8 characters long.");
            return;
        }
        if (password !== confirmPassword) {
            showAlert("Passwords do not match.");
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Creating Account...';

            const resp = await API.register({
                full_name: fullName,
                email: email,
                password: password,
                confirm_password: confirmPassword,
            });

            // Store session
            Auth.setSession(resp.access_token, resp.user);

            // Redirect to dashboard
            window.location.href = "dashboard.html";
        } catch (error) {
            showAlert(error.message || "Registration failed. Please try again.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-person-plus-fill me-1"></i> Create Account';
        }
    });

    function showAlert(msg) {
        alertBox.innerText = msg;
        alertBox.classList.remove("d-none");
        alertBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
});

