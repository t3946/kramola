/**
 * Сервис для работы с Socket.IO
 * Предоставляет простой интерфейс для подключения к комнатам и подписки на события
 */

import {io} from 'socket.io-client';

class SocketioService {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.rooms = new Map(); // Хранит информацию о подключенных комнатах
    }

    /**
     * Инициализирует подключение к Socket.IO
     * @param {string} url - URL сервера (опционально, по умолчанию текущий домен)
     * @returns {Promise} - Promise, который резолвится при подключении
     */
    connect(url = null) {
        if (this.socket && this.connected) {
            return Promise.resolve();
        }

        if (this.socket && !this.connected) {
            return new Promise((resolve) => {
                this.socket.once('connect', () => {
                    this.connected = true;
                    resolve();
                });
            });
        }

        this.socket = url ? io(url) : io();

        return new Promise((resolve, reject) => {
            const connectHandler = () => {
                this.connected = true;
                console.log('Socket.IO connected');
                resolve();
            };

            const errorHandler = (error) => {
                console.error('Socket.IO connection error:', error);
                reject(error);
            };

            this.socket.once('connect', connectHandler);
            this.socket.once('connect_error', errorHandler);

            this.socket.on('disconnect', () => {
                this.connected = false;
                console.log('Socket.IO disconnected');
            });
        });
    }

    /**
     * Подключается к комнате прогресса задачи
     * @param {string} taskId - ID задачи
     * @param {Function} onProgress - Callback для события progress
     * @param {Function} onJoined - Callback для события joined
     * @param {Function} onStatus - Callback для события task_status
     */
    async joinTaskProgress(taskId, onProgress = null, onJoined = null, onStatus = null) {
        if (!this.socket || !this.connected) {
            await this.connect();
        }

        if (!this.socket || !this.connected) {
            console.error('Socket.IO not connected, cannot join room');
            return;
        }

        // Если уже подписаны на эту комнату, сначала отписываемся
        if (this.rooms.has(taskId)) {
            console.log('Already subscribed to room, cleaning up old handlers:', taskId);
            this.leaveTaskProgress(taskId);
        }

        // Сначала подписываемся на события, чтобы не пропустить события от сервера
        const handlers = [];

        if (onProgress) {
            const progressHandler = (data) => {
                console.log('Progress event received:', data);
                if (data.task_id === taskId) {
                    onProgress(data);
                } else {
                    console.warn('Progress event task_id mismatch:', data.task_id, 'expected:', taskId);
                }
            };
            this.socket.on('progress', progressHandler);
            handlers.push({event: 'progress', handler: progressHandler});
        }

        if (onJoined) {
            const joinedHandler = (data) => {
                console.log('Joined event received:', data);
                if (data.task_id === taskId) {
                    onJoined(data);
                } else {
                    console.warn('Joined event task_id mismatch:', data.task_id, 'expected:', taskId);
                }
            };
            this.socket.on('joined', joinedHandler);
            handlers.push({event: 'joined', handler: joinedHandler});
        }

        if (onStatus) {
            const statusHandler = (data) => {
                if (data.task_id === taskId) {
                    onStatus(data);
                } else {
                    console.warn('Status event task_id mismatch:', data.task_id, 'expected:', taskId);
                }
            };
            this.socket.on('task_status', statusHandler);
            handlers.push({event: 'task_status', handler: statusHandler});
        }

        // Сохраняем информацию о комнате
        this.rooms.set(taskId, {handlers});

        // Отправляем запрос на подключение к комнате после подписки на события
        console.log('Joining task progress room:', taskId);
        this.socket.emit('join_task_progress', {task_id: taskId});
    }

    /**
     * Отключается от комнаты прогресса задачи
     * @param {string} taskId - ID задачи
     */
    leaveTaskProgress(taskId) {
        if (!this.socket || !this.connected) {
            return;
        }

        // Отправляем запрос на отключение от комнаты
        this.socket.emit('leave_task_progress', {task_id: taskId});

        // Отписываемся от событий
        const roomInfo = this.rooms.get(taskId);
        if (roomInfo && roomInfo.handlers) {
            roomInfo.handlers.forEach(({event, handler}) => {
                this.socket.off(event, handler);
            });
        }

        // Удаляем информацию о комнате
        this.rooms.delete(taskId);
    }

    /**
     * Подписывается на произвольное событие
     * @param {string} event - Название события
     * @param {Function} handler - Обработчик события
     */
    async on(event, handler) {
        if (!this.socket || !this.connected) {
            await this.connect();
        }
        if (this.socket) {
            this.socket.on(event, handler);
        }
    }

    /**
     * Отписывается от события
     * @param {string} event - Название события
     * @param {Function} handler - Обработчик события (опционально)
     */
    off(event, handler = null) {
        if (!this.socket) {
            return;
        }
        if (handler) {
            this.socket.off(event, handler);
        } else {
            this.socket.off(event);
        }
    }

    /**
     * Отправляет событие на сервер
     * @param {string} event - Название события
     * @param {object} data - Данные для отправки
     */
    emit(event, data) {
        if (!this.socket || !this.connected) {
            return;
        }
        this.socket.emit(event, data);
    }

    /**
     * Проверяет, подключен ли сокет
     * @returns {boolean}
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
}

// Создаем единственный экземпляр сервиса (singleton)
const socketIOService = new SocketioService();

// Экспортируем для использования в других модулях
export default socketIOService;
