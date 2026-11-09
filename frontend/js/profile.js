/**
 * Multi-Agent BI Platform - User Profile Controller
 */

document.addEventListener("DOMContentLoaded", async () => {
    // Enforce authentication guard
    if (!Auth.requireAuth()) {
        return;
    }

    const profileAlert = document.getElementById("profileAlert");
    const profileSuccess = document.getElementById("profileSuccess");

    // Profile Display Elements
    const bigAvatar = document.getElementById("profileBigAvatar");
    const headerName = document.getElementById("profileHeaderName");
    const headerEmail = document.getElementById("profileHeaderEmail");
    const badgeType = document.getElementById("badgeAccountType");
    const badgeStatus = document.getElementById("badgeAccountStatus");
    const userIdEl = document.getElementById("profileUserId");
    const createdAtEl = document.getElementById("profileCreatedAt");
    const lastLoginEl = document.getElementById("profileLastLogin");

    // Edit Profile Form
    const editForm = document.getElementById("editProfileForm");
    const fullNameInput = document.getElementById("fullNameInput");
    const emailInput = document.getElementById("emailInput");
    const saveProfileBtn = document.getElementById("saveProfileBtn");

    // Change Password Form
    const changePwdForm = document.getElementById("changePasswordForm");
    const currentPwdInput = document.getElementById("currentPassword");
    const newPwdInput = document.getElementById("newPassword");
    const confirmNewPwdInput = document.getElementById("confirmNewPassword");
    const changePwdBtn = document.getElementById("changePasswordBtn");

    // Delete Account Modal
    const deletePasswordInput = document.getElementById("deletePasswordConfirm");
    const confirmDeleteBtn = document.getElementById("confirmDeleteAccountBtn");
    const deleteModalAlert = document.getElementById("deleteModalAlert");

    // Load initial profile data
    await loadUserProfile();

    // -------------------------------------------------------------
    // 1. Profile Data Loader
    // -------------------------------------------------------------
    async function loadUserProfile() {
        try {
            const user = await API.getMe();
            if (!user) return;

            // Update Auth cache
            Auth.setSession(Auth.getToken(), user);

            const displayName = user.full_name || user.username || "Analyst";
            const initial = displayName.charAt(0).toUpperCase();

            if (bigAvatar) bigAvatar.textContent = initial;
            if (headerName) headerName.textContent = displayName;
            if (headerEmail) headerEmail.textContent = user.email || "";
            if (fullNameInput) fullNameInput.value = displayName;
            if (emailInput) emailInput.value = user.email || "";

            if (badgeType) {
                if (user.is_guest) {
                    badgeType.className = "badge bg-warning-subtle text-warning px-3 py-2 rounded-pill";
                    badgeType.innerHTML = `<i class="bi bi-person-workspace me-1"></i> Guest Demo`;
                } else {
                    badgeType.className = "badge bg-primary-subtle text-primary px-3 py-2 rounded-pill";
                    badgeType.innerHTML = `<i class="bi bi-shield-check me-1"></i> Member`;
                }
            }

            if (badgeStatus) {
                if (user.is_active) {
                    badgeStatus.className = "badge bg-success-subtle text-success px-3 py-2 rounded-pill";
                    badgeStatus.innerHTML = `<i class="bi bi-check-circle me-1"></i> Active`;
                } else {
                    badgeStatus.className = "badge bg-secondary-subtle text-secondary px-3 py-2 rounded-pill";
                    badgeStatus.innerHTML = `<i class="bi bi-pause-circle me-1"></i> Inactive`;
                }
            }

            if (userIdEl) userIdEl.textContent = user.id || "--";
            if (createdAtEl) createdAtEl.textContent = formatDate(user.created_at);
            if (lastLoginEl) lastLoginEl.textContent = formatDate(user.last_login);
        } catch (err) {
            showError("Failed to load user profile: " + (err.message || "Unknown error"));
        }
    }

    // -------------------------------------------------------------
    // 2. Edit Profile Submission
    // -------------------------------------------------------------
    if (editForm) {
        editForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlerts();

            const fullName = fullNameInput.value.trim();
            if (!fullName) {
                showError("Full Name cannot be empty.");
                return;
            }

            saveProfileBtn.disabled = true;
            saveProfileBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Saving...`;

            try {
                const updated = await API.updateProfile(fullName);
                Auth.setSession(Auth.getToken(), updated);

                if (headerName) headerName.textContent = updated.full_name;
                if (bigAvatar) bigAvatar.textContent = updated.full_name.charAt(0).toUpperCase();

                showSuccess("Profile details updated successfully.");
            } catch (err) {
                showError(err.message || "Failed to update profile.");
            } finally {
                saveProfileBtn.disabled = false;
                saveProfileBtn.innerHTML = `<i class="bi bi-save me-1"></i> Save Changes`;
            }
        });
    }

    // -------------------------------------------------------------
    // 3. Change Password Submission
    // -------------------------------------------------------------
    if (changePwdForm) {
        changePwdForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlerts();

            const currentPwd = currentPwdInput.value;
            const newPwd = newPwdInput.value;
            const confirmNewPwd = confirmNewPwdInput.value;

            if (!currentPwd) {
                showError("Please enter your current password.");
                return;
            }

            if (newPwd.length < 8) {
                showError("New password must be at least 8 characters long.");
                return;
            }

            if (newPwd !== confirmNewPwd) {
                showError("New passwords do not match.");
                return;
            }

            changePwdBtn.disabled = true;
            changePwdBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Updating...`;

            try {
                await API.changePassword(currentPwd, newPwd, confirmNewPwd);
                showSuccess("Password changed successfully.");
                changePwdForm.reset();
            } catch (err) {
                showError(err.message || "Failed to change password.");
            } finally {
                changePwdBtn.disabled = false;
                changePwdBtn.innerHTML = `<i class="bi bi-shield-check me-1"></i> Update Password`;
            }
        });
    }

    // -------------------------------------------------------------
    // 4. Delete Account Submission
    // -------------------------------------------------------------
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", async () => {
            const pwd = deletePasswordInput ? deletePasswordInput.value : "";
            if (!pwd) {
                if (deleteModalAlert) {
                    deleteModalAlert.textContent = "Please enter your password to confirm deletion.";
                    deleteModalAlert.classList.remove("d-none");
                }
                return;
            }

            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Deleting...`;

            try {
                await API.deleteAccount(pwd);
                // Dismiss modal
                const modalEl = document.getElementById("deleteAccountModal");
                if (modalEl && window.bootstrap) {
                    const modal = window.bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }
                Auth.logout();
            } catch (err) {
                if (deleteModalAlert) {
                    deleteModalAlert.textContent = err.message || "Failed to delete account.";
                    deleteModalAlert.classList.remove("d-none");
                }
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = `<i class="bi bi-trash me-1"></i> Permanently Delete My Account`;
            }
        });
    }

    // Helper functions
    function formatDate(isoStr) {
        if (!isoStr) return "--";
        try {
            const d = new Date(isoStr);
            return d.toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return isoStr;
        }
    }

    function showError(msg) {
        if (profileAlert) {
            profileAlert.textContent = msg;
            profileAlert.classList.remove("d-none");
        }
    }

    function showSuccess(msg) {
        if (profileSuccess) {
            profileSuccess.textContent = msg;
            profileSuccess.classList.remove("d-none");
        }
    }

    function clearAlerts() {
        if (profileAlert) {
            profileAlert.textContent = "";
            profileAlert.classList.add("d-none");
        }
        if (profileSuccess) {
            profileSuccess.textContent = "";
            profileSuccess.classList.add("d-none");
        }
    }
});
