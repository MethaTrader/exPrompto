/**
 * audioRecorder.js - Модуль для записи аудио
 * Отвечает за запись аудио с микрофона и отправку на сервер для распознавания
 */

class AudioRecorder {
    /**
     * Создает экземпляр рекордера аудио
     * @param {Object} config - Конфигурация рекордера
     * @param {HTMLElement} config.recordButton - Кнопка записи
     * @param {HTMLElement} config.progressBar - Прогресс-бар записи
     * @param {HTMLElement} config.currentTimeElement - Элемент отображения текущего времени
     * @param {HTMLElement} config.resultText - Элемент для отображения результата распознавания
     * @param {HTMLElement} config.statusMessage - Элемент для отображения статусных сообщений
     * @param {HTMLElement} config.copyButton - Кнопка копирования текста
     * @param {HTMLElement} config.exportPdfButton - Кнопка экспорта в PDF
     * @param {HTMLElement} config.exportTxtButton - Кнопка экспорта в TXT
     * @param {AudioVisualizer} config.audioVisualizerInstance - Экземпляр визуализатора аудио
     * @param {Notifications} config.notificationsInstance - Экземпляр менеджера уведомлений
     * @param {number} config.maxRecordingTime - Максимальное время записи в миллисекундах
     */
    constructor(config) {
        this.recordButton = config.recordButton;
        this.progressBar = config.progressBar;
        this.currentTimeElement = config.currentTimeElement;
        this.resultText = config.resultText;
        this.statusMessage = config.statusMessage;
        this.copyButton = config.copyButton || null;  // Use null default here
        this.exportPdfButton = config.exportPdfButton || null;  // Add null defaults
        this.exportTxtButton = config.exportTxtButton || null;  // Add null defaults
        this.audioVisualizer = config.audioVisualizerInstance;
        this.notifications = config.notificationsInstance;
        this.maxRecordingTime = config.maxRecordingTime;


        // Переменные для записи
        this.mediaRecorder = null;
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.audioChunks = [];
        this.animationFrame = null;
        this.timerInterval = null;
        this.startTime = null;
    }

    /**
     * Форматирует время в миллисекундах в формат "MM:SS"
     * @param {number} ms - Время в миллисекундах
     * @returns {string} - Отформатированное время
     */
    formatTime(ms) {
        const seconds = Math.floor((ms / 1000) % 60).toString().padStart(2, '0');
        const minutes = Math.floor((ms / 1000 / 60) % 60).toString().padStart(2, '0');
        return `${minutes}:${seconds}`;
    }

    /**
     * Обновляет таймер и прогресс-бар во время записи
     */
    updateTimer() {
        const elapsed = Date.now() - this.startTime;
        this.currentTimeElement.textContent = this.formatTime(elapsed);

        // Обновляем прогресс-бар
        const progress = (elapsed / this.maxRecordingTime) * 100;
        this.progressBar.style.width = `${Math.min(progress, 100)}%`;

        // Если достигнут максимальный лимит записи, останавливаем запись
        if (elapsed >= this.maxRecordingTime) {
            this.stopRecording();
        }
    }

    /**
     * Начинает запись аудио с микрофона
     * @returns {Promise<boolean>} - Promise, который резолвится в true если запись началась успешно
     */
    async startRecording() {
        // Изменяем текст кнопки
        this.recordButton.innerHTML = '<i class="fas fa-stop"></i><span>Остановить</span>';
        this.recordButton.classList.add('recording');

        // Инициализируем аудио-контекст
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Показываем сообщение о статусе
        this.statusMessage.textContent = 'Инициализация микрофона...';

        try {
            // Запрашиваем доступ к микрофону
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Сбрасываем предыдущие данные
            this.audioChunks = [];
            this.resultText.textContent = 'Говорите...';
            this.statusMessage.textContent = 'Запись активна';

            // Деактивируем кнопки экспорта
            if (this.copyButton) {
                this.copyButton.disabled = true;
            }
            if (this.exportPdfButton) {
                this.exportPdfButton.disabled = true;
            }
            if (this.exportTxtButton) {
                this.exportTxtButton.disabled = true;
            }


            // Запускаем таймер
            this.startTime = Date.now();
            this.timerInterval = setInterval(() => this.updateTimer(), 100);

            // Настраиваем визуализацию
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            this.microphone.connect(this.analyser);

            // Запускаем визуализацию
            this.animationFrame = this.audioVisualizer.drawWaveform(this.analyser);

            // Создаем медиа-рекордер
            this.mediaRecorder = new MediaRecorder(stream);

            // Событие при получении данных
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            // Событие при остановке записи
            this.mediaRecorder.onstop = () => {
                // Останавливаем все треки
                stream.getTracks().forEach(track => track.stop());

                // Обрабатываем аудио
                this.processAudioData();
            };

            // Начинаем запись
            this.mediaRecorder.start();
            return true;

        } catch (error) {
            this.statusMessage.textContent = `Ошибка доступа к микрофону: ${error.message}`;
            this.recordButton.innerHTML = '<i class="fas fa-microphone"></i><span>Записать</span>';
            this.recordButton.classList.remove('recording');
            console.error('Ошибка доступа к микрофону:', error);
            return false;
        }
    }

    /**
     * Останавливает запись аудио
     */
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.recordButton.innerHTML = '<i class="fas fa-microphone"></i><span>Записать</span>';
            this.recordButton.classList.remove('recording');

            // Останавливаем анимацию и таймер
            cancelAnimationFrame(this.animationFrame);
            clearInterval(this.timerInterval);

            // Закрываем аудио контекст
            if (this.audioContext && this.audioContext.state !== 'closed') {
                this.audioContext.close();
            }

            this.resultText.textContent = 'Обработка записи...';
            this.statusMessage.textContent = 'Идет распознавание речи...';

            // Рисуем пустую волну
            this.audioVisualizer.drawInitialVisualizer();
        }
    }

    /**
     * Обрабатывает записанные аудио-данные и отправляет на сервер для распознавания
     */
    processAudioData() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });

        // Создаем форму для отправки данных
        const formData = new FormData();
        formData.append('audio', audioBlob);

        // Отправляем запрос на сервер
        this.statusMessage.textContent = 'Отправка аудио на распознавание...';

        fetch('/recognize', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                this.resultText.textContent = `Ошибка: ${data.error}`;
                this.statusMessage.textContent = 'Произошла ошибка при распознавании';
                // Не активируем кнопки экспорта при ошибке
            } else {
                this.resultText.textContent = data.transcription || 'Текст не распознан';
                this.statusMessage.textContent = 'Распознавание завершено успешно!';

                // Активируем кнопки экспорта, если есть текст
                        if (data.transcription && data.transcription.trim() !== '') {
            if (this.copyButton) {
                this.copyButton.disabled = false;
            }
            if (this.processButton) {
                this.processButton.disabled = false;
            }
            if (this.exportPdfButton) {
                this.exportPdfButton.disabled = false;
            }
            if (this.exportTxtButton) {
                this.exportTxtButton.disabled = false;
            }
        }

                // Добавляем эффект успешного завершения
                this.resultText.style.animation = 'highlight 1s';
                setTimeout(() => {
                    this.resultText.style.animation = '';
                }, 1000);
            }
        })
        .catch(error => {
            this.resultText.textContent = 'Произошла ошибка при отправке аудио';
            this.statusMessage.textContent = `Ошибка: ${error.message}`;
            console.error('Ошибка при отправке аудио:', error);
        });
    }
}