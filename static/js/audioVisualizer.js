/**
 * audioVisualizer.js - Модуль для визуализации аудио-волны
 * Отвечает за отрисовку визуализации звуковой волны на канвасе
 */

class AudioVisualizer {
    /**
     * Создает экземпляр визуализатора аудио
     * @param {HTMLCanvasElement} canvas - HTML-элемент canvas для визуализации
     */
    constructor(canvas) {
        this.canvas = canvas;
        this.canvasCtx = this.canvas.getContext('2d');
    }

    /**
     * Настраивает размер канваса с учетом плотности пикселей устройства
     */
    setupCanvas() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;

        this.canvasCtx.scale(dpr, dpr);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }

    /**
     * Рисует сетку на канвасе
     */
    drawGrid() {
        const canvasWidth = this.canvas.width / window.devicePixelRatio;
        const canvasHeight = this.canvas.height / window.devicePixelRatio;

        // Рисуем горизонтальные линии
        this.canvasCtx.strokeStyle = '#2d2d2d';
        this.canvasCtx.lineWidth = 1;

        // Горизонтальные линии
        const step = canvasHeight / 4;
        for (let i = 1; i < 4; i++) {
            this.canvasCtx.beginPath();
            this.canvasCtx.moveTo(0, step * i);
            this.canvasCtx.lineTo(canvasWidth, step * i);
            this.canvasCtx.stroke();
        }

        // Вертикальные линии (5-секундные интервалы для 30 секунд)
        const timeSteps = 6;
        for (let i = 1; i < timeSteps; i++) {
            this.canvasCtx.beginPath();
            this.canvasCtx.moveTo((canvasWidth / timeSteps) * i, 0);
            this.canvasCtx.lineTo((canvasWidth / timeSteps) * i, canvasHeight);
            this.canvasCtx.stroke();
        }
    }

    /**
     * Рисует начальное состояние визуализатора (без аудио)
     */
    drawInitialVisualizer() {
        const canvasWidth = this.canvas.width / window.devicePixelRatio;
        const canvasHeight = this.canvas.height / window.devicePixelRatio;

        // Очищаем канвас и заполняем фоном
        this.canvasCtx.fillStyle = '#141414';
        this.canvasCtx.fillRect(0, 0, canvasWidth, canvasHeight);

        // Рисуем сетку
        this.drawGrid();

        // Рисуем центральную линию
        this.canvasCtx.strokeStyle = '#2d2d2d';
        this.canvasCtx.lineWidth = 2;
        this.canvasCtx.beginPath();
        this.canvasCtx.moveTo(0, canvasHeight / 2);
        this.canvasCtx.lineTo(canvasWidth, canvasHeight / 2);
        this.canvasCtx.stroke();

        // Добавляем подпись
        this.canvasCtx.fillStyle = '#9e9e9e';
        this.canvasCtx.font = '12px sans-serif';
        this.canvasCtx.textAlign = 'center';
        this.canvasCtx.fillText('Нажмите кнопку "Записать" для начала',
            canvasWidth / 2,
            canvasHeight / 2 - 20);
    }

    /**
     * Рисует аудио-волну в реальном времени
     * @param {AnalyserNode} analyser - Анализатор аудио из Web Audio API
     * @returns {number} - ID анимационного фрейма для последующей отмены
     */
    drawWaveform(analyser) {
        const bufferLength = analyser.fftSize;
        const dataArray = new Uint8Array(bufferLength);
        let animationFrame;

        const draw = () => {
            animationFrame = requestAnimationFrame(draw);
            analyser.getByteTimeDomainData(dataArray);

            const canvasWidth = this.canvas.width / window.devicePixelRatio;
            const canvasHeight = this.canvas.height / window.devicePixelRatio;

            // Очищаем канвас
            this.canvasCtx.fillStyle = '#141414';
            this.canvasCtx.fillRect(0, 0, canvasWidth, canvasHeight);

            // Рисуем сетку
            this.drawGrid();

            // Рисуем волну с градиентом
            const gradient = this.canvasCtx.createLinearGradient(0, 0, 0, canvasHeight);
            gradient.addColorStop(0, '#8075e5');
            gradient.addColorStop(1, '#6c5ce7');

            this.canvasCtx.lineWidth = 2;
            this.canvasCtx.strokeStyle = gradient;
            this.canvasCtx.beginPath();

            const sliceWidth = canvasWidth / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvasHeight / 2;

                if (i === 0) {
                    this.canvasCtx.moveTo(x, y);
                } else {
                    this.canvasCtx.lineTo(x, y);
                }

                x += sliceWidth;
            }

            this.canvasCtx.lineTo(canvasWidth, canvasHeight / 2);
            this.canvasCtx.stroke();

            // Добавляем свечение для волны
            this.canvasCtx.shadowBlur = 10;
            this.canvasCtx.shadowColor = '#6c5ce7';
        };

        draw();
        return animationFrame;
    }
}