/**
 * documentProcessor.js - Module for text processing with LLM
 * Handles structuring raw text into formal documents
 */

class DocumentProcessor {
    /**
     * Creates a document processor instance
     * @param {Object} config - Configuration object
     * @param {HTMLElement} config.resultText - Element containing the raw text
     * @param {HTMLElement} config.processTextButton - Button to initiate processing
     * @param {HTMLElement} config.structuredDocumentCard - Card element for the structured document
     * @param {HTMLElement} config.structuredDocumentText - Element to display the structured document
     * @param {HTMLElement} config.processingModal - Modal for selecting templates
     * @param {HTMLElement} config.processingStatusModal - Modal for showing processing status
     * @param {HTMLElement} config.templateSelect - Select element for templates
     * @param {HTMLElement} config.templateDescription - Element for template description
     * @param {HTMLElement} config.startProcessingButton - Button to start processing
     * @param {HTMLElement} config.cancelProcessingButton - Button to cancel
     * @param {HTMLElement} config.processingStatusText - Element for status text
     * @param {HTMLElement} config.processingProgressBar - Progress bar for processing
     * @param {Notifications} config.notificationsInstance - Notifications manager
     */
    constructor(config) {
        this.resultText = config.resultText;
        this.processTextButton = config.processTextButton;
        this.structuredDocumentCard = config.structuredDocumentCard;
        this.structuredDocumentText = config.structuredDocumentText;
        this.processingModal = config.processingModal;
        this.processingStatusModal = config.processingStatusModal;
        this.templateSelect = config.templateSelect;
        this.templateDescription = config.templateDescription;
        this.startProcessingButton = config.startProcessingButton;
        this.cancelProcessingButton = config.cancelProcessingButton;
        this.processingStatusText = config.processingStatusText;
        this.processingProgressBar = config.processingProgressBar;
        this.notifications = config.notificationsInstance;

        // Additional properties
        this.currentJobId = null;
        this.pollingInterval = null;
        this.templateDescriptions = {};
        this.pollingCount = 0;
        this.maxPollingAttempts = 120; // 2 minutes at 1 second intervals
        this.pollingDelay = 1000; // 1 second between polls

        // Initialize
        this.setupEventListeners();
        this.loadTemplateDescriptions();
    }

    /**
     * Setup event listeners for the document processor
     */
    setupEventListeners() {
        // Process text button
        if (this.processTextButton) {
            console.log('Setting up event listener for process text button');
            this.processTextButton.addEventListener('click', () => {
                console.log('Process text button clicked');
                this.openProcessingModal();
            });
        } else {
            console.error('Process text button not found');
        }

        // Template selection change
        if (this.templateSelect) {
            this.templateSelect.addEventListener('change', () => {
                this.updateTemplateDescription();
            });
        }

        // Start processing button
        this.startProcessingButton.addEventListener('click', () => {
            this.startProcessing();
        });

        // Cancel processing button
        this.cancelProcessingButton.addEventListener('click', () => {
            this.closeProcessingModal();
        });
    }

