 SprintHealth — это приложение для анализа и визуализации данных Agile-команд, которое предоставляет ключевую информацию о ходе спринтов. Приложение помогает командам мониторить состояние задач, управлять метриками производительности и принимать решения на основе данных.

        ---

        ## Основные возможности
        1. **Загрузка данных**:
        - Поддерживаются файлы CSV для:
            - Entities (задачи в спринте).
            - History (история изменений задач).
            - Sprints (спринты и их атрибуты).

        2. **Анализ данных**:
        - Анализ задач для выбранного спринта.
        - Распределение задач по статусам, приоритетам и командам спринта.
        - Основные метрики:
            - Общее количество задач.
            - Сумма оценок задач в часах.
        - Отслеживание прогресса задач по датам.

        3. **Интерактивная визуализация**:
        - **Диаграмма распределения задач**: Распределение задач по статусам.
        - **График приоритетов**: Количество задач по уровням приоритета.
        - **Burndown Chart**: Прогресс выполнения задач в течение спринта.
        - **Cumulative Flow Diagram (CFD)**: Наглядное распределение задач по статусам со временем.

        ---

        ## Категории статусов

        - **К выполнению**: задачи, которые еще не начаты и ожидают выполнения.
        - **В работе**: задачи, которые находятся в процессе выполнения.
        - **Сделано**: задачи, которые завершены или отклонены.

        ### Приоритеты задач

        - **Низкий**: задачи с наименьшим приоритетом.
        - **Средний**: задачи со средним приоритетом.
        - **Высокий**: задачи с высоким приоритетом.
        - **Критический**: задачи с наивысшим приоритетом, требующие немедленного внимания.

        ### Метрики здоровья спринта

        - **К выполнению**: SUM (estimation/3600) в человеко-часах
        - **В работе**: SUM (estimation/3600) в человеко-часах
        - **Сделано**: SUM (estimation/3600) в человеко-часах
        - **Снято**: SUM (estimation/3600) в человеко-часах
        - **Бэклог изменен**: (twoDaysAfterStartOfSprint * 100) / startOfSprint в процентах

        ### Критерии успешности спринта

        - Статусы задач изменяются равномерно: "К выполнению" → "В работе" → "Сделано".
        - Параметр "К выполнению" не должен составлять более 20% от общего объёма.
        - Параметр "Снято" не должен составлять более 10% от общего объёма.
        - Бэклог не должен изменяться более чем на 20% после начала спринта.
                    
        Таким образом, цвет имени спринта (зеленый, желтый, оранжевый, красный) отражает его здоровье, на основе выполнения главных критериев оценки спринта. 
                    Кроме того, добавлена возможность регулировки критериев оценки здоровья.

        ---

        ## Как пользоваться приложением

        ### Шаг 1: Загрузка данных
        1. Загрузите три CSV-файла через интерфейс:
        - **Entities CSV**: Содержит задачи (ID задачи, статус, приоритет, исполнитель и т.д.).
        - **History CSV**: Хранит изменения задач (даты изменения, новые значения статусов и приоритетов).
        - **Sprints CSV**: Информация о спринтах (названия, даты начала/окончания, список задач).

        2. Нажмите кнопку **"Загрузить данные"**.

        ### Шаг 2: Выбор спринтов
        1. После успешной загрузки данных выберите спринт для анализа через **выпадающий список**.
        2. Можно выбрать до 4 спринтов для анализа одновременно.
        3. Опционально можно выбрать одну или несколько команд, учавствующих в спринте, для сравнения между собой
        4. Опционально выбрать членов команды

        ### Шаг 3: Просмотр аналитики
        После нажатия кнопки "Начать анализ" доступны следующие параметры (указаны только основные):
        - **Визуализация**:
        \t- Распределение задач по статусам.
        \t- Распределение задач по приоритетам.
        - **Основные метрики**:
        \t- Общее количество задач.
        \t- Суммарное время оценок задач.
        \t- Количество задач в определённых статусах.
        - **Диаграммы прогресса**:
        \t- **Burndown Chart**: Прогресс выполнения задач.
        \t- **Cumulative Flow Diagram**: Наглядное изменение задач по статусам со временем.
        """)

Важно:
Убедитесь, что Python установлен на вашем компьютере и добавлен в системный PATH.
Для первого запуска рекомендуется подключение к интернету, чтобы программа могла установить недостающие библиотеки.

1. Подготовка приложения
Переместите папку SprintHealth в любое удобное место (Например, на рабочий стол для быстрого доступа

2. Запуск приложения
Откройте папку SprintHealth и запустите файл SprintHealth runner.
Этот файл запускает основной скрипт приложения SprintHealth.py.

3. Процессы в консоли
После запуска приложения откроется консоль. На этом этапе происходит следующее:

Программа проверяет наличие необходимых библиотек Python для корректной работы приложения.
Проверяемые библиотеки (при отсутствии будут установлены автоматически):
*Streamlit
*Pandas
*NumPy
*Plotly

4. Доступ к приложению
После проверки библиотек автоматически откроется окно браузера с интерфейсом приложения.

Если браузер не открылся автоматически, вы можете найти ссылку в консоли. Вы увидите сообщение вида:

"You can now view your Streamlit app in your browser.

Local URL: http://localhost:xxxx  
Network URL: http://xxx.xx.xx.x:xxxx"

Просто нажмите на Local URL или Network URL

5. Для закрытия приложения нажмите на "Крестик" в консоли (Или CTRL +C)

Приятного использования SprintHealth! 🚀






