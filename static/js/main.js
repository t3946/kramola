// main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM загружен, скрипт main.js выполняется.");

    // --- ОБЩИЕ ЭЛЕМЕНТЫ DOM (объявляем один раз) ---
    const uploadForm = document.getElementById('uploadForm');
    const submitButton = document.getElementById('submitButton');
    const clientErrorMessage = document.getElementById('clientErrorMessage');
    const serverErrorMessage = document.getElementById('serverErrorMessage'); // Для ошибок от Flask при рендере
    const sourceFileInput = document.getElementById('source_file');
    const wordsFileInput = document.getElementById('words_file');
    const wordsTextarea = document.getElementById('words-textarea');
    const predefinedCheckboxes = document.querySelectorAll('input[name="predefined_list_keys"]');
    const checkboxGroup = document.querySelector('.checkbox-group');
    const inputMethodRadios = document.querySelectorAll('input[name="input-method"]');

    // Элементы для отображения статуса АСИНХРОННОЙ обработки
    const processingMessageDiv = document.getElementById('processingMessage');
    const loaderIcon = document.getElementById('loaderIcon');
    const statusTextElement = document.getElementById('statusText');

    // Элемент preloader из старой логики (если все еще нужен для чего-то, иначе можно удалить)
    const preloader = document.getElementById('preloader'); // Убедитесь, что этот элемент есть в HTML, если используется

    // --- ПРОВЕРКА НАЛИЧИЯ КЛЮЧЕВЫХ ЭЛЕМЕНТОВ (ВАЖНО!) ---
    if (!uploadForm) console.error("ОШИБКА: Элемент uploadForm не найден!");
    if (!submitButton) console.error("ОШИБКА: Элемент submitButton не найден!");
    if (!sourceFileInput) console.error("ОШИБКА: Элемент sourceFileInput не найден!");
    if (!clientErrorMessage) console.warn("Предупреждение: clientErrorMessage не найден.");

    // Для асинхронной логики
    if (!processingMessageDiv) console.error("ОШИБКА АСИНХ: Элемент processingMessageDiv не найден!");
    if (!loaderIcon) console.error("ОШИБКА АСИНХ: Элемент loaderIcon не найден!");
    if (!statusTextElement) console.error("ОШИБКА АСИНХ: Элемент statusTextElement не найден!");


    // --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ИЗ ВЕРХНЕЙ ЧАСТИ (валидация и т.д.) ---
    function handleInvalidFile(fileInput, buttonSelector, fileInfoId, defaultFileInfoText, errorMessageText) {
        if (clientErrorMessage) {
            clientErrorMessage.textContent = errorMessageText;
            clientErrorMessage.style.display = 'block';
        }
        const button = document.querySelector(buttonSelector);
        if (button && button.style) {
            button.style.border = '2px solid red !important';
        } else if (fileInput && fileInput.style) {
            fileInput.style.border = '2px solid red !important';
        }
        if (fileInput) fileInput.value = '';
        const fileInfoElement = document.getElementById(fileInfoId);
        if (fileInfoElement) {
            fileInfoElement.textContent = defaultFileInfoText;
        }
        window.scrollTo(0, 0);
    }

    function resetHighlights() {
        if (sourceFileInput && sourceFileInput.style) sourceFileInput.style.border = '';
        const sourceFileButton = document.querySelector('button[onclick*="source_file"]');
        if (sourceFileButton && sourceFileButton.style) sourceFileButton.style.border = '';

        if (wordsFileInput && wordsFileInput.style) wordsFileInput.style.border = '';
        const wordsFileButton = document.querySelector('button[onclick*="words_file"]');
        if (wordsFileButton && wordsFileButton.style) wordsFileButton.style.border = '';

        if (wordsTextarea && wordsTextarea.style) wordsTextarea.style.border = '';
        if (checkboxGroup && checkboxGroup.style) checkboxGroup.style.border = '';
    }

    function validateFileExtensions() {
        // ... (код validateFileExtensions без изменений) ...
        let isValid = true;
        if (!uploadForm) return true;

        const formAction = uploadForm.getAttribute('action') || '';
        const isHighlightForm = formAction.includes('highlight.process'); // или highlight.process_async
        const isFootnotesForm = formAction.includes('footnotes.process');

        if (sourceFileInput && sourceFileInput.files.length > 0) {
            const file = sourceFileInput.files[0];
            const fileName = file.name.toLowerCase();
            let allowedExtensionsRegex, errorMessage, defaultInfoText;
            if (isFootnotesForm) {
                allowedExtensionsRegex = /\.docx$/i;
                errorMessage = 'Ошибка: Исходный документ должен быть в формате .docx.';
                defaultInfoText = 'Файл: docx | файл не выбран';
            } else {
                allowedExtensionsRegex = /\.docx|\.pdf$/i;
                errorMessage = 'Ошибка: Исходный документ должен быть в формате .docx или .pdf.';
                defaultInfoText = 'Файл: docx, pdf | файл не выбран';
            }
            if (!allowedExtensionsRegex.test(fileName)) {
                handleInvalidFile(sourceFileInput, 'button[onclick*="source_file"]', 'source_file_info', defaultInfoText, `${errorMessage} Некорректный файл: ${file.name}`);
                isValid = false;
            } else {
                const button = document.querySelector('button[onclick*="source_file"]');
                if (button && button.style) button.style.border = '';
            }
        }

        if (wordsFileInput && wordsFileInput.files.length > 0) {
            const file = wordsFileInput.files[0];
            const fileName = file.name.toLowerCase();
            let allowedExtensionsRegex, errorMessage, defaultInfoText;
            // Убедитесь, что isHighlightForm правильно определяется для async эндпоинта
            const currentFormAction = uploadForm.getAttribute('action') || '';
            const isCurrentHighlightForm = currentFormAction.includes('highlight.process') || currentFormAction.includes('highlight.process_async');

            if (isCurrentHighlightForm) { // Используем isCurrentHighlightForm для файла слов
                allowedExtensionsRegex = /\.docx|\.xlsx$/i;
                errorMessage = 'Ошибка: Файл со словами должен быть в формате .docx или .xlsx.';
                defaultInfoText = 'Файл: docx, excel | файл не выбран';
            } else { // Для других форм, например, isFootnotesForm
                allowedExtensionsRegex = /\.docx$/i;
                errorMessage = 'Ошибка: Файл со словами должен быть в формате .docx.';
                defaultInfoText = 'Файл: docx | файл не выбран';
            }
            if (!allowedExtensionsRegex.test(fileName)) {
                handleInvalidFile(wordsFileInput, 'button[onclick*="words_file"]', 'words_file_info', defaultInfoText, `${errorMessage} Некорректный файл: ${file.name}`);
                isValid = false;
            } else {
                const button = document.querySelector('button[onclick*="words_file"]');
                if (button && button.style) button.style.border = '';
            }
        }
        return isValid;
    }

    function validateFields() {
        // ... (код validateFields без изменений, но убедитесь, что isHighlightForm правильно определяется для async) ...
        console.log("--- validateFields ---");
        resetHighlights();
        if (clientErrorMessage) {
            clientErrorMessage.textContent = '';
            clientErrorMessage.style.display = 'none';
        }

        if (!uploadForm || !sourceFileInput) {
            console.error("Критическая ошибка: uploadForm или sourceFileInput не найдены.");
            if (clientErrorMessage) {
                clientErrorMessage.textContent = 'Ошибка конфигурации страницы. Обновите.';
                clientErrorMessage.style.display = 'block';
            }
            return false;
        }

        const sourceFileSelected = sourceFileInput.files.length > 0;
        const formAction = uploadForm.getAttribute('action') || '';
        // Важно: Асинхронная форма может иметь другой action, например, /highlight/process_async
        const isHighlightForm = formAction.includes('highlight.process') || formAction.includes('highlight.process_async');
        const isFootnotesForm = formAction.includes('footnotes.process');

        if (!sourceFileSelected) {
            console.log("Ошибка: Исходный документ не выбран.");
            let errorText = 'Ошибка: Необходимо загрузить исходный документ';
            if (isFootnotesForm) {
                errorText += ' (.docx).';
            } else if (isHighlightForm) { // Явно для highlight
                errorText += ' (.docx или .pdf).';
            } else { // Общий случай, если не одна из известных форм
                errorText += '.';
            }
             if (clientErrorMessage) {
                clientErrorMessage.textContent = errorText;
                clientErrorMessage.style.display = 'block';
            }
            const sourceButton = document.querySelector('button[onclick*="source_file"]');
            if (sourceButton && sourceButton.style) sourceButton.style.border = '2px solid red !important';
            else if (sourceFileInput && sourceFileInput.style) sourceFileInput.style.border = '2px solid red !important';
            window.scrollTo(0, 0);
            return false;
        }

        if (isHighlightForm) {
            console.log("Форма 'Выделение слов'. Проверка источников слов...");
            const wordsFileSelected = wordsFileInput ? wordsFileInput.files.length > 0 : false;
            const wordsTextEntered = wordsTextarea ? wordsTextarea.value.trim().length > 0 : false;
            let predefinedListSelected = false;
            predefinedCheckboxes.forEach(checkbox => {
                if (checkbox.checked) predefinedListSelected = true;
            });
            const selectedMethod = document.querySelector('input[name="input-method"]:checked')?.value || 'file';

            if (!predefinedListSelected &&
                ((selectedMethod === 'file' && !wordsFileSelected) || (selectedMethod === 'text' && !wordsTextEntered))
            ) {
                if (clientErrorMessage) {
                    clientErrorMessage.textContent = 'Ошибка: Укажите источник слов - загрузите файл, введите текст или выберите готовый список.';
                    clientErrorMessage.style.display = 'block';
                }
                if (selectedMethod === 'file' && !wordsFileSelected) {
                    const btn = document.querySelector('button[onclick*="words_file"]');
                    if (btn && btn.style) btn.style.border = '2px solid red !important';
                    else if (wordsFileInput && wordsFileInput.style) wordsFileInput.style.border = '2px solid red !important';
                } else if (selectedMethod === 'text' && !wordsTextEntered) {
                    if (wordsTextarea && wordsTextarea.style) wordsTextarea.style.border = '2px solid red !important';
                }
                if (checkboxGroup && checkboxGroup.style) checkboxGroup.style.border = '2px solid red !important';
                window.scrollTo(0, 0);
                return false;
            }
        }
        console.log("--- validateFields успешно завершена ---");
        return true;
    }

    // --- ОБРАБОТЧИКИ СОБЫТИЙ ДЛЯ ВАЛИДАЦИИ И UI (из верхней части) ---
    if (sourceFileInput) {
        sourceFileInput.addEventListener('change', function() {
            resetHighlights();
            validateFileExtensions();
            const fileInfo = document.getElementById('source_file_info');
            if(fileInfo) fileInfo.textContent = this.files.length > 0 ? `Файл: ${this.files[0].name}` : 'Файл: docx, pdf | файл не выбран';
        });
    }
    if (wordsFileInput) {
        wordsFileInput.addEventListener('change', function() {
            resetHighlights();
            validateFileExtensions();
            const fileInfo = document.getElementById('words_file_info');
            if(fileInfo) fileInfo.textContent = this.files.length > 0 ? `Файл: ${this.files[0].name}` : 'Файл: docx, excel | файл не выбран';
        });
    }
    if (wordsTextarea) {
        wordsTextarea.addEventListener('input', () => {
            resetHighlights();
            adjustTextareaHeight();
        });
    }
    predefinedCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', resetHighlights);
    });
    if (inputMethodRadios.length > 0) {
        inputMethodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                resetHighlights();
                toggleInputMethod();
            });
        });
    }


    // --- ФУНКЦИИ ДЛЯ ПЕРЕКЛЮЧЕНИЯ МЕТОДА ВВОДА И РАЗМЕРА TEXTAREA (из старого кода) ---
    function toggleInputMethod() {
        const fileInputDiv = document.getElementById('file-input'); // Используем fileInputDiv вместо fileInput
        const textInputDiv = document.getElementById('text-input'); // Используем textInputDiv вместо textInput
        const fileLabel = document.querySelector('label[for="file-method"]');
        const textLabel = document.querySelector('label[for="text-method"]');
        const selectedMethodRadio = document.querySelector('input[name="input-method"]:checked');

        if (!selectedMethodRadio || !fileInputDiv || !textInputDiv || !fileLabel || !textLabel) {
            console.error("Ошибка в toggleInputMethod: один из элементов не найден.");
            return;
        }
        const selectedMethod = selectedMethodRadio.value;

        if (selectedMethod === 'file') {
            fileInputDiv.classList.remove('hidden');
            textInputDiv.classList.add('hidden');
            fileLabel.classList.add('active');
            textLabel.classList.remove('active');
        } else {
            fileInputDiv.classList.add('hidden');
            textInputDiv.classList.remove('hidden');
            fileLabel.classList.remove('active');
            textLabel.classList.add('active');
            if (wordsTextarea) adjustTextareaHeight(); // Вызываем, если wordsTextarea существует
        }
    }

    function adjustTextareaHeight() {
        if (wordsTextarea) { // Проверка, что элемент существует
            wordsTextarea.style.height = 'auto';
            wordsTextarea.style.height = Math.min(wordsTextarea.scrollHeight, 200) + 'px';
        }
    }

    // Инициализация переключателя и textarea при загрузке
    toggleInputMethod();
    if(wordsTextarea) adjustTextareaHeight();


    // --- ЛОГИКА АСИНХРОННОЙ ОТПРАВКИ И ОПРОСА СТАТУСА (из нижней части) ---
    let currentTaskId = null;
    let pollIntervalId = null;

    function displayClientError(message) {
        if (serverErrorMessage && serverErrorMessage.style) serverErrorMessage.style.display = 'none';
        if (clientErrorMessage) {
            clientErrorMessage.textContent = message;
            clientErrorMessage.style.display = 'block';
        }
    }

    function clearClientError() {
        if (clientErrorMessage) {
            clientErrorMessage.textContent = '';
            clientErrorMessage.style.display = 'none';
        }
    }

    function showProcessingState(message = "Ваш файл обрабатывается. Пожалуйста, подождите...") {
        // Важно: Убедитесь, что эти элементы есть в HTML!
        if (processingMessageDiv && processingMessageDiv.style) processingMessageDiv.style.display = 'block';
        if (loaderIcon && loaderIcon.style) loaderIcon.style.display = 'block'; // или 'inline-block' или 'flex' в зависимости от вашего CSS
        if (statusTextElement) statusTextElement.textContent = message;

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Обрабатывается...';
        }
    }

    function hideProcessingState() {
        if (processingMessageDiv && processingMessageDiv.style) processingMessageDiv.style.display = 'none';
        if (loaderIcon && loaderIcon.style) loaderIcon.style.display = 'none';
        if (statusTextElement) statusTextElement.textContent = '';

        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Обработать';
        }
    }

    function pollTaskStatus(taskId) {
        if (pollIntervalId) clearInterval(pollIntervalId);

        pollIntervalId = setInterval(() => {
            fetch(`/highlight/task_status/${taskId}`) // Убедитесь, что URL правильный
                .then(response => {
                    if (!response.ok) {
                        return response.json().catch(() => {
                            throw new Error(`Ошибка сервера: ${response.status} ${response.statusText}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if(statusTextElement) statusTextElement.textContent = data.status || 'Проверка статуса...';
                    console.log("Task status:", data);

                    if (data.state === 'SUCCESS') {
                        clearInterval(pollIntervalId);
                        pollIntervalId = null;
                        if(statusTextElement) statusTextElement.textContent = "Обработка завершена! Перенаправление...";
                        window.location.href = `/highlight/results?task_id=${taskId}`;
                    } else if (data.state === 'FAILURE') {
                        clearInterval(pollIntervalId);
                        pollIntervalId = null;
                        hideProcessingState();
                        let errorMsg = data.status || 'Произошла ошибка при обработке файла.';
                        window.location.href = `/highlight/results?task_id=${taskId}`;
                    } else if (data.state === 'NOT_FOUND') {
                        clearInterval(pollIntervalId);
                        pollIntervalId = null;
                        hideProcessingState();
                        displayClientError('Задача не найдена на сервере. Попробуйте снова.');
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке статуса:', error);
                    clearInterval(pollIntervalId);
                    pollIntervalId = null;
                    hideProcessingState();
                    displayClientError('Не удалось проверить статус задачи: ' + error.message);
                });
        }, 3000);
    }

    // ОСНОВНОЙ ОБРАБОТЧИК ОТПРАВКИ ФОРМЫ (АСИНХРОННЫЙ)
    if (submitButton && uploadForm) {
        submitButton.addEventListener('click', function(event) {
            event.preventDefault(); // Предотвращаем стандартную отправку формы
            clearClientError();
            if (serverErrorMessage && serverErrorMessage.style) serverErrorMessage.style.display = 'none';

            // Выполняем ВАШУ валидацию полей и расширений
            if (!validateFields()) {
                console.log("Отправка ПРЕДОТВРАЩЕНА: ошибки валидации полей.");
                return;
            }
            if (!validateFileExtensions()) {
                console.log("Отправка ПРЕДОТВРАЩЕНА: ошибки расширений файлов.");
                return;
            }

            // Валидация из нового блока (можно объединить с validateFields или оставить как доп. быструю проверку)
            // const sourceFile = sourceFileInput.files[0]; // sourceFileInput уже есть
            // if (!sourceFile) {
            //     displayClientError('Пожалуйста, выберите исходный документ.');
            //     return;
            // }
            // ... (остальные быстрые проверки из нового блока можно оставить или интегрировать в validateFields)

            const formData = new FormData(uploadForm);
            showProcessingState(); // Эта функция теперь должна работать, если HTML элементы добавлены

            // Убедитесь, что uploadForm.action указывает на АСИНХРОННЫЙ эндпоинт
            // например, /highlight/process_async
            fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    return response.json().then(data => ({ ok: response.ok, status: response.status, data }));
                } else {
                    return response.text().then(text => {
                        throw new Error(`Неожиданный ответ сервера (не JSON): ${response.status}. Ответ: ${text.substring(0,200)}...`);
                    });
                }
            })
            .then(responseData => {
                const { ok, status, data } = responseData;
                if (ok && data.task_id) { // HTTP 202 Accepted
                    currentTaskId = data.task_id;
                    if(statusTextElement) statusTextElement.textContent = data.message || 'Задача принята, ID: ' + currentTaskId;
                    pollTaskStatus(currentTaskId);
                } else {
                    hideProcessingState();
                    let errorMsg = 'Произошла ошибка.';
                    if (data && data.error) {
                        errorMsg = data.error;
                    } else if (status) {
                        errorMsg = `Ошибка сервера: ${status}`;
                    }
                    displayClientError(errorMsg);
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке формы:', error);
                hideProcessingState();
                displayClientError('Произошла ошибка при отправке запроса: ' + error.message);
            });
        });
    } else {
        console.error("Не найден submitButton или uploadForm для асинхронной отправки.");
    }

    // Проверка ID задачи при загрузке страницы
    const urlParams = new URLSearchParams(window.location.search);
    const checkTaskId = urlParams.get('check_task_id');
    if (checkTaskId) {
        currentTaskId = checkTaskId;
        showProcessingState('Проверяем статус предыдущей задачи...');
        pollTaskStatus(currentTaskId);
    }

    // Скрытие серверной ошибки через некоторое время (из старого кода)
    if (serverErrorMessage) {
        if (serverErrorMessage.textContent && serverErrorMessage.textContent.trim()) {
            serverErrorMessage.style.display = 'block';
            // Плавное исчезновение не будет работать, если мы его сразу скрываем в displayClientError
            // Оставляю логику, но она может конфликтовать.
            /*
            serverErrorMessage.style.transition = 'opacity 0.5s ease-out';
            setTimeout(function() {
                if (serverErrorMessage.style) serverErrorMessage.style.opacity = '0';
                setTimeout(function() {
                    if (serverErrorMessage.parentNode && serverErrorMessage.style) {
                         serverErrorMessage.style.display = 'none';
                    }
                }, 500);
            }, 5000);
            */
        } else if (serverErrorMessage.style) {
            serverErrorMessage.style.display = 'none';
        }
    }

    console.log("Все обработчики событий установлены.");
});