document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const results = document.getElementById('results');

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        handleFiles(files);
    });

    function handleFiles(files) {
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                uploadFile(file);
            } else {
                showResult('error', 'Invalid file type', `${file.name} is not an image file.`);
            }
        });
    }

    async function uploadFile(file) {
        // Validate file size (500MB for RAW, 10MB for regular images)
        const isRaw = file.name.toLowerCase().match(/\.(cr2|cr3|nef|nrw|arw|sr2|raf|rw2|orf|pef|dng|raw|rwz|3fr|fff|hdr|srw|mrw|mef|mos|bay|dcr|kdc|erf|mdc|x3f|r3d|cine|dpx|exr|tga|tif|tiff)$/);
        const maxSize = isRaw ? 500 * 1024 * 1024 : 10 * 1024 * 1024;
        
        if (file.size > maxSize) {
            const maxSizeMB = maxSize / (1024 * 1024);
            showResult('error', 'File too large', `${file.name} exceeds the ${maxSizeMB}MB limit for ${isRaw ? 'RAW' : 'regular'} images.`);
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show progress
        showProgress();
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                if (result.is_raw) {
                    showRawResult(result);
                } else {
                    showRegularResult(result);
                }
            } else {
                showResult('error', 'Upload failed', result.detail || 'Unknown error occurred');
            }
        } catch (error) {
            showResult('error', 'Upload failed', 'Network error or server unavailable');
        } finally {
            hideProgress();
        }
    }

    function showProgress() {
        progressContainer.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Uploading...';
        
        // Simulate progress animation
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);
        
        // Store interval ID to clear later
        progressContainer.dataset.interval = interval;
    }

    function hideProgress() {
        progressContainer.style.display = 'none';
        // Clear progress animation
        if (progressContainer.dataset.interval) {
            clearInterval(parseInt(progressContainer.dataset.interval));
        }
    }

    function showResult(type, title, message, additionalInfo = '') {
        const resultItem = document.createElement('div');
        resultItem.className = `result-item ${type}`;
        
        let html = `
            <h4>${title}</h4>
            <p>${message}</p>
        `;
        
        if (additionalInfo) {
            if (additionalInfo.includes('S3 URL:')) {
                // Make S3 URL clickable
                const url = additionalInfo.split('S3 URL: ')[1];
                html += `<p>S3 URL: <a href="${url}" target="_blank">${url}</a></p>`;
            } else {
                html += `<p>${additionalInfo}</p>`;
            }
        }
        
        resultItem.innerHTML = html;
        
        // Add to results
        results.appendChild(resultItem);
        
        // Auto-remove after 10 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                resultItem.style.opacity = '0';
                setTimeout(() => {
                    if (resultItem.parentNode) {
                        resultItem.parentNode.removeChild(resultItem);
                    }
                }, 500);
            }, 10000);
        }
        
        // Scroll to results
        results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showRawResult(result) {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item success raw-result';
        
        let html = `
            <h4>🎯 RAW File Processed Successfully!</h4>
            <p><strong>File:</strong> ${result.filename}</p>
            <p><strong>Size:</strong> ${(result.file_size / (1024*1024)).toFixed(2)} MB</p>
            <p><strong>Format:</strong> ${result.processing_info.original_format.toUpperCase()}</p>
        `;
        
        // Add metadata if available
        if (result.metadata && Object.keys(result.metadata).length > 0) {
            html += '<div class="metadata-section">';
            html += '<h5>📷 Camera Information:</h5>';
            if (result.metadata.camera_make !== 'Unknown') {
                html += `<p><strong>Camera:</strong> ${result.metadata.camera_make} ${result.metadata.camera_model}</p>`;
            }
            if (result.metadata.iso > 0) {
                html += `<p><strong>ISO:</strong> ${result.metadata.iso}</p>`;
            }
            if (result.metadata.exposure_time > 0) {
                html += `<p><strong>Exposure:</strong> 1/${Math.round(1/result.metadata.exposure_time)}s</p>`;
            }
            if (result.metadata.f_number > 0) {
                html += `<p><strong>Aperture:</strong> f/${result.metadata.f_number}</p>`;
            }
            if (result.metadata.focal_length > 0) {
                html += `<p><strong>Focal Length:</strong> ${result.metadata.focal_length}mm</p>`;
            }
            html += '</div>';
        }
        
        // Add URLs
        html += '<div class="urls-section">';
        html += '<h5>🔗 Download Links:</h5>';
        html += `<p><strong>Original RAW:</strong> <a href="${result.urls.raw}" target="_blank">Download RAW</a></p>`;
        html += `<p><strong>Processed JPEG:</strong> <a href="${result.urls.processed}" target="_blank">View JPEG</a></p>`;
        html += `<p><strong>Thumbnail:</strong> <a href="${result.urls.thumbnail}" target="_blank">View Thumbnail</a></p>`;
        html += '</div>';
        
        resultItem.innerHTML = html;
        results.appendChild(resultItem);
        
        // Auto-remove after 15 seconds for RAW files (longer due to more info)
        setTimeout(() => {
            resultItem.style.opacity = '0';
            setTimeout(() => {
                if (resultItem.parentNode) {
                    resultItem.parentNode.removeChild(resultItem);
                }
            }, 500);
        }, 15000);
        
        results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function showRegularResult(result) {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item success';
        
        let html = `
            <h4>✅ Image Uploaded Successfully!</h4>
            <p><strong>File:</strong> ${result.filename}</p>
            <p><strong>Size:</strong> ${(result.file_size / (1024*1024)).toFixed(2)} MB</p>
            <p><strong>Format:</strong> ${result.processing_info.format.toUpperCase()}</p>
        `;
        
        if (result.urls.image) {
            html += `<p><strong>URL:</strong> <a href="${result.urls.image}" target="_blank">${result.urls.image}</a></p>`;
        }
        
        resultItem.innerHTML = html;
        results.appendChild(resultItem);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            resultItem.style.opacity = '0';
            setTimeout(() => {
                if (resultItem.parentNode) {
                    resultItem.parentNode.removeChild(resultItem);
                }
            }, 500);
        }, 10000);
        
        results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Add some visual feedback for file selection
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            uploadArea.style.borderColor = '#667eea';
            setTimeout(() => {
                uploadArea.style.borderColor = '#ddd';
            }, 1000);
        }
    });
});
