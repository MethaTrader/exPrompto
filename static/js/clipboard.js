/**
 * clipboard.js - Модуль для работы с буфером обмена
 * Отвечает за копирование текста в буфер обмена
 */

class ClipboardManager {
    /**
     * Создает экземпляр менеджера буфера обмена
     * @param {Object} config - Конфигурация менеджера
     * @param {HTMLElement} config.copyButton - Кнопка копирования
     * @param {HTMLElement} config.resultText - Элемент с текстом для копирования
     * @param {Notifications} config.notificationsInstance - Экземпляр менеджера уведомлений
     * @param {HTMLElement} config.statusMessage - Элемент для отображения статусных сообщений
     */
    constructor(config) {
        this.copyButton = config.copyButton;
        this.resultText = config.resultText;
        this.notifications = config.notificationsInstance;
        this.statusMessage = config.statusMessage;
    }

    /**
     * Проверяет, доступен ли API буфера обмена в браузере
     * @returns {boolean} - true, если API доступен
     */
    isClipboardAPIAvailable() {
        return navigator.clipboard !== undefined;
    }

    /**
     * Проверяет, содержит ли элемент с текстом валидный текст для копирования
     * @returns {boolean} - true, если текст валиден для копирования
     */
    hasValidText() {
        const text = this.resultText.textContent.trim();
        return text &&
               text !== 'Здесь появится распознанный текст...' &&
               !text.startsWith('Ошибка:') &&
               !text.startsWith('Говорите...') &&
               !text.startsWith('Обработка записи...');
    }

    /**
     * Копирует текст в буфер обмена через современный API
     * @param {string} text - Текст для копирования
     * @returns {Promise<void>} - Promise, который резолвится после успешного копирования
     */
    async copyWithClipboardAPI(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.notifications.showNotification('copy');
        } catch (error) {
            this.statusMessage.textContent = `Ошибка копирования: ${error.message}`;
            console.error('Ошибка при копировании в буфер обмена:', error);
            throw error;
        }
    }

    /**
     * Копирует текст в буфер обмена через устаревший метод (fallback)
     * @param {string} text - Текст для копирования
     */
    copyWithExecCommand(text) {
        try {
            // Создаем временный элемент textarea
            const textarea = document.createElement('textarea');
            textarea.value = text;

            // Настраиваем стили для скрытия элемента
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            textarea.style.top = '-9999px';

            // Добавляем элемент, выделяем текст и копируем
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();

            const successful = document.execCommand('copy');

            // Удаляем временный элемент
            document.body.removeChild(textarea);

            if (successful) {
                this.notifications.showNotification('copy');
            } else {
                this.statusMessage.textContent = 'Не удалось скопировать текст';
            }
        } catch (error) {
            this.statusMessage.textContent = `Ошибка копирования: ${error.message}`;
            console.error('Ошибка при копировании в буфер обмена:', error);
        }
    }

    /**
     * Копирует текст в буфер обмена, используя доступный метод
     */
    copyToClipboard() {
        if (!this.hasValidText()) {
            return;
        }

        const text = this.resultText.textContent.trim();

        if (this.isClipboardAPIAvailable()) {
            this.copyWithClipboardAPI(text).catch(() => {
                // Если современный API не сработал, используем fallback
                this.copyWithExecCommand(text);
            });
        } else {
            this.copyWithExecCommand(text);
        }
    }
}