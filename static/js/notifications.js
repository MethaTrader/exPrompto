/**
 * notifications.js - Модуль для управления уведомлениями
 * Отвечает за отображение всплывающих уведомлений о действиях пользователя
 */

class Notifications {
    /**
     * Создает экземпляр менеджера уведомлений
     * @param {Object} config - Конфигурация уведомлений
     * @param {HTMLElement} config.copyNotification - Элемент уведомления о копировании
     * @param {HTMLElement} config.pdfNotification - Элемент уведомления о создании PDF
     * @param {HTMLElement} config.txtNotification - Элемент уведомления о создании TXT
     */
    constructor(config) {
        this.notifications = {
            copy: config.copyNotification,
            pdf: config.pdfNotification,
            txt: config.txtNotification
        };

        // Время отображения уведомления в миллисекундах
        this.displayTime = 3000;

        // Текущие таймауты уведомлений
        this.timeouts = {
            copy: null,
            pdf: null,
            txt: null
        };
    }

    /**
     * Показывает выбранное уведомление
     * @param {string} type - Тип уведомления ('copy', 'pdf', 'txt')
     */
    showNotification(type) {
        if (!this.notifications[type]) {
            console.error(`Уведомление типа "${type}" не найдено`);
            return;
        }

        // Очищаем предыдущий таймаут, если он есть
        if (this.timeouts[type]) {
            clearTimeout(this.timeouts[type]);
        }

        // Добавляем класс для показа уведомления
        this.notifications[type].classList.add('show');

        // Устанавливаем таймаут для скрытия уведомления
        this.timeouts[type] = setTimeout(() => {
            this.notifications[type].classList.remove('show');
        }, this.displayTime);
    }

    /**
     * Скрывает выбранное уведомление
     * @param {string} type - Тип уведомления ('copy', 'pdf', 'txt')
     */
    hideNotification(type) {
        if (!this.notifications[type]) {
            console.error(`Уведомление типа "${type}" не найдено`);
            return;
        }

        // Очищаем таймаут, если он есть
        if (this.timeouts[type]) {
            clearTimeout(this.timeouts[type]);
            this.timeouts[type] = null;
        }

        // Удаляем класс для скрытия уведомления
        this.notifications[type].classList.remove('show');
    }

    /**
     * Скрывает все уведомления
     */
    hideAllNotifications() {
        // Перебираем все типы уведомлений и скрываем их
        Object.keys(this.notifications).forEach(type => {
            this.hideNotification(type);
        });
    }

    /**
     * Обновляет текст уведомления
     * @param {string} type - Тип уведомления ('copy', 'pdf', 'txt')
     * @param {string} text - Новый текст уведомления
     */
    updateNotificationText(type, text) {
        if (!this.notifications[type]) {
            console.error(`Уведомление типа "${type}" не найдено`);
            return;
        }

        // Ищем текстовый узел в уведомлении (после иконки)
        const textNode = Array.from(this.notifications[type].childNodes)
            .find(node => node.nodeType === Node.TEXT_NODE);

        if (textNode) {
            textNode.nodeValue = text;
        } else {
            // Если текстового узла нет, добавляем новый текст после иконки
            const iconElement = this.notifications[type].querySelector('i');
            if (iconElement) {
                iconElement.insertAdjacentText('afterend', text);
            } else {
                // Если нет иконки, просто устанавливаем текст напрямую
                this.notifications[type].textContent = text;
            }
        }
    }
}