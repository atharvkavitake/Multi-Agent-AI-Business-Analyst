/**
 * Multi-Agent BI Platform - Upload Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const progressBox = document.getElementById("uploadProgressBox");
    const previewContainer = document.getElementById("previewContainer");
    const analyzeBtn = document.getElementById("analyzeNowBtn");

    let currentUploadedDatasetId = null;

    // Check if an active dataset already exists to render its preview
    const existingDatasetId = AppState.currentDatasetId;
    if (existingDatasetId) {
        loadExistingDataset(existingDatasetId);
    }

    // Drag and Drop Events
    if (dropzone) {
        ["dragenter", "dragover"].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(name => {
            dropzone.addEventListener(name, (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
            });
        });

        dropzone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    async function handleFileUpload(file) {
        // Validate extension
        const validExts = [".csv", ".xlsx", ".xls"];
        const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
        if (!validExts.includes(ext)) {
            showToast(`Unsupported format '${ext}'. Allowed: .csv, .xlsx, .xls`, "danger");
            return;
        }

        // Validate size (25MB)
        if (file.size > 25 * 1024 * 1024) {
            showToast("File size exceeds 25 MB limit.", "danger");
            return;
        }

        // Show Progress
        if (progressBox) progressBox.classList.remove("d-none");
        document.getElementById("uploadFilename").innerText = `Uploading and inspecting ${file.name}...`;

        try {
            const data = await API.uploadDataset(file);
            currentUploadedDatasetId = data.dataset_id;

            // Set global active dataset
            AppState.setActiveDataset(data.dataset_id, data.filename);

            showToast(`Dataset '${data.filename}' successfully validated!`, "success");
            renderDatasetPreview(data);
        } catch (error) {
            console.error("Upload failed:", error);
            showToast(`Upload failed: ${error.message}`, "danger");
        } finally {
            if (progressBox) progressBox.classList.add("d-none");
        }
    }

    async function loadExistingDataset(datasetId) {
        try {
            const data = await API.getDataset(datasetId);
            currentUploadedDatasetId = data.dataset_id;
            renderDatasetPreview(data);
        } catch (e) {
            // Expired or not found
        }
    }

    function renderDatasetPreview(data) {
        if (!previewContainer) return;
        previewContainer.classList.remove("d-none");

        // Metadata Header
        document.getElementById("metaFilename").innerText = data.filename;
        document.getElementById("metaRows").innerText = formatNumber(data.row_count);
        document.getElementById("metaCols").innerText = data.column_count;
        document.getElementById("metaSize").innerText = data.file_size_formatted;

        // Column Inspection Table
        const colBody = document.getElementById("columnMetaBody");
        if (colBody && data.columns) {
            colBody.innerHTML = data.columns.map(c => {
                let typeBadge = "badge-primary";
                if (c.data_type === "numeric") typeBadge = "badge-success";
                if (c.data_type === "datetime") typeBadge = "badge-warning";

                const sampleStr = c.sample_values ? c.sample_values.slice(0, 3).join(", ") : "—";

                return `
                    <tr>
                        <td class="fw-bold">${c.name}</td>
                        <td><span class="badge-custom ${typeBadge}">${c.data_type}</span></td>
                        <td><code class="small text-secondary">${c.raw_type}</code></td>
                        <td>${c.null_count} (${c.null_percentage}%)</td>
                        <td>${formatNumber(c.unique_count)}</td>
                        <td><small class="text-secondary text-truncate d-inline-block" style="max-width: 250px;">${sampleStr}</small></td>
                    </tr>
                `;
            }).join("");
        }

        // Preview Table
        const thead = document.getElementById("previewThead");
        const tbody = document.getElementById("previewTbody");

        if (thead && data.preview && data.preview.columns) {
            thead.innerHTML = `<tr>${data.preview.columns.map(col => `<th>${col}</th>`).join("")}</tr>`;
        }

        if (tbody && data.preview && data.preview.rows) {
            tbody.innerHTML = data.preview.rows.map(row => {
                const cells = data.preview.columns.map(col => {
                    const val = row[col];
                    return `<td>${val !== null && val !== undefined ? val : '<span class="text-muted">null</span>'}</td>`;
                }).join("");
                return `<tr>${cells}</tr>`;
            }).join("");
        }

        // Smooth scroll to preview
        previewContainer.scrollIntoView({ behavior: "smooth" });
    }

    // Run Analysis Button Handler
    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", async () => {
            const dId = currentUploadedDatasetId || AppState.currentDatasetId;
            if (!dId) {
                showToast("No active dataset loaded.", "warning");
                return;
            }

            try {
                analyzeBtn.disabled = true;
                analyzeBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Orchestrating 7 Agents...`;
                showToast("Executing multi-agent analytics pipeline...", "info");

                const result = await API.runAnalysis(dId);
                AppState.setActiveAnalysis(result.analysis_id);

                showToast("Multi-Agent Analysis Complete!", "success");
                window.location.href = "insights.html";
            } catch (error) {
                console.error("Analysis launch error:", error);
                showToast(`Analysis failed: ${error.message}`, "danger");
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = `<i class="bi bi-play-circle-fill"></i> Run Multi-Agent Analysis`;
            }
        });
    }
});

