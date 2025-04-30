/**
 * fileUploader.js - Module for handling audio file uploads
 * Handles file selection, upload, and transcription
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing file uploader...');

    /**
     * Function to update transcription progress based on file duration
     * @param {number} duration - Duration of the file in seconds
     */
    function startProgressTimer(duration) {
        if (!duration || duration <= 0) return;

        const startTime = Date.now();
        const estimatedProcessingTime = Math.max(duration * 1.5, 10); // 1.5x file length, min 10 seconds
        const maxProgress = 95; // Maximum progress before completion

        // Cleanup any existing interval
        if (window.progressInterval) {
            clearInterval(window.progressInterval);
        }

        // Get stage and progress elements
        const transcribeStage = document.getElementById('stage-transcribe');
        const progressBar = document.getElementById('progressBar');
        const statusMessage = document.getElementById('statusMessage');

        // Show processing indicator
        if (transcribeStage) {
            transcribeStage.classList.add('stage-active');
            transcribeStage.querySelector('.stage-dot').classList.add('pulsing');
        }

        statusMessage.innerHTML = 'Идет распознавание речи... <div class="processing-spinner"></div>';

        window.progressInterval = setInterval(() => {
            const elapsed = (Date.now() - startTime) / 1000;
            const progressPercent = Math.min((elapsed / estimatedProcessingTime) * maxProgress, maxProgress);

            if (progressBar) {
                progressBar.style.width = `${Math.max(70, progressPercent)}%`;
            }

            // Add time estimate if it's taking a while
            if (elapsed > 10) {
                const remaining = Math.max(Math.round(estimatedProcessingTime - elapsed), 0);
                statusMessage.innerHTML = 
                    `Идет распознавание речи... <div class="processing-spinner"></div> ` +
                    `<span class="time-estimate">(примерно еще ${remaining} сек.)</span>`;
            }

            // If taking too long, adjust the message
            if (elapsed > estimatedProcessingTime * 1.2) {
                statusMessage.innerHTML = 
                    `Распознавание занимает больше времени, чем ожидалось... <div class="processing-spinner"></div> ` +
                    `<span class="time-estimate">(большие файлы могут обрабатываться дольше)</span>`;
            }
        }, 1000);
    }

    /**
     * Function to stop the progress timer
     */
    function stopProgressTimer() {
        if (window.progressInterval) {
            clearInterval(window.progressInterval);
            window.progressInterval = null;
        }

        // Remove processing indicators
        const stageDots = document.querySelectorAll('.stage-dot');
        stageDots.forEach(dot => dot.classList.remove('pulsing'));
    }

    // UI Elements
    const uploadArea = document.getElementById('uploadArea');
    const audioFileInput = document.getElementById('audioFileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const uploadButton = document.getElementById('uploadButton');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const resultText = document.getElementById('resultText');
    const statusMessage = document.getElementById('statusMessage');
    const copyTranscriptButton = document.getElementById('copyTranscriptButton');
    const copyTranscriptNotification = document.getElementById('copyTranscriptNotification');

    // Initialize notifications
    const notificationsInstance = new Notifications({
        copyNotification: copyTranscriptNotification
    });

    // Initialize clipboard manager
    const clipboardInstance = new ClipboardManager({
        copyButton: copyTranscriptButton,
        resultText: resultText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage
    });

    // Selected file
    let selectedFile = null;

    // Event listeners for file drop area
    uploadArea.addEventListener('click', () => {
        audioFileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    audioFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    uploadButton.addEventListener('click', () => {
        if (selectedFile) {
            uploadAndTranscribeFile(selectedFile);
        }
    });

    copyTranscriptButton.addEventListener('click', () => {
        clipboardInstance.copyToClipboard();
    });

    /**
     * Handles the file selection process
     * @param {File} file - The selected audio or video file
     */
    function handleFileSelection(file) {
        // Check if file is an audio or video file
        if (!file.type.startsWith('audio/') && !file.type.startsWith('video/')) {
            statusMessage.textContent = 'Пожалуйста, выберите аудио или видео файл';
            return;
        }

        selectedFile = file;

        // Update UI to show file info
        uploadArea.style.display = 'none';
        fileInfo.style.display = 'flex';
        fileName.textContent = file.name;

        // Format file size
        const fileSizeInMB = file.size / (1024 * 1024);
        fileSize.textContent = fileSizeInMB.toFixed(2) + ' MB';

        // Add file type icon
        const fileIcon = document.querySelector('.file-icon');
        if (fileIcon) {
            if (file.type.startsWith('video/')) {
                fileIcon.classList.remove('fa-file-audio');
                fileIcon.classList.add('fa-file-video');
            } else {
                fileIcon.classList.remove('fa-file-video');
                fileIcon.classList.add('fa-file-audio');
            }
        }

        // Reset result text
        resultText.textContent = 'Здесь появится распознанный текст...';
        copyTranscriptButton.disabled = true;
        statusMessage.textContent = `${file.type.startsWith('video/') ? 'Видео' : 'Аудио'} файл выбран и готов к загрузке`;
    }

    /**
     * Uploads and transcribes the selected audio file
     * @param {File} file - The audio file to upload and transcribe
     */
    function uploadAndTranscribeFile(file) {
        // Create form data
        const formData = new FormData();
        formData.append('audio', file);

        // Add language selection
        const languageSelect = document.getElementById('languageSelect');
        if (languageSelect) {
            formData.append('language', languageSelect.value);
        }

        // Update UI to show progress
        uploadButton.disabled = true;
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        resultText.textContent = 'Идет обработка файла...';
        statusMessage.textContent = 'Загрузка файла...';

        // Add processing stages visualization
        if (!document.querySelector('.processing-stages')) {
            const stagesContainer = document.createElement('div');
            stagesContainer.className = 'processing-stages';

            // Determine if it's a video file
            const isVideo = selectedFile.type.startsWith('video/');

            // Create stages
            const stages = [
                { id: 'upload', label: 'Загрузка' },
                ...(isVideo ? [{ id: 'extract', label: 'Извлечение аудио' }] : []),
                { id: 'transcribe', label: 'Распознавание' },
                { id: 'complete', label: 'Завершено' }
            ];

            stages.forEach((stage, index) => {
                const stageElem = document.createElement('div');
                stageElem.className = 'processing-stage' + (index === 0 ? ' stage-active' : '');
                stageElem.id = `stage-${stage.id}`;

                const dot = document.createElement('div');
                dot.className = 'stage-dot';

                const label = document.createElement('div');
                label.className = 'stage-label';
                label.textContent = stage.label;

                stageElem.appendChild(dot);
                stageElem.appendChild(label);
                stagesContainer.appendChild(stageElem);
            });

            progressContainer.appendChild(stagesContainer);
        }

        // Create and configure XHR request for upload progress tracking
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                // For large files, we show upload progress up to 70%
                // The remaining 30% is reserved for actual processing and transcription
                const adjustedPercent = Math.min(percentComplete * 0.7, 70);
                progressBar.style.width = adjustedPercent + '%';

                const isVideo = selectedFile.type.startsWith('video/');

                if (percentComplete < 100) {
                    statusMessage.textContent = `Загрузка ${isVideo ? 'видео' : 'аудио'} файла: ${Math.round(percentComplete)}%`;
                } else {
                    statusMessage.textContent = isVideo ?
                        'Файл загружен, извлечение аудио из видео...' :
                        'Файл загружен, начало распознавания...';

                    // Add video processing message
                    if (isVideo) {
                        const videoProcessingMsg = document.createElement('div');
                        videoProcessingMsg.innerHTML = 
                            `<div class="processing-note">Извлечение аудио из видео... <div class="processing-spinner"></div></div>`;
                        statusMessage.appendChild(videoProcessingMsg);
                    }

                    // Try to get duration from file metadata if available
                    let duration;

                    // For audio files, we can try to get duration
                    if (!isVideo && selectedFile) {
                        try {
                            const audio = new Audio();
                            audio.src = URL.createObjectURL(selectedFile);
                            audio.onloadedmetadata = function() {
                                duration = audio.duration;
                                if (duration) {
                                    startProgressTimer(duration);
                                }
                                URL.revokeObjectURL(audio.src);
                            };
                        } catch (e) {
                            console.warn("Could not get audio duration:", e);
                        }
                    } else {
                        // For video files, we'll start the timer with an estimated duration
                        // based on file size (rough estimate: 1MB ≈ 10 seconds of audio)
                        const estimatedDuration = selectedFile ? (selectedFile.size / (1024 * 1024)) * 10 : 30;
                        startProgressTimer(estimatedDuration);
                    }

                    // Update processing stages
                    const uploadStage = document.getElementById('stage-upload');
                    if (uploadStage) {
                        uploadStage.classList.remove('stage-active');
                        uploadStage.classList.add('stage-complete');

                        if (isVideo) {
                            const extractStage = document.getElementById('stage-extract');
                            if (extractStage) {
                                extractStage.classList.add('stage-active');
                            }
                        } else {
                            const transcribeStage = document.getElementById('stage-transcribe');
                            if (transcribeStage) {
                                transcribeStage.classList.add('stage-active');
                            }
                        }
                    }
                }
            }
        });

        xhr.addEventListener('load', function() {
            // Stop the progress timer
            stopProgressTimer();

            if (this.status >= 200 && this.status < 300) {
                try {
                    const response = JSON.parse(this.responseText);

                    if (response.transcription) {
                        // Success - show transcription
                        resultText.textContent = response.transcription;

                        // Show media metadata if available
                        let statusText = 'Распознавание завершено успешно!';
                        if (response.media_type && response.duration) {
                            statusText += ` (${response.media_type === 'video' ? 'Видео' : 'Аудио'}, длительность: ${response.duration})`;
                        }
                        statusMessage.textContent = statusText;

                        // Update processing stages to show completion
                        const stages = document.querySelectorAll('.processing-stage');
                        stages.forEach(stage => {
                            stage.classList.remove('stage-active');
                            stage.classList.add('stage-complete');
                        });

                        const completeStage = document.getElementById('stage-complete');
                        if (completeStage) {
                            completeStage.classList.add('stage-active');
                        }

                        copyTranscriptButton.disabled = false;

                        // Add highlight effect
                        resultText.style.animation = 'highlight 1s';
                        setTimeout(() => {
                            resultText.style.animation = '';
                        }, 1000);

                        // Add media metadata display
                        if (response.media_type || response.duration) {
                            const mediaMetadata = document.createElement('div');
                            mediaMetadata.className = 'media-metadata';
                            mediaMetadata.innerHTML = `
                                <span class="media-type">${response.media_type === 'video' ? '<i class="fas fa-film"></i> Видео' : '<i class="fas fa-music"></i> Аудио'}</span>
                                ${response.duration ? `<span class="media-duration"><i class="fas fa-clock"></i> ${response.duration}</span>` : ''}
                            `;

                            // Add metadata to result card
                            const resultContent = document.querySelector('.result-content');
                            const existingMetadata = document.querySelector('.media-metadata');

                            if (existingMetadata) {
                                resultContent.removeChild(existingMetadata);
                            }

                            resultContent.insertBefore(mediaMetadata, resultText);
                        }

                    } else if (response.error) {
                        resultText.textContent = `Ошибка: ${response.error}`;
                        statusMessage.textContent = 'Произошла ошибка при распознавании';
                    }
                } catch (error) {
                    resultText.textContent = 'Ошибка при обработке ответа сервера';
                    statusMessage.textContent = `Ошибка: ${error.message}`;
                }
            } else {
                // Error response
                resultText.textContent = 'Ошибка при загрузке или распознавании файла';
                statusMessage.textContent = `Код ошибки: ${this.status}`;
            }

            // Reset UI
            progressBar.style.width = '100%';
            uploadButton.disabled = false;
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 1000);
        });

        xhr.addEventListener('error', function() {
            stopProgressTimer();
            resultText.textContent = 'Произошла ошибка при отправке файла';
            statusMessage.textContent = 'Ошибка соединения с сервером';
            uploadButton.disabled = false;
            progressContainer.style.display = 'none';
        });

        xhr.open('POST', '/transcribe');
        xhr.send(formData);
    }

    // Function to reset the form and allow new file upload
    window.resetUploadForm = function() {
        selectedFile = null;
        audioFileInput.value = '';
        uploadArea.style.display = 'flex';
        fileInfo.style.display = 'none';
        progressContainer.style.display = 'none';
        statusMessage.textContent = '';
    };

    // Add a cancel/reset button to the UI
    const cancelButton = document.createElement('button');
    cancelButton.className = 'cancel-btn';
    cancelButton.innerHTML = '<i class="fas fa-times"></i>';
    cancelButton.title = 'Отменить и выбрать другой файл';
    cancelButton.addEventListener('click', (e) => {
        e.preventDefault();
        window.resetUploadForm();
    });

    fileInfo.appendChild(cancelButton);
});