    /**
     * Load template descriptions from the server
     */
    loadTemplateDescriptions() {
        fetch('/api/templates')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch templates: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Templates loaded:', data);
                const templates = data.templates || [];
                templates.forEach(template => {
                    this.templateDescriptions[template.id] = template.description;
                });
                this.updateTemplateDescription();
            })
            .catch(error => {
                console.error('Error loading templates:', error);
            });
    }

    /**
     * Update the template description based on selected template
     */
    updateTemplateDescription() {
        if (!this.templateSelect || !this.templateDescription) return;

        const selectedTemplate = this.templateSelect.value;
        const description = this.templateDescriptions[selectedTemplate] || 'Нет описания';
        this.templateDescription.textContent = description;
    }

    /**
     * Open the processing modal
     */
    openProcessingModal() {
        if (!this.hasValidText()) {
            console.warn('No valid text to process');
            return;
        }

        console.log('Opening processing modal');
        this.processingModal.style.display = 'flex';
        this.updateTemplateDescription();
    }

    /**
     * Close the processing modal
     */
    closeProcessingModal() {
        this.processingModal.style.display = 'none';
    }

    /**
     * Open the processing status modal
     */
    openProcessingStatusModal() {
        this.processingStatusModal.style.display = 'flex';
        this.processingProgressBar.style.width = '0%';
        this.processingStatusText.textContent = 'Инициализация обработки...';
    }

    /**
     * Close the processing status modal
     */
    closeProcessingStatusModal() {
        this.processingStatusModal.style.display = 'none';
        this.clearPolling();
    }

    /**
     * Check if there is valid text to process
     * @returns {boolean} True if there is valid text to process
     */
    hasValidText() {
        if (!this.resultText) {
            console.error('Result text element not found');
            return false;
        }

        const text = this.resultText.textContent.trim();
        console.log('Checking if text is valid:', text ? 'Text is present' : 'No text');

        return text &&
               text !== 'Здесь появится распознанный текст...' &&
               !text.startsWith('Ошибка:') &&
               !text.startsWith('Говорите...') &&
               !text.startsWith('Обработка записи...');
    }

    /**
     * Start processing the text
     */
    startProcessing() {
        if (!this.hasValidText()) {
            console.warn('No valid text to process');
            return;
        }

        const text = this.resultText.textContent.trim();
        const templateType = this.templateSelect ? this.templateSelect.value : 'technical_specification';

        console.log(`Starting text processing with template: ${templateType}`);

        // Reset polling count
        this.pollingCount = 0;

        // Close the processing modal and open the status modal
        this.closeProcessingModal();
        this.openProcessingStatusModal();

        // Send the text for processing
        fetch('/process-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                template_type: templateType
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.job_id) {
                console.log(`Processing job started with ID: ${data.job_id}`);
                this.currentJobId = data.job_id;
                this.startPollingJobStatus();
            } else {
                throw new Error(data.error || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error('Error starting text processing:', error);
            this.processingStatusText.textContent = `Ошибка: ${error.message}`;
            setTimeout(() => {
                this.closeProcessingStatusModal();
            }, 3000);
        });
    }

    /**
     * Start polling for job status
     */
    startPollingJobStatus() {
        if (!this.currentJobId) {
            console.error('No job ID to poll');
            return;
        }

        // Set initial progress
        this.processingProgressBar.style.width = '10%';
        this.processingStatusText.textContent = 'Обработка текста...';

        let progress = 10;

        // Clear any existing interval
        this.clearPolling();

        console.log(`Starting polling for job: ${this.currentJobId}`);

        // Define a function to check the job status
        const checkJobStatus = () => {
            this.pollingCount++;

            // Increment artificial progress (up to 90%)
            // Real completion will set it to 100%
            if (progress < 90) {
                progress += Math.floor(Math.random() * 3) + 1;
                progress = Math.min(progress, 90);
                this.processingProgressBar.style.width = `${progress}%`;
            }

            // Log polling attempt
            console.log(`Polling attempt ${this.pollingCount} for job: ${this.currentJobId}`);

            // Check job status
            fetch(`/job-status/${this.currentJobId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(`Job status: ${data.status}`, data);

                    if (data.status === 'completed') {
                        // Job completed successfully
                        this.processingProgressBar.style.width = '100%';
                        this.processingStatusText.textContent = 'Обработка завершена!';

                        // Clear polling and display results
                        clearTimeout(this.pollingTimeout);
                        this.pollingTimeout = null;

                        setTimeout(() => {
                            this.closeProcessingStatusModal();
                            this.displayProcessedDocument(data.result.text);
                        }, 1000);
                    } else if (data.status === 'failed') {
                        // Job failed
                        this.processingStatusText.textContent = `Ошибка: ${data.result?.error || 'Обработка не удалась'}`;
                        clearTimeout(this.pollingTimeout);
                        this.pollingTimeout = null;

                        // Close modal after a delay
                        setTimeout(() => {
                            this.closeProcessingStatusModal();
                        }, 3000);
                    } else if (data.status === 'not_found') {
                        // First few attempts might return not_found while the job is being created
                        if (this.pollingCount < 5) {
                            console.log(`Job not found yet, retry ${this.pollingCount}/5`);
                            this.pollingTimeout = setTimeout(checkJobStatus, this.pollingDelay);
                        } else {
                            // Job not found after several attempts
                            this.processingStatusText.textContent = 'Задача не найдена';
                            clearTimeout(this.pollingTimeout);
                            this.pollingTimeout = null;

                            // Close modal after a delay
                            setTimeout(() => {
                                this.closeProcessingStatusModal();
                            }, 3000);
                        }
                    } else if (data.status === 'processing' || data.status === 'queued') {
                        // Job is still being processed, continue polling
                        this.processingStatusText.textContent = data.status === 'processing' ?
                            'Обработка текста...' : 'В очереди на обработку...';

                        // Continue polling
                        if (this.pollingCount < this.maxPollingAttempts) {
                            this.pollingTimeout = setTimeout(checkJobStatus, this.pollingDelay);
                        } else {
                            // Exceeded max attempts
                            this.processingStatusText.textContent = 'Превышено время ожидания';
                            clearTimeout(this.pollingTimeout);
                            this.pollingTimeout = null;

                            setTimeout(() => {
                                this.closeProcessingStatusModal();
                            }, 3000);
                        }
                    } else {
                        // Unknown status
                        console.warn(`Unknown job status: ${data.status}`);

                        // Continue polling for a while
                        if (this.pollingCount < this.maxPollingAttempts) {
                            this.pollingTimeout = setTimeout(checkJobStatus, this.pollingDelay);
                        } else {
                            // Exceeded max attempts
                            this.processingStatusText.textContent = 'Превышено время ожидания';
                            clearTimeout(this.pollingTimeout);
                            this.pollingTimeout = null;

                            setTimeout(() => {
                                this.closeProcessingStatusModal();
                            }, 3000);
                        }
                    }
                })
                .catch(error => {
                    console.error('Error checking job status:', error);
                    this.processingStatusText.textContent = `Ошибка: ${error.message}`;

                    // Continue polling for a few more attempts if there's a network error
                    if (this.pollingCount < 10) {
                        this.pollingTimeout = setTimeout(checkJobStatus, this.pollingDelay);
                    } else {
                        clearTimeout(this.pollingTimeout);
                        this.pollingTimeout = null;

                        setTimeout(() => {
                            this.closeProcessingStatusModal();
                        }, 3000);
                    }
                });
        };

        // Start the first check
        checkJobStatus();
    }

    /**
     * Clear polling interval
     */
    clearPolling() {
        if (this.pollingTimeout) {
            clearTimeout(this.pollingTimeout);
            this.pollingTimeout = null;
            console.log('Polling timeout cleared');
        }
    }

    /**
     * Display the processed document
     * @param {string} text - Processed document text
     */
    displayProcessedDocument(text) {
        if (!text) {
            console.warn('No text to display');
            return;
        }

        console.log('Displaying processed document');

        // Show the structured document card
        this.structuredDocumentCard.style.display = 'block';

        // Scroll to it
        this.structuredDocumentCard.scrollIntoView({ behavior: 'smooth' });

        // Set the text (convert markdown to HTML for better display)
        this.structuredDocumentText.innerHTML = this.markdownToHtml(text);
    }

    /**
     * Simple markdown to HTML converter
     * @param {string} markdown - Markdown text
     * @returns {string} HTML
     */
    markdownToHtml(markdown) {
        if (!markdown) return '';

        // This is a simple converter for basic markdown
        let html = markdown
            // Headers
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^#### (.*$)/gm, '<h4>$1</h4>')

            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')

            // Lists
            .replace(/^\s*\n\* (.*)/gm, '<ul>\n<li>$1</li>')
            .replace(/^\* (.*)/gm, '<li>$1</li>')
            .replace(/^\s*\n\d+\. (.*)/gm, '<ol>\n<li>$1</li>')
            .replace(/^\d+\. (.*)/gm, '<li>$1</li>')

            // Paragraphs
            .replace(/^\s*\n([^\n]+)\n/gm, '<p>$1</p>')

            // Line breaks
            .replace(/\n/g, '<br>');

        return html;
    }
}