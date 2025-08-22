document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const results = document.getElementById('results');
    
    // Gallery elements
    const galleryGrid = document.getElementById('galleryGrid');
    const refreshGalleryBtn = document.getElementById('refreshGallery');
    const galleryFilter = document.getElementById('galleryFilter');
    
    // Modal elements
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modalTitle');
    const modalInfo = document.getElementById('modalInfo');
    const downloadBtn = document.getElementById('downloadBtn');
    const closeModal = document.querySelector('.close');
    const closeModalBtn = document.getElementById('closeModal');
    
    // Current modal data
    let currentModalData = null;

    // Initialize gallery
    loadGallery();

    // Gallery event listeners
    refreshGalleryBtn.addEventListener('click', loadGallery);
    galleryFilter.addEventListener('change', filterGallery);
    
    // Modal event listeners
    closeModal.addEventListener('click', closeImageModal);
    closeModalBtn.addEventListener('click', closeImageModal);
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeImageModal();
        }
    });

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
                // Refresh gallery after successful upload
                setTimeout(loadGallery, 1000);
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
            if (result.metadata.width && result.metadata.height) {
                html += `<p><strong>Resolution:</strong> ${result.metadata.width} x ${result.metadata.height}</p>`;
            }
            if (result.metadata.colors) {
                html += `<p><strong>Colors:</strong> ${result.metadata.colors}</p>`;
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
        
        // Add to results
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
        
        // Add to results
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

    // Gallery Functions
    async function loadGallery() {
        try {
            galleryGrid.innerHTML = '<div class="gallery-loading">Loading gallery...</div>';
            
            const response = await fetch('/images?limit=100');
            const data = await response.json();
            
            if (data.images && data.images.length > 0) {
                displayGallery(data.images);
            } else {
                galleryGrid.innerHTML = `
                    <div class="gallery-empty">
                        <h3>📸 No images found</h3>
                        <p>Upload some images to see them here!</p>
                    </div>
                `;
            }
        } catch (error) {
            galleryGrid.innerHTML = `
                <div class="gallery-empty">
                    <h3>❌ Error loading gallery</h3>
                    <p>Failed to load images. Please try again.</p>
                </div>
            `;
        }
    }

    function displayGallery(images) {
        galleryGrid.innerHTML = '';
        
        images.forEach(image => {
            const galleryItem = createGalleryItem(image);
            galleryGrid.appendChild(galleryItem);
        });
    }

    function createGalleryItem(image) {
        const item = document.createElement('div');
        item.className = `gallery-item ${image.is_raw ? 'raw' : 'regular'}`;
        
        const imageType = image.is_raw ? 'RAW' : 'Regular';
        const fileSize = (image.size / (1024 * 1024)).toFixed(2);
        
        // Use high-quality images for display, thumbnails only for very small previews
        // For better quality, we'll use the main display URL instead of thumbnails
        let imageSrc = image.url; // Use high-quality image for display
        
        item.innerHTML = `
            <img src="${imageSrc}" alt="${image.filename}" class="gallery-item-image" 
                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjVGNUY1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTk5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZTwvdGV4dD4KPC9zdmc+'">
            <div class="gallery-item-info">
                <div class="gallery-item-title">${image.filename}</div>
                <div class="gallery-item-meta">
                    <span>${fileSize} MB</span>
                    <span class="gallery-item-type ${image.is_raw ? 'raw' : 'regular'}">${imageType}</span>
                </div>
            </div>
        `;
        
        // Add click event to open modal
        item.addEventListener('click', () => openImageModal(image));
        
        return item;
    }

    function filterGallery() {
        const filter = galleryFilter.value;
        const items = galleryGrid.querySelectorAll('.gallery-item');
        
        items.forEach(item => {
            if (filter === 'all' || 
                (filter === 'raw' && item.classList.contains('raw')) ||
                (filter === 'regular' && item.classList.contains('regular'))) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Modal Functions
    function openImageModal(image) {
        currentModalData = image;
        
        // Set modal content
        modalTitle.textContent = image.filename;
        modalImage.src = image.url;
        
        // Set modal info
        const fileSize = (image.size / (1024 * 1024)).toFixed(2);
        const uploadDate = new Date(image.last_modified).toLocaleDateString();
        
        modalInfo.innerHTML = `
            <p><strong>File:</strong> ${image.filename}</p>
            <p><strong>Type:</strong> ${image.is_raw ? 'RAW' : 'Regular'} Image</p>
            <p><strong>Size:</strong> ${fileSize} MB</p>
            <p><strong>Uploaded:</strong> ${uploadDate}</p>
            <p><strong>Folder:</strong> ${image.folder}</p>
        `;
        
        // Generate download buttons based on image type
        generateDownloadButtons(image);
        
        // Show modal
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    function generateDownloadButtons(image) {
        const downloadButtonsContainer = document.getElementById('downloadButtons');
        
        if (image.is_raw) {
            // For RAW files, show two download buttons
            downloadButtonsContainer.innerHTML = `
                <button class="btn btn-download btn-download-processed" id="downloadProcessedBtn">
                    ⬇️ Download JPEG (Processed)
                </button>
                <button class="btn btn-download btn-download-raw" id="downloadRawBtn">
                    ⬇️ Download RAW (Original)
                </button>
            `;
            
            // Add event listeners for RAW download buttons
            document.getElementById('downloadProcessedBtn').addEventListener('click', () => {
                downloadImage(image.filename, 'processed', image.url);
            });
            
            document.getElementById('downloadRawBtn').addEventListener('click', () => {
                downloadImage(image.filename, 'raw', image.raw_original_url);
            });
        } else {
            // For regular images, show one download button
            downloadButtonsContainer.innerHTML = `
                <button class="btn btn-download btn-download-regular" id="downloadRegularBtn">
                    ⬇️ Download Image
                </button>
            `;
            
            // Add event listener for regular download button
            document.getElementById('downloadRegularBtn').addEventListener('click', () => {
                downloadImage(image.filename, 'regular', image.original_url || image.url);
            });
        }
    }

    function closeImageModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        currentModalData = null;
    }

    function downloadImage(filename, type, url) {
        console.log(`Download requested:`, { filename, type, url });
        
        if (!url) {
            alert(`Download URL not available for ${type} file.`);
            return;
        }
        
        try {
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank'; // Open in new tab as fallback
            
            // Set appropriate filename based on type
            let downloadFilename = filename;
            if (type === 'processed') {
                // For processed files, ensure .jpg extension
                downloadFilename = filename.replace(/\.[^/.]+$/, '.jpg');
            } else if (type === 'raw') {
                // For RAW files, try to get original extension from URL
                const urlParts = url.split('/');
                const lastPart = urlParts[urlParts.length - 1];
                if (lastPart.includes('.')) {
                    downloadFilename = lastPart;
                }
            }
            
            link.download = downloadFilename;
            
            console.log(`Attempting download:`, { url, downloadFilename });
            
            // Try to trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            console.log(`Download started: ${downloadFilename}`);
            
        } catch (error) {
            console.error('Download failed:', error);
            // Fallback: open in new tab
            console.log('Opening URL in new tab as fallback:', url);
            window.open(url, '_blank');
        }
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
