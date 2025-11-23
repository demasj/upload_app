// Upload component JavaScript
const apiBase = "{{API_BASE}}";
const chunkSize = {{CHUNK_SIZE}};

let uploadId = null;
let file = null;
let isUploading = false;

document.getElementById('fileInput').addEventListener('change', function(e) {
    file = e.target.files[0];
    if (file) {
        document.getElementById('statusText').innerText = `Selected: ${file.name} (${file.size.toLocaleString()} bytes)`;
        document.getElementById('statusText').style.color = '#666';
    }
});

document.getElementById('uploadButton').addEventListener('click', async function() {
    if (!file) {
        alert('Please select a file first');
        return;
    }

    if (isUploading) {
        alert('Upload already in progress');
        return;
    }

    isUploading = true;
    document.getElementById('uploadButton').disabled = true;
    document.getElementById('uploadButton').innerText = 'Uploading...';
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('statusText').innerText = 'Initializing upload...';
    document.getElementById('statusText').style.color = '#666';

    try {
        // Initialize upload
        const initResponse = await fetch(`${apiBase}/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: file.name,
                file_size: file.size
            })
        });

        if (!initResponse.ok) {
            const errorText = await initResponse.text();
            throw new Error(`Init failed: ${initResponse.status} - ${errorText}`);
        }

        const initData = await initResponse.json();
        uploadId = initData.upload_id;
        const actualChunkSize = initData.chunk_size;

        document.getElementById('statusText').innerText = 'Uploading...';

        // Upload chunks
        const totalChunks = Math.ceil(file.size / actualChunkSize);
        let uploadedChunks = 0;
        const startTime = Date.now();
        let totalBytesUploaded = 0;

        for (let i = 0; i < totalChunks; i++) {
            const start = i * actualChunkSize;
            const end = Math.min(start + actualChunkSize, file.size);
            const chunk = file.slice(start, end);

            const formData = new FormData();
            formData.append('upload_id', uploadId);
            formData.append('chunk_index', i);
            formData.append('file', chunk);

            const chunkResponse = await fetch(`${apiBase}/chunk`, {
                method: 'POST',
                body: formData
            });

            if (!chunkResponse.ok) {
                const errorText = await chunkResponse.text();
                throw new Error(`Chunk upload failed: ${chunkResponse.status} - ${errorText}`);
            }

            uploadedChunks++;
            totalBytesUploaded += chunk.size;

            const progress = Math.round((uploadedChunks / totalChunks) * 100);
            const elapsedTime = (Date.now() - startTime) / 1000; // seconds
            const speedBps = totalBytesUploaded / elapsedTime;

            let speedText = '';
            if (speedBps > 1024 * 1024) {
                speedText = `${(speedBps / (1024 * 1024)).toFixed(1)} MB/s`;
            } else if (speedBps > 1024) {
                speedText = `${(speedBps / 1024).toFixed(1)} KB/s`;
            } else {
                speedText = `${speedBps.toFixed(0)} B/s`;
            }

            document.getElementById('progressBar').value = progress;
            document.getElementById('progressText').innerText = `${progress}% (${speedText})`;
            // Hide chunk progress during upload
            // document.getElementById('statusText').innerText = `Uploaded chunk ${uploadedChunks}/${totalChunks}`;
        }

        // Complete upload
        const completeResponse = await fetch(`${apiBase}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ upload_id: uploadId })
        });

        if (!completeResponse.ok) {
            const errorText = await completeResponse.text();
            throw new Error(`Complete failed: ${completeResponse.status} - ${errorText}`);
        }

        const completeData = await completeResponse.json();
        document.getElementById('statusText').innerText = 'Upload completed successfully!';
        document.getElementById('statusText').style.color = '#28a745';
        alert('Upload completed successfully!');

    } catch (error) {
        document.getElementById('statusText').innerText = `Error: ${error.message}`;
        document.getElementById('statusText').style.color = '#dc3545';
        alert(`Upload failed: ${error.message}`);
        console.error('Upload error:', error);
    } finally {
        isUploading = false;
        document.getElementById('uploadButton').disabled = false;
        document.getElementById('uploadButton').innerText = 'Start Upload';
    }
});