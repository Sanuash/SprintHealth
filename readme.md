# Sprint Analysis Tool

## Основные возможности

### Загрузка данных
Поддерживается импорт CSV-файлов для анализа:
- **Entities** – список задач в спринте (ID, статус, приоритет, исполнитель и т. д.).
- **History** – история изменений статусов и приоритетов задач.
- **Sprints** – информация о спринтах (названия, даты, список задач).

### Анализ данных
- Анализ задач в выбранном спринте.
- Распределение задач по статусам, приоритетам и командам.
- Основные метрики:
  - Общее количество задач.
  - Сумма оценок задач в человеко-часах.
  - Отслеживание прогресса задач по датам.

### Интерактивная визуализация
- **Диаграмма распределения задач** – отображает задачи по статусам.
- **График приоритетов** – количество задач по уровням приоритета.
- **Burndown Chart** – прогресс выполнения задач в течение спринта.
- **Cumulative Flow Diagram (CFD)** – наглядное распределение задач по статусам во времени.

---

## Категории статусов

- **К выполнению** – задачи, ожидающие выполнения.
- **В работе** – задачи, находящиеся в процессе выполнения.
- **Сделано** – завершенные или отклоненные задачи.

### Приоритеты задач

- **Низкий** – задачи с наименьшим приоритетом.
- **Средний** – задачи со средним приоритетом.
- **Высокий** – задачи с высоким приоритетом.
- **Критический** – задачи, требующие немедленного внимания.

### Метрики здоровья спринта

- **К выполнению**: `SUM(estimation/3600)` в человеко-часах.
- **В работе**: `SUM(estimation/3600)` в человеко-часах.
- **Сделано**: `SUM(estimation/3600)` в человеко-часах.
- **Снято**: `SUM(estimation/3600)` в человеко-часах.
- **Бэклог изменен**: `(twoDaysAfterStartOfSprint * 100) / startOfSprint` в процентах.

### Критерии успешности спринта

- Статусы задач изменяются равномерно: **"К выполнению" → "В работе" → "Сделано"**.
- Параметр **"К выполнению"** не должен составлять более **20%** от общего объема.
- Параметр **"Снято"** не должен превышать **10%** от общего объема.
- Бэклог не должен изменяться более чем на **20%** после начала спринта.

Цвет имени спринта (зеленый, желтый, оранжевый, красный) отражает его здоровье на основе выполнения основных критериев. Доступна возможность настройки критериев оценки здоровья.

---

## Как пользоваться приложением

### Шаг 1: Загрузка данных
1. Загрузите три CSV-файла через интерфейс:
   - **Entities CSV** – содержит список задач.
   - **History CSV** – фиксирует изменения задач.
   - **Sprints CSV** – содержит информацию о спринтах.

2. Нажмите кнопку **"Загрузить данные"**.

### Шаг 2: Выбор спринтов
1. Выберите спринт для анализа через **выпадающий список**.
2. Можно выбрать до **четырех спринтов** для анализа одновременно.
3. Опционально выберите одну или несколько команд для сравнения.
4. Опционально выберите членов команды.

### Шаг 3: Просмотр аналитики
После нажатия кнопки **"Начать анализ"** доступны следующие параметры:

#### Визуализация:
- Распределение задач по статусам.
- Распределение задач по приоритетам.

#### Основные метрики:
- Общее количество задач.
- Суммарное время оценок задач.
- Количество задач в определенных статусах.

#### Диаграммы прогресса:
- **Burndown Chart** – прогресс выполнения задач.
- **Cumulative Flow Diagram** – изменение задач по статусам со временем.

## Важно
Перед началом работы убедитесь, что **Python** установлен на вашем компьютере и добавлен в системный **PATH**.  
При первом запуске рекомендуется подключение к интернету, чтобы программа могла автоматически установить недостающие библиотеки.

---

## Подготовка приложения
1. Переместите папку **SprintHealth** в любое удобное место (например, на рабочий стол для быстрого доступа).

---

## Запуск приложения
1. Откройте папку **SprintHealth**.
2. Запустите файл **SprintHealth_runner.py** – это основной скрипт для запуска приложения.

---

## Процессы в консоли
После запуска приложения откроется консоль, где выполняются следующие действия:

1. Программа проверяет наличие необходимых библиотек Python.
2. Если библиотек не хватает, они будут установлены автоматически.  
   Проверяемые библиотеки:
   - **Streamlit**
   - **Pandas**
   - **NumPy**
   - **Plotly**









