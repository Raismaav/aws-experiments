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
        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showResult('error', 'File too large', `${file.name} exceeds the 10MB limit.`);
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
                showResult('success', 'Upload successful!', 
                    `File: ${result.filename}`, 
                    `S3 URL: ${result.s3_url}`);
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
