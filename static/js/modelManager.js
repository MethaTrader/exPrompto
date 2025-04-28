/**
 * modelManager.js - Module for managing LLM models
 * Handles model downloading and selection
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const downloadButtons = document.querySelectorAll('.download-model-btn');
    const useModelButtons = document.querySelectorAll('.use-model-btn');
    const downloadStatusModal = document.getElementById('downloadStatusModal');
    const downloadModelName = document.getElementById('downloadModelName');
    const downloadProgressBar = document.getElementById('downloadProgressBar');
    const downloadStatusText = document.getElementById('downloadStatusText');

    // Add event listeners to download buttons
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const repo = this.getAttribute('data-repo');
            const variant = this.getAttribute('data-variant');
            startModelDownload(repo, variant);
        });
    });

    // Add event listeners to use model buttons
    useModelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modelName = this.getAttribute('data-model');
            setActiveModel(modelName);
        });
    });

    /**
     * Start downloading a model
     * @param {string} repo - Repository name
     * @param {string} variant - Model variant
     */
    function startModelDownload(repo, variant) {
        // Show download modal
        downloadStatusModal.style.display = 'flex';
        downloadModelName.textContent = variant;
        downloadProgressBar.style.width = '0%';
        downloadStatusText.textContent = 'Инициализация загрузки...';

        // Make API request to download model
        fetch('/api/models/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                repo: repo,
                variant: variant
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Simulate download progress (actual progress isn't available via API)
                simulateDownloadProgress(variant);
            } else {
                downloadStatusText.textContent = `Ошибка: ${data.error}`;
                setTimeout(() => {
                    downloadStatusModal.style.display = 'none';
                }, 3000);
            }
        })
        .catch(error => {
            downloadStatusText.textContent = `Ошибка: ${error.message}`;
            setTimeout(() => {
                downloadStatusModal.style.display = 'none';
            }, 3000);
        });
    }

    /**
     * Simulate download progress with periodic checks
     * @param {string} variant - Model variant being downloaded
     */
    function simulateDownloadProgress(variant) {
        let progress = 0;
        let checkCount = 0;
        const interval = setInterval(() => {
            checkCount++;

            // Increment artificial progress
            progress += Math.floor(Math.random() * 5) + 1;

            // Don't go to 100% until we confirm it's actually complete
            progress = Math.min(progress, 95);
            downloadProgressBar.style.width = `${progress}%`;

            // Update status text
            downloadStatusText.textContent = `Загрузка... ${progress}%`;

            // Check if the model has actually been downloaded
            fetch('/api/models')
                .then(response => response.json())
                .then(data => {
                    const availableModels = data.available_models || [];

                    // Check if our model is in the available list
                    const modelDownloaded = availableModels.some(model => model.name === variant);

                    if (modelDownloaded) {
                        // Model is available, complete the download
                        clearInterval(interval);
                        downloadProgressBar.style.width = '100%';
                        downloadStatusText.textContent = 'Загрузка завершена!';

                        // Close modal and reload page
                        setTimeout(() => {
                            downloadStatusModal.style.display = 'none';
                            location.reload();
                        }, 2000);
                    }

                    // If we've been checking for too long, give up
                    if (checkCount > 120) { // 120 * 1 second = 2 minutes
                        clearInterval(interval);
                        downloadStatusText.textContent = 'Превышено время ожидания. Проверьте страницу моделей позже.';

                        setTimeout(() => {
                            downloadStatusModal.style.display = 'none';
                        }, 3000);
                    }
                })
                .catch(error => {
                    console.error('Error checking model status:', error);
                });
        }, 1000);
    }

    /**
     * Set a model as the active model
     * @param {string} modelName - Name of the model to activate
     */
    function setActiveModel(modelName) {
        // Find the button that was clicked
        const button = document.querySelector(`.use-model-btn[data-model="${modelName}"]`);

        // Disable all buttons temporarily
        useModelButtons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-play"></i> Использовать';
        });

        // Update the clicked button
        if (button) {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
        }

        // Send request to set active model
        fetch('/api/models/set-active', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: modelName
            })
        })
        .then(response => response.json())
        .then(data => {
            // Enable buttons again
            useModelButtons.forEach(btn => {
                btn.disabled = false;
            });

            if (data.success) {
                // Update button to show it's active
                if (button) {
                    button.innerHTML = '<i class="fas fa-check"></i> Активна';
                    button.classList.add('active-model');

                    // Reset other buttons
                    useModelButtons.forEach(btn => {
                        if (btn !== button) {
                            btn.innerHTML = '<i class="fas fa-play"></i> Использовать';
                            btn.classList.remove('active-model');
                        }
                    });
                }
            } else {
                // Reset button on error
                if (button) {
                    button.innerHTML = '<i class="fas fa-play"></i> Использовать';
                }

                alert(`Ошибка при активации модели: ${data.error}`);
            }
        })
        .catch(error => {
            // Enable buttons again
            useModelButtons.forEach(btn => {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Использовать';
            });

            console.error('Error setting active model:', error);
            alert(`Ошибка: ${error.message}`);
        });
    }
});