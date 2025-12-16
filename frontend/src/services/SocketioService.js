/**
 * Сервис для работы с Socket.IO
 * Предоставляет простой интерфейс для подключения к комнатам и подписки на события
 */

class SocketioService {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.rooms = new Map(); // Хранит информацию о подключенных комнатах
    }

    /**
     * Инициализирует подключение к Socket.IO
     * @param {string} url - URL сервера (опционально, по умолчанию текущий домен)
     */
    connect(url = null) {
        if (this.socket && this.connected) {
            return;
        }

        if (typeof io === 'undefined') {
            return;
        }

        this.socket = url ? io(url) : io();
        
        this.socket.on('connect', () => {
            this.connected = true;
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
        });
    }

    /**
     * Подключается к комнате прогресса задачи
     * @param {string} taskId - ID задачи
     * @param {Function} onProgress - Callback для события progress
     * @param {Function} onJoined - Callback для события joined
     */
    joinTaskProgress(taskId, onProgress = null, onJoined = null) {
        if (!this.socket || !this.connected) {
            this.connect();
        }

        if (!this.socket) {
            return;
        }

        // Отправляем запрос на подключение к комнате
        this.socket.emit('join_task_progress', { task_id: taskId });

        // Подписываемся на события
        const handlers = [];
        
        if (onProgress) {
            const progressHandler = (data) => {
                if (data.task_id === taskId) {
                    onProgress(data);
                }
            };
            this.socket.on('progress', progressHandler);
            handlers.push({ event: 'progress', handler: progressHandler });
        }

        if (onJoined) {
            const joinedHandler = (data) => {
                if (data.task_id === taskId) {
                    onJoined(data);
                }
            };
            this.socket.on('joined', joinedHandler);
            handlers.push({ event: 'joined', handler: joinedHandler });
        }

        // Сохраняем информацию о комнате
        this.rooms.set(taskId, { handlers });
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
        this.socket.emit('leave_task_progress', { task_id: taskId });

        // Отписываемся от событий
        const roomInfo = this.rooms.get(taskId);
        if (roomInfo && roomInfo.handlers) {
            roomInfo.handlers.forEach(({ event, handler }) => {
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
    on(event, handler) {
        if (!this.socket) {
            this.connect();
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
