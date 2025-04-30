/**
 * main.js - Main application module for exPrompto
 * Initializes and connects all components
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing exPrompto application...');

    // UI Elements - Speech Recognition
    const recordButton = document.getElementById('recordButton');
    const progressBar = document.getElementById('progressBar');
    const visualizer = document.getElementById('visualizer');
    const currentTimeElement = document.getElementById('currentTime');
    const resultText = document.getElementById('resultText');
    const statusMessage = document.getElementById('statusMessage');
    const copyTranscriptButton = document.getElementById('copyTranscriptButton');
    const processTextButton = document.getElementById('processTextButton');

    // UI Elements - Document Processing
    const structuredDocumentCard = document.getElementById('structuredDocumentCard');
    const structuredDocumentText = document.getElementById('structuredDocumentText');
    const copyDocumentButton = document.getElementById('copyDocumentButton');
    const exportPdfButton = document.getElementById('exportPdfButton');
    const exportTxtButton = document.getElementById('exportTxtButton');
    const processingModal = document.getElementById('processingModal');
    const processingStatusModal = document.getElementById('processingStatusModal');
    const templateSelect = document.getElementById('templateSelect');
    const templateDescription = document.getElementById('templateDescription');
    const startProcessingButton = document.getElementById('startProcessingButton');
    const cancelProcessingButton = document.getElementById('cancelProcessingButton');
    const processingStatusText = document.getElementById('processingStatusText');
    const processingProgressBar = document.getElementById('processingProgressBar');

    // UI Elements - Notifications
    const copyTranscriptNotification = document.getElementById('copyTranscriptNotification');
    const copyDocumentNotification = document.getElementById('copyDocumentNotification');
    const pdfNotification = document.getElementById('pdfNotification');
    const txtNotification = document.getElementById('txtNotification');

    // Validate UI elements
    const validateElements = () => {
        const elements = {
            'recordButton': recordButton,
            'progressBar': progressBar,
            'visualizer': visualizer,
            'currentTimeElement': currentTimeElement,
            'resultText': resultText,
            'statusMessage': statusMessage,
            'copyTranscriptButton': copyTranscriptButton,
            'processTextButton': processTextButton
        };

        let missing = [];
        for (const [name, element] of Object.entries(elements)) {
            if (!element) {
                missing.push(name);
                console.error(`Element not found: ${name}`);
            }
        }

        if (missing.length > 0) {
            console.error(`Missing UI elements: ${missing.join(', ')}`);
            return false;
        }
        return true;
    };

    // Validate required UI elements
    if (!validateElements()) {
        statusMessage.textContent = 'Ошибка инициализации приложения: не найдены элементы интерфейса';
        return;
    }

    // Variables for recording
    let mediaRecorder;
    let audioContext;
    let analyser;
    let microphone;
    let audioChunks = [];
    let recording = false;
    let animationFrame;
    let timerInterval;
    let startTime;
    const MAX_RECORDING_TIME = 30000; // 30 seconds

    // Initialize audio visualizer
    console.log('Initializing audio visualizer...');
    const audioVisualizerInstance = new AudioVisualizer(visualizer);
    audioVisualizerInstance.setupCanvas();
    audioVisualizerInstance.drawInitialVisualizer();

    // Initialize notifications
    console.log('Initializing notifications...');
    const notificationsInstance = new Notifications({
        copyNotification: copyTranscriptNotification,
        pdfNotification: pdfNotification,
        txtNotification: txtNotification
    });

    // Initialize clipboard manager for transcription results
    console.log('Initializing transcript clipboard manager...');
    const clipboardTranscriptInstance = new ClipboardManager({
        copyButton: copyTranscriptButton,
        resultText: resultText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage
    });

    // Initialize clipboard manager for structured document
    console.log('Initializing document clipboard manager...');
    const clipboardDocumentInstance = new ClipboardManager({
        copyButton: copyDocumentButton,
        resultText: structuredDocumentText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage,
        notificationType: 'document'
    });

    // Initialize audio recorder
    console.log('Initializing audio recorder...');
    const audioRecorderInstance = new AudioRecorder({
        recordButton: recordButton,
        progressBar: progressBar,
        currentTimeElement: currentTimeElement,
        resultText: resultText,
        statusMessage: statusMessage,
        copyButton: copyTranscriptButton,
        processButton: processTextButton, // Make sure this is properly passed
        exportPdfButton: exportPdfButton,
        exportTxtButton: exportTxtButton,
        audioVisualizerInstance: audioVisualizerInstance,
        notificationsInstance: notificationsInstance,
        maxRecordingTime: MAX_RECORDING_TIME
    });

    // Initialize document processor
    console.log('Initializing document processor...');
    const documentProcessorInstance = new DocumentProcessor({
        resultText: resultText,
        processTextButton: processTextButton,
        structuredDocumentCard: structuredDocumentCard,
        structuredDocumentText: structuredDocumentText,
        processingModal: processingModal,
        processingStatusModal: processingStatusModal,
        templateSelect: templateSelect,
        templateDescription: templateDescription,
        startProcessingButton: startProcessingButton,
        cancelProcessingButton: cancelProcessingButton,
        processingStatusText: processingStatusText,
        processingProgressBar: processingProgressBar,
        notificationsInstance: new Notifications({
            copyNotification: copyDocumentNotification,
            pdfNotification: pdfNotification,
            txtNotification: txtNotification
        })
    });

    // Event Listeners - Recording
    recordButton.addEventListener('click', function() {
        console.log('Record button clicked, current state:', recording ? 'recording' : 'not recording');
        if (recording) {
            audioRecorderInstance.stopRecording();
            recording = false;
        } else {
            audioRecorderInstance.startRecording().then(isRecording => {
                recording = isRecording;
                console.log('Recording started:', isRecording);
            });
        }
    });

    // Event Listeners - Copying
    copyTranscriptButton.addEventListener('click', () => {
        console.log('Copy transcript button clicked');
        clipboardTranscriptInstance.copyToClipboard();
    });

    copyDocumentButton.addEventListener('click', () => {
        console.log('Copy document button clicked');
        clipboardDocumentInstance.copyToClipboard();
    });

    // Event Listeners - Exporting
    exportPdfButton.addEventListener('click', () => {
        console.log('Export PDF button clicked');
        const text = structuredDocumentText.innerHTML;
        if (!text || text === '') {
            console.warn('No text to export as PDF');
            return;
        }

        // Send text to server for PDF generation
        fetch('/generate-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: structuredDocumentText.textContent })
        })
        .then(response => {
            if (response.ok) {
                // If PDF creation was successful, download it
                window.location.href = '/download-pdf';
                notificationsInstance.showNotification('pdfNotification');
                console.log('PDF generated successfully');
            } else {
                statusMessage.textContent = 'Ошибка при создании PDF файла';
                console.error('Error response from server when generating PDF');
            }
        })
        .catch(error => {
            statusMessage.textContent = `Ошибка: ${error.message}`;
            console.error('Error exporting to PDF:', error);
        });
    });

    exportTxtButton.addEventListener('click', () => {
        console.log('Export TXT button clicked');
        const text = structuredDocumentText.textContent;
        if (!text || text === '') {
            console.warn('No text to export as TXT');
            return;
        }

        // Send text to server for TXT generation
        fetch('/generate-txt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => {
            if (response.ok) {
                // If TXT creation was successful, download it
                window.location.href = '/download-txt';
                notificationsInstance.showNotification('txtNotification');
                console.log('TXT generated successfully');
            } else {
                statusMessage.textContent = 'Ошибка при создании TXT файла';
                console.error('Error response from server when generating TXT');
            }
        })
        .catch(error => {
            statusMessage.textContent = `Ошибка: ${error.message}`;
            console.error('Error exporting to TXT:', error);
        });
    });

    // Additional event listeners for structuring text
    if (processTextButton) {
        console.log('Adding event listener for process text button');
        processTextButton.addEventListener('click', () => {
            console.log('Process text button clicked from main.js');
            documentProcessorInstance.openProcessingModal();
        });
    } else {
        console.error('Process text button not found');
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        audioVisualizerInstance.setupCanvas();
        if (!recording) {
            audioVisualizerInstance.drawInitialVisualizer();
        }
    });

    // Close modals when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === processingModal) {
            processingModal.style.display = 'none';
        }
        if (event.target === processingStatusModal) {
            processingStatusModal.style.display = 'none';
        }
    });

    console.log('exPrompto application initialized successfully');

    // Get test elements
    const testLlmButton = document.getElementById('testLlmButton');
    const testLlmResult = document.getElementById('testLlmResult');

    if (testLlmButton) {
        testLlmButton.addEventListener('click', function() {
            // Show loading state
            testLlmButton.disabled = true;
            testLlmButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Выполняется тест...';
            testLlmResult.style.display = 'block';
            testLlmResult.textContent = 'Тестирование LLM, пожалуйста, подождите...';

            // Call the test endpoint
            fetch('/test-llm')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('LLM test result:', data);

                    if (data.status === 'success') {
                        testLlmResult.innerHTML = `
                            <div style="color: #2ecc71;">✓ Тест успешно выполнен!</div>
                            <div>Время обработки: ${data.processing_time.toFixed(2)} секунд</div>
                            <div>Длина результата: ${data.full_length} символов</div>
                            <div style="margin-top: 10px;"><strong>Предпросмотр:</strong></div>
                            <div style="margin-top: 5px; padding: 10px; background: rgba(46, 204, 113, 0.1); border-left: 3px solid #2ecc71;">${data.preview}</div>
                        `;
                    } else {
                        testLlmResult.innerHTML = `
                            <div style="color: #e74c3c;">✗ Ошибка тестирования</div>
                            <div>${data.message}</div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error testing LLM:', error);
                    testLlmResult.innerHTML = `
                        <div style="color: #e74c3c;">✗ Ошибка при выполнении теста</div>
                        <div>${error.message}</div>
                    `;
                })
                .finally(() => {
                    // Reset button
                    testLlmButton.disabled = false;
                    testLlmButton.innerHTML = '<i class="fas fa-vial"></i> Запустить тест LLM';
                });
        });
    }


});