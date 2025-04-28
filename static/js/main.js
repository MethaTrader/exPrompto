/**
 * main.js - Main application module for exPrompto
 * Initializes and connects all components
 */

document.addEventListener('DOMContentLoaded', function() {
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
    const audioVisualizerInstance = new AudioVisualizer(visualizer);
    audioVisualizerInstance.setupCanvas();
    audioVisualizerInstance.drawInitialVisualizer();

    // Initialize notifications
    const notificationsInstance = new Notifications({
        copyNotification: copyTranscriptNotification,
        pdfNotification: pdfNotification,
        txtNotification: txtNotification
    });

    // Initialize clipboard manager for transcription results
    const clipboardTranscriptInstance = new ClipboardManager({
        copyButton: copyTranscriptButton,
        resultText: resultText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage
    });

    // Initialize clipboard manager for structured document
    const clipboardDocumentInstance = new ClipboardManager({
        copyButton: copyDocumentButton,
        resultText: structuredDocumentText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage,
        notificationType: 'document'
    });

    // Initialize audio recorder
    // Example from main.js
    const audioRecorderInstance = new AudioRecorder({
        recordButton: recordButton,
        progressBar: progressBar,
        currentTimeElement: currentTimeElement,
        resultText: resultText,
        statusMessage: statusMessage,
        copyButton: copyTranscriptButton,
        processButton: processTextButton,
        // Make sure you're not trying to pass exportPdfButton or exportTxtButton if they don't exist
        // in this context - they might belong to a different card
        audioVisualizerInstance: audioVisualizerInstance,
        notificationsInstance: notificationsInstance,
        maxRecordingTime: MAX_RECORDING_TIME
    });

    // Initialize document processor
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
        if (recording) {
            audioRecorderInstance.stopRecording();
            recording = false;
        } else {
            audioRecorderInstance.startRecording().then(isRecording => {
                recording = isRecording;
            });
        }
    });

    // Event Listeners - Copying
    copyTranscriptButton.addEventListener('click', () => {
        clipboardTranscriptInstance.copyToClipboard();
    });

    copyDocumentButton.addEventListener('click', () => {
        clipboardDocumentInstance.copyToClipboard();
    });

    // Event Listeners - Exporting
    exportPdfButton.addEventListener('click', () => {
        const text = structuredDocumentText.innerHTML;
        if (!text || text === '') return;

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
            } else {
                statusMessage.textContent = 'Ошибка при создании PDF файла';
            }
        })
        .catch(error => {
            statusMessage.textContent = `Ошибка: ${error.message}`;
            console.error('Error exporting to PDF:', error);
        });
    });

    exportTxtButton.addEventListener('click', () => {
        const text = structuredDocumentText.textContent;
        if (!text || text === '') return;

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
            } else {
                statusMessage.textContent = 'Ошибка при создании TXT файла';
            }
        })
        .catch(error => {
            statusMessage.textContent = `Ошибка: ${error.message}`;
            console.error('Error exporting to TXT:', error);
        });
    });

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
    });
});