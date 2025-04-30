/**
 * main.js - Main application module for exPrompto
 * Initializes and connects audio recording and transcription components
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

    // UI Elements - Prompt Generation
    const promptText = document.getElementById('promptText');
    const promptStatusMessage = document.getElementById('promptStatusMessage');
    const copyPromptButton = document.getElementById('copyPromptButton');

    // UI Elements - Notifications
    const copyTranscriptNotification = document.getElementById('copyTranscriptNotification');
    const copyPromptNotification = document.getElementById('copyPromptNotification');

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
            'promptText': promptText,
            'promptStatusMessage': promptStatusMessage,
            'copyPromptButton': copyPromptButton
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
    const MAX_RECORDING_TIME = 30000; // 30 seconds
    let recording = false;

    // Initialize audio visualizer
    console.log('Initializing audio visualizer...');
    const audioVisualizerInstance = new AudioVisualizer(visualizer);
    audioVisualizerInstance.setupCanvas();
    audioVisualizerInstance.drawInitialVisualizer();

    // Initialize notifications
    console.log('Initializing notifications...');
    const notificationsInstance = new Notifications({
        copyNotification: copyTranscriptNotification,
        pdfNotification: copyPromptNotification,
        txtNotification: null
    });

    // Initialize clipboard manager for transcription results
    console.log('Initializing transcript clipboard manager...');
    const clipboardTranscriptInstance = new ClipboardManager({
        copyButton: copyTranscriptButton,
        resultText: resultText,
        notificationsInstance: notificationsInstance,
        statusMessage: statusMessage
    });

    // Initialize clipboard manager for prompt
    console.log('Initializing prompt clipboard manager...');
    const clipboardPromptInstance = new ClipboardManager({
        copyButton: copyPromptButton,
        resultText: promptText,
        notificationsInstance: notificationsInstance,
        statusMessage: promptStatusMessage
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
        promptText: promptText,
        promptStatusMessage: promptStatusMessage,
        copyPromptButton: copyPromptButton,
        audioVisualizerInstance: audioVisualizerInstance,
        notificationsInstance: notificationsInstance,
        maxRecordingTime: MAX_RECORDING_TIME
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

    // Event Listeners - Copying Transcription
    copyTranscriptButton.addEventListener('click', () => {
        console.log('Copy transcript button clicked');
        clipboardTranscriptInstance.copyToClipboard();
    });

    // Event Listeners - Copying Prompt
    copyPromptButton.addEventListener('click', () => {
        console.log('Copy prompt button clicked');
        clipboardPromptInstance.copyToClipboard();
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        audioVisualizerInstance.setupCanvas();
        if (!recording) {
            audioVisualizerInstance.drawInitialVisualizer();
        }
    });

    console.log('exPrompto application initialized successfully');
});