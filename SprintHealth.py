import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Установка ширины страницы и заголовка
st.set_page_config(layout="wide")
st.title("SprintHealth: инновационный анализ для Agile-команд")

# Инициализация состояния сессии
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = {}
if 'analyze' not in st.session_state:
    st.session_state['analyze'] = False

# Цветовая схема для статусов
status_colors = {
    "Закрыто": "#2E8B57",                # SeaGreen
    "Тестирование": "#FFD700",           # Gold
    "Выполнено": "#32CD32",              # LimeGreen
    "Создано": "#1E90FF",                # DodgerBlue
    "В работе": "#FFA500",               # Orange
    "Анализ": "#9370DB",                 # MediumPurple
    "Исправление": "#DC143C",            # Crimson
    "Отклонен исполнителями": "#FF69B4", # HotPink
    "Отложен": "#8B4513",                # SaddleBrown
    "Разработка": "#3CB371",             # MediumSeaGreen
    "В ожидании": "#A9A9A9"              # DarkGray
}

# Цветовая схема для приоритетов
priority_colors = {
    "Низкий": "#7FB3D5",      # Light Blue
    "Средний": "#F5B041",     # Orange
    "Высокий": "#EC7063",     # Red
    "Критический": "#AF7AC5"  # Purple
}

# Цветовая схема для сгруппированных статусов
status_group_colors = {
    "К выполнению": "#1E90FF", # DodgerBlue
    "В работе": "#FFA500",     # Orange
    "Сделано": "#32CD32"       # LimeGreen
}

# --- Вспомогательные функции и функции ЧД ---

# Функция для получения идентификаторов сущностей спринта
def get_entity_ids(sprint_number):
    s = sprints_df.loc[sprint_number, 'entity_ids']
    s = s[1:-1]
    nums = []
    num = ''
    for char in s:
        if char != ',':
            num += char
        else:
            nums.append(int(num))
            num = ''
    if num:
        nums.append(int(num))
    return nums

# Функция Заблокировано (ЧД/шт)
def blocked_per_day(sprint_number):
    sprint_start_date = pd.to_datetime(sprints_df.loc[sprint_number, 'sprint_start_date']).date()
    sprint_end_date = pd.to_datetime(sprints_df.loc[sprint_number, 'sprint_end_date']).date()
    date_range = pd.date_range(start=sprint_start_date, end=sprint_end_date)

    blocked_data = []
    for current_date in date_range:
        blocked_data.append({
            'Дата': current_date.date(),
            'Сумма оценок в часах': 0.0,  # Всегда ноль
            'Количество задач': 0,
            'Список задач': []
        })

    blocked_df = pd.DataFrame(blocked_data)
    return blocked_df

# Функция снято
def removed(num_of_sprint, entities_df):
    nums_list = get_entity_ids(num_of_sprint)
    removed_tasks = entities_df[
        (entities_df['entity_id'].isin(nums_list)) &
        (entities_df['status'].isin(['Закрыто', 'Выполнено'])) &
        (entities_df['resolution'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат']))
    ]['estimation'].sum() / 3600
    return round(removed_tasks, 3)

# Функция Исключено (Чд/шт)
def excluded(sprint_numb, sprints, history, entity):
    num_list = get_entity_ids(sprint_numb)

    dates = []
    date = sprints.loc[sprint_numb, 'sprint_start_date']
    sprint_end_date = sprints.loc[sprint_numb, 'sprint_end_date']
    while date <= sprint_end_date:
        dates.append(date)
        date += timedelta(days=1)

    # Список для хранения промежуточных данных
    all_results = []

    for elem in dates:
        morning = elem.replace(hour=0, minute=0, second=0, microsecond=0)
        night = elem.replace(hour=23, minute=59, second=59, microsecond=0)

        changes = history.loc[
            (pd.to_datetime(history['history_date']) < night) &
            (pd.to_datetime(history['history_date']) > morning) &
            (history['entity_id'].isin(num_list)) &
            (history['history_change_type'].isin(['FIELD_CHANGED']))
        ]

        changes['history_change_spl'] = changes['history_change'].apply(lambda x: str(x).split(' '))
        changes['history_change_spl'] = changes['history_change_spl'].apply(
            lambda x: True if any(word in str(x).lower() for word in ['готово', 'closed', 'снят', 'снято']) else False
        )

        changes = changes.loc[changes['history_change_spl'] == True]
        id_to_sum = changes.loc[:, 'entity_id']

        est_count = entity.loc[entity['entity_id'].isin(id_to_sum.tolist()), 'estimation'].sum()

        # Создание DataFrame для текущей даты
        df_1 = pd.DataFrame({'Дата': [elem],
                             'Сумма оценок в часах': [est_count / 3600],
                             'Количество задач': [id_to_sum.nunique()],
                             'Список задач': [id_to_sum.values]})

        # Добавляем текущий результат в список
        all_results.append(df_1)

    # Объединяем все промежуточные результаты в один DataFrame
    final_df = pd.concat(all_results, ignore_index=True)
    final_df['Дата'] = pd.to_datetime(final_df['Дата']).dt.date
    return final_df

# Функция Добавлено (ЧД/шт)
def added_per_day(num_of_sprint, sprints_df, history_df, entities_df):
    sprint_nums = get_entity_ids(num_of_sprint)

    sprint_start_date = pd.to_datetime(sprints_df.loc[num_of_sprint, 'sprint_start_date']).date()
    sprint_end_date = pd.to_datetime(sprints_df.loc[num_of_sprint, 'sprint_end_date']).date()

    date_range = pd.date_range(start=sprint_start_date, end=sprint_end_date)

    entity_date = entities_df.copy()
    entity_date['create_date'] = pd.to_datetime(entity_date['create_date']).dt.date

    added_data = []
    for current_date in date_range:
        current_date_date = current_date.date()

        if current_date == date_range[0]:
            added_entities = entity_date[
                (entity_date['entity_id'].isin(sprint_nums)) &
                (entity_date['create_date'] <= current_date_date)
            ]
        else:
            added_entities = entity_date[
                (entity_date['entity_id'].isin(sprint_nums)) &
                (entity_date['create_date'] == current_date_date)
            ]

        declined = history_df[
            (history_df['history_date'] == current_date_date) &
            (history_df['history_change'].str.contains('отклонен', case=False, na=False))
        ]['entity_id'].to_list()

        added_entities = added_entities[~added_entities['entity_id'].isin(declined)]
        # declined_ent = added_entities[added_entities['entity_id'].isin(declined)]

        total_added_estimation = added_entities['estimation'].sum() / 3600
        count_added = added_entities['entity_id'].nunique()

        added_data.append({
            'Дата': current_date_date,
            'Сумма оценок в часах': round(total_added_estimation, 3),
            'Количество задач': count_added,
            'Список задач': added_entities['entity_id'].to_list(),
        })

    added_df = pd.DataFrame(added_data)

    return added_df

# Функция для изменения статуса задачи при перемещении ползунка
def adjust_status(row, selected_date):
    status_order = [
        "Создано", "Анализ", "В ожидании", "В работе",
        "Разработка", "Исправление", "Тестирование",
        "Выполнено", "Закрыто", "Отклонен исполнителями", "Отложен"
    ]
    if pd.isna(row['update_date']):
        return row['status']
    if row['update_date'].date() <= selected_date:
        return row['status']
    try:
        current_index = status_order.index(row['status'])
        if current_index < len(status_order) - 1:
            return status_order[current_index + 1]
    except ValueError:
        pass
    return row['status']

# Функция для расчета Burndown Chart
def calculate_burndown(sprint_entities, sprint_start, sprint_end):
    # Общая оценка задач в спринте
    total_work = sprint_entities['estimation'].sum() / 3600  # в часах

    # Создание диапазона дат спринта
    date_range = pd.date_range(start=sprint_start.date(), end=sprint_end.date())

    burndown = []
    remaining_work = total_work

    for single_date in date_range:
        # Количество выполненной работы до текущей даты
        completed_work = sprint_entities[
            (sprint_entities['update_date'].dt.date <= single_date.date()) &
            (sprint_entities['status'].isin(['Закрыто', 'Выполнено']))
        ]['estimation'].sum() / 3600  # в часах
        remaining = total_work - completed_work
        remaining_work = max(remaining, 0)
        burndown.append({'date': single_date.date(), 'remaining_work': remaining_work})

    burndown_df = pd.DataFrame(burndown)
    return burndown_df

# Функция для расчета BurnUp Chart
def calculate_burnup(sprint_entities, sprint_start, sprint_end):
    # Общая оценка задач в спринте
    total_work = sprint_entities['estimation'].sum() / 3600  # в часах

    # Создание диапазона дат спринта
    date_range = pd.date_range(start=sprint_start.date(), end=sprint_end.date())

    burnup = []
    completed_work = 0

    for single_date in date_range:
        # Количество выполненной работы до текущей даты
        daily_completed = sprint_entities[
            (sprint_entities['update_date'].dt.date <= single_date.date()) &
            (sprint_entities['status'].isin(['Закрыто', 'Выполнено']))
        ]['estimation'].sum() / 3600  # в часах
        completed_work = max(daily_completed, 0)
        burnup.append({'date': single_date.date(), 'completed_work': completed_work})

    burnup_df = pd.DataFrame(burnup)
    burnup_df['total_work'] = total_work

    return burnup_df

# Функция для расчета задач, не завершённых в спринте
def calculate_uncompleted_tasks(sprint_entities, sprint_start, sprint_end):
    uncompleted = sprint_entities[~sprint_entities['status'].isin(['Закрыто', 'Выполнено'])]
    total_uncompleted = uncompleted['estimation'].sum() / 3600  # в часах
    percentage_uncompleted = (total_uncompleted / (sprint_entities['estimation'].sum() / 3600)) * 100 if sprint_entities['estimation'].sum() > 0 else 0
    # Добавление новых колонок
    uncompleted = uncompleted.copy()
    uncompleted['percent_complete'] = 100 * (uncompleted['estimation'] - uncompleted['spent']) / uncompleted['estimation']
    uncompleted['percent_remaining'] = 100 - uncompleted['percent_complete']
    uncompleted['hours_complete'] = uncompleted['spent']
    uncompleted['hours_remaining'] = uncompleted['estimation'] - uncompleted['spent']
    return uncompleted, total_uncompleted, percentage_uncompleted

# Функция для расчета Cumulative Flow Diagram
def calculate_cfd(sprint_entities, sprint_start, sprint_end):
    date_range = pd.date_range(start=sprint_start.date(), end=sprint_end.date())
    statuses = ['Создано', 'Анализ', 'В ожидании', 'В работе', 'Разработка', 'Исправление',
                'Тестирование', 'Выполнено', 'Закрыто', 'Отклонен исполнителями', 'Отложен']
    cfd = pd.DataFrame({'date': date_range})

    for status in statuses:
        cfd[status] = 0

    for single_date in date_range:
        for status in statuses:
            count = sprint_entities[
                (sprint_entities['adjusted_status'] == status) &
                (sprint_entities['create_date'].dt.date <= single_date.date()) &
                (sprint_entities['update_date'].dt.date >= single_date.date())
            ].shape[0]
            cfd.loc[cfd['date'] == single_date, status] = count

    return cfd

# Функция для расчета сгруппированного CFD
def calculate_grouped_cfd(sprint_entities, sprint_start, sprint_end):
    date_range = pd.date_range(start=sprint_start.date(), end=sprint_end.date())
    status_group_mapping = {
        "Создано": "К выполнению",
        "Анализ": "К выполнению",
        "В ожидании": "К выполнению",
        "Отложен": "К выполнению",
        "В работе": "В работе",
        "Разработка": "В работе",
        "Исправление": "В работе",
        "Тестирование": "В работе",
        "Выполнено": "Сделано",
        "Закрыто": "Сделано",
        "Отклонен исполнителями": "Сделано"
    }
    sprint_entities['status_group'] = sprint_entities['adjusted_status'].map(status_group_mapping)
    groups = ['К выполнению', 'В работе', 'Сделано']
    cfd = pd.DataFrame({'date': date_range})

    for group in groups:
        cfd[group] = 0

    for single_date in date_range:
        for group in groups:
            count = sprint_entities[
                (sprint_entities['status_group'] == group) &
                (sprint_entities['create_date'].dt.date <= single_date.date()) &
                (sprint_entities['update_date'].dt.date >= single_date.date())
            ].shape[0]
            cfd.loc[cfd['date'] == single_date, group] = count

    return cfd

# Функция для создания временной шкалы (Timeline)
def create_timeline(sprint_entities, sprint_start, sprint_end, sprint_name):
    # Генерация диапазона дат
    date_range = pd.date_range(start=sprint_start.date(), end=sprint_end.date())

    timeline_data = []
    for date in date_range:
        day_data = {
            "date": date,
            "added": sprint_entities[sprint_entities['create_date'].dt.date == date.date()].shape[0],
            "removed": sprint_entities[
                (sprint_entities['update_date'].dt.date == date.date()) &
                (sprint_entities['status'].isin(['Отклонен исполнителями', 'Отложен']))
            ].shape[0],
            "blocked": sprint_entities[
                (sprint_entities['status'] == 'Заблокировано') &
                (sprint_entities['update_date'].dt.date == date.date())
            ].shape[0],
        }
        timeline_data.append(day_data)

    timeline_df = pd.DataFrame(timeline_data)

    # Построение графика
    fig = go.Figure()
    fig.add_trace(go.Bar(x=timeline_df['date'], y=timeline_df['added'], name="Добавлено", marker_color='#32CD32'))
    fig.add_trace(go.Bar(x=timeline_df['date'], y=timeline_df['removed'], name="Удалено", marker_color='#DC143C'))
    fig.add_trace(go.Bar(x=timeline_df['date'], y=timeline_df['blocked'], name="Заблокировано", marker_color='#FFD700'))

    fig.update_layout(barmode='stack', title=f"Временная шкала для {sprint_name}",
                      xaxis_title="Дата", yaxis_title="Количество задач",
                      legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.5)'),
                      hovermode='x unified')

    return fig

# Функция для расчета доли всех задач в 10% родительских задач (среднее по всем спринтам)
def all_sprints_parent_ids(sprints, entity):
    all_sprints_amount = sprints.shape[0]
    av_num, av_est = [], []
    for sprint_numb in range(all_sprints_amount):
        num_list = get_entity_ids(sprint_numb)
        parent_ids = entity.loc[entity['entity_id'].isin(num_list), 'parent_ticket_id'].unique()
        df_1 = pd.DataFrame(columns = ['parent_id', 'num_tasks', 'estimation'])
        for i, elem in enumerate(parent_ids):
            df_1.loc[i, 'parent_id'] = elem
            df_1.loc[i, 'num_tasks'] = entity.loc[entity['parent_ticket_id']==elem, 'entity_id'].nunique()
            df_1.loc[i, 'estimation'] = entity.loc[entity['parent_ticket_id']==elem, 'estimation'].sum() / 3600
        df_1 = df_1.dropna().sort_values(by=['num_tasks'], ascending=False)
        twenty_perc = int(df_1.shape[0] * 0.2)
        perc_of_numb = df_1.iloc[:twenty_perc, 1].sum() / df_1['num_tasks'].sum()
        perc_of_estimation = df_1.iloc[:twenty_perc, 2].sum() / df_1['estimation'].sum()
        av_num.append(perc_of_numb)
        av_est.append(perc_of_estimation)
    return av_num, av_est

def one_sprint_parent_ids(sprint_numb, entity):
    num_list = get_entity_ids(sprint_numb)
    parent_ids = entity.loc[entity['entity_id'].isin(num_list), 'parent_ticket_id'].unique()
    df_1 = pd.DataFrame(columns = ['parent_id', 'num_tasks', 'estimation'])
    for i, elem in enumerate(parent_ids):
        df_1.loc[i, 'parent_id'] = elem
        df_1.loc[i, 'num_tasks'] = entity.loc[entity['parent_ticket_id']==elem, 'entity_id'].nunique()
        df_1.loc[i, 'estimation'] = entity.loc[entity['parent_ticket_id']==elem, 'estimation'].sum() / 3600
    return df_1.dropna()

# Функция для отображения документации
def show_documentation():
    with st.expander("Документация", expanded=False):
        st.markdown("""
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

# Этап 1: Загрузка данных с использованием аккордеона
with st.sidebar.expander("Настройки", expanded=True):
    # Этап 1: Загрузка файла
    st.markdown("#### Этап 1: Загрузка файлов")
    uploaded_entities = st.file_uploader("Загрузите файл Entities CSV", type="csv")
    uploaded_history = st.file_uploader("Загрузите файл History CSV", type="csv")
    uploaded_sprints = st.file_uploader("Загрузите файл Sprints CSV", type="csv")

    k_vypolneniyu = st.number_input("К выполнению", value=20)
    snyato = st.number_input("Снято", value=10)
    backlog_range = st.number_input("Граница бэклога", value=20)

    if uploaded_entities and uploaded_history and uploaded_sprints:
        # Загрузка данных
        entities_df = pd.read_csv(uploaded_entities, sep=';', skiprows=1, on_bad_lines='skip')
        history_df = pd.read_csv(uploaded_history, sep=';', skiprows=1, on_bad_lines='skip')
        sprints_df = pd.read_csv(uploaded_sprints, sep=';', skiprows=1, on_bad_lines='skip')

        # Преобразование дат в datetime формат
        entities_df['create_date'] = pd.to_datetime(entities_df['create_date'], errors='coerce')
        entities_df['update_date'] = pd.to_datetime(entities_df['update_date'], errors='coerce')
        sprints_df['sprint_start_date'] = pd.to_datetime(sprints_df['sprint_start_date'], errors='coerce')
        sprints_df['sprint_end_date'] = pd.to_datetime(sprints_df['sprint_end_date'], errors='coerce')
        history_df['history_date'] = pd.to_datetime(history_df['history_date'], errors='coerce')

        st.success("Файлы успешно загружены и обработаны.")
        st.info("Перейдите к следующему этапу для выбора спринтов.")

        # Этап 2: Выбор спринтов
        st.markdown("#### Этап 2: Выбор спринтов")
        sprint_options = sprints_df['sprint_name'].unique()
        selected_sprints = st.multiselect("Выберите спринты для анализа", sprint_options, key="selected_sprints")

        if len(selected_sprints) > 4:
            st.error("Можно выбрать не более 4 спринтов.")
            selected_sprints = selected_sprints[:4]

        if selected_sprints:
            # Этап 3: Выбор команд и исполнителей
            st.markdown("#### Этап 3: Выбор команд и исполнителей")
            sprint_data = {}

            for sprint_name in selected_sprints:
                sprint_number = sprints_df.loc[sprints_df['sprint_name'] == sprint_name].index[0]
                sprint_row = sprints_df[sprints_df['sprint_name'] == sprint_name].iloc[0]
                sprint_entity_ids = sprint_row['entity_ids'].strip('{}').split(',')
                sprint_entity_ids = [id.strip() for id in sprint_entity_ids]
                sprint_entities = entities_df[entities_df['entity_id'].astype(str).isin(sprint_entity_ids)]

                # Шаг 1: Выбор команд (area)
                areas_with_tasks = sprint_entities['area'].dropna().unique().tolist()
                areas_with_tasks = sorted(areas_with_tasks)
                areas_with_all = ['Все'] + areas_with_tasks

                selected_areas = st.multiselect(
                    f"Выберите команды (area) для спринта {sprint_name}",
                    options=areas_with_all,
                    default=['Все'],
                    key=f"areas_{sprint_name}"
                )

                if 'Все' in selected_areas or not selected_areas:
                    filtered_entities_by_area = sprint_entities
                else:
                    filtered_entities_by_area = sprint_entities[sprint_entities['area'].isin(selected_areas)]

                # Шаг 2: Выбор исполнителей (assignee) на основе выбранных команд
                assignees_with_tasks = filtered_entities_by_area['assignee'].dropna().unique().tolist()
                assignees_with_tasks = sorted(assignees_with_tasks)
                assignees_with_all = ['Все'] + assignees_with_tasks

                selected_assignees = st.multiselect(
                    f"Выберите исполнителей для спринта {sprint_name}",
                    options=assignees_with_all,
                    default=['Все'],
                    key=f"assignees_{sprint_name}"
                )

                if 'Все' in selected_assignees or not selected_assignees:
                    final_filtered_entities = filtered_entities_by_area
                else:
                    final_filtered_entities = filtered_entities_by_area[filtered_entities_by_area['assignee'].isin(selected_assignees)]

                # Сохранение отфильтрованных данных для спринта
                sprint_data[sprint_name] = final_filtered_entities

            st.info("Все этапы настройки завершены. Нажмите кнопку ниже для начала анализа.")

            # Этап 4: Подтверждение настроек и запуск анализа
            st.markdown("#### Этап 4: Подтверждение и запуск анализа")
            if st.button("Начать анализ"):
                st.session_state['analyze'] = True
                st.success("Анализ начался!")
            else:
                st.session_state['analyze'] = False
    else:
        st.warning("Пожалуйста, загрузите все необходимые файлы для продолжения.")

# Отображение документации через кнопку
if st.sidebar.button("Документация"):
    show_documentation()

# Проверка, нажата ли кнопка "Начать анализ"
if st.session_state['analyze'] and 'selected_sprints' in st.session_state:
    selected_sprints = st.session_state['selected_sprints']
    # Основной контент
    st.subheader("Результаты анализа")

    # Колонки для спринтов
    cols = st.columns(len(selected_sprints))

    for idx, sprint_name in enumerate(selected_sprints):
        with cols[idx]:
            # Определение номера спринта
            sprint_number = sprints_df.loc[sprints_df['sprint_name'] == sprint_name].index[0]
            sprint_row = sprints_df[sprints_df['sprint_name'] == sprint_name].iloc[0]
            sprint_entity_ids = sprint_row['entity_ids'].strip('{}').split(',')
            sprint_entity_ids = [id.strip() for id in sprint_entity_ids]
            full_sprint_entities = entities_df[entities_df['entity_id'].astype(str).isin(sprint_entity_ids)]

            # Фильтрация данных на основе выбранных команд и исполнителей
            sprint_entities = sprint_data[sprint_name]
            sprint_start = sprints_df[sprints_df['sprint_name'] == sprint_name]['sprint_start_date'].iloc[0]
            sprint_end = sprints_df[sprints_df['sprint_name'] == sprint_name]['sprint_end_date'].iloc[0]

            if sprint_name not in st.session_state['selected_date']:
                st.session_state['selected_date'][sprint_name] = sprint_end.date()

            selected_date = st.session_state['selected_date'][sprint_name]
            # Слайдер для выбора даты
            st.markdown(
                f"""
                <div style="text-align: center; font-size: 27px; font-weight: bold; margin-bottom: 10px;">
                    Срок спринта
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 20px;">{sprint_start.date()}</span>
                    <div style="flex-grow: 1; height: 3px; background: #32CD32; margin: 0 10px;"></div>
                    <span style="font-weight: bold; font-size: 20px;">{sprint_end.date()}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.session_state['selected_date'][sprint_name] = selected_date

            # Применение функции изменения статуса для полного набора данных
            full_sprint_entities = full_sprint_entities.copy()
            full_sprint_entities['adjusted_status'] = full_sprint_entities.apply(adjust_status, args=(selected_date,), axis=1)

            # Группировка статусов
            status_group_mapping = {
                "Создано": "К выполнению",
                "Анализ": "К выполнению",
                "В ожидании": "К выполнению",
                "Отложен": "К выполнению",
                "В работе": "В работе",
                "Разработка": "В работе",
                "Исправление": "В работе",
                "Тестирование": "В работе",
                "Выполнено": "Сделано",
                "Закрыто": "Сделано",
                "Отклонен исполнителями": "Сделано"
            }
            full_sprint_entities['status_group'] = full_sprint_entities['adjusted_status'].map(status_group_mapping)

            # Основные параметры
            st.markdown("#### Основные параметры")

            # Метрики "К выполнению", "В работе", "Сделано" для полного спринта
            group_metrics = {}
            total_estimation = full_sprint_entities['estimation'].sum() / 3600  # Общий объем

            for group in ["К выполнению", "В работе", "Сделано"]:
                group_sum = full_sprint_entities[full_sprint_entities['status_group'] == group]['estimation'].sum() / 3600
                group_metrics[group] = round(group_sum, 1)

            # Метрика "Снято"
            group_metrics["Снято"] = round(removed(sprint_number, entities_df), 1)

            # Вычисление процентов для проверки условий
            to_do_percentage = (group_metrics['К выполнению'] / total_estimation) * 100 if total_estimation > 0 else 0
            removed_percentage = (group_metrics['Снято'] / total_estimation) * 100 if total_estimation > 0 else 0

            # Проверка условий и установка цветов
            red_conditions = {
                'to_do': to_do_percentage > k_vypolneniyu,
                'removed': removed_percentage > snyato,
                'backlog': False  # Определим ниже
            }

            # Расчет бэклога изменен
            # Исключаем дефекты
            non_defects = full_sprint_entities[~full_sprint_entities['status'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат', 'Отклонен исполнителями'])]
            tasks_before_start = non_defects[non_defects['create_date'] <= (sprint_start + pd.Timedelta(days=2))]
            tasks_after_start = non_defects[non_defects['create_date'] > (sprint_start + pd.Timedelta(days=2))]

            backlog_change = 0
            if not tasks_before_start.empty and tasks_before_start['estimation'].sum() > 0:
                backlog_change = (tasks_after_start['estimation'].sum() / tasks_before_start['estimation'].sum()) * 100

            if backlog_change > backlog_range:
                red_conditions['backlog'] = True

            # Определение цвета для названия спринта
            red_count = sum(red_conditions.values())
            if red_count == 0:
                sprint_color = "green"
            elif red_count == 1 or red_count == 2:
                sprint_color = "orange"
            else:
                sprint_color = "red"

            st.markdown(f"<h3 style='color: {sprint_color};'><strong>{sprint_name}</strong></h3>", unsafe_allow_html=True)

            # Вывод метрик с подсветкой
            metric_cols = st.columns(4)
            # Определение цветов для метрик
            to_do_color = "red" if red_conditions['to_do'] else "green"
            removed_color = "red" if red_conditions['removed'] else "green"
            backlog_color = "red" if red_conditions['backlog'] else "green"

            # Метрики
            with metric_cols[0]:
                st.markdown(f"**К выполнению (Человеко-часы)**")
                st.markdown(f"<h2 style='color: {to_do_color};'>{group_metrics['К выполнению']} ({to_do_percentage:.1f}%)</h2>", unsafe_allow_html=True)
            with metric_cols[1]:
                st.markdown(f"**В работу (Человеко-часы)**")
                st.markdown(f"<h2 style='color: black;'>{group_metrics['В работе']}</h2>", unsafe_allow_html=True)
            with metric_cols[2]:
                st.markdown(f"**Сделано (Человеко-часы)**")
                st.markdown(f"<h2 style='color: black;'>{group_metrics['Сделано']}</h2>", unsafe_allow_html=True)
            with metric_cols[3]:
                st.markdown(f"**Снято (Человеко-часы)**")
                st.markdown(f"<h2 style='color: {removed_color};'>{group_metrics['Снято']} ({removed_percentage:.1f}%)</h2>", unsafe_allow_html=True)

            # Метрики человека-дни
            with metric_cols[0]:
                st.markdown(f"**К выполнению (Человеко-дни)**")
                st.markdown(f"<h2 style='color: {to_do_color};'>{round(group_metrics['К выполнению'] / 24, 2)} ({to_do_percentage:.1f}%)</h2>", unsafe_allow_html=True)
            with metric_cols[1]:
                st.markdown(f"**В работу (Человеко-дни)**")
                st.markdown(f"<h2 style='color: black;'>{round(group_metrics['В работе'] / 24, 2)}</h2>", unsafe_allow_html=True)
            with metric_cols[2]:
                st.markdown(f"**Сделано (Человеко-дни)**")
                st.markdown(f"<h2 style='color: black;'>{round(group_metrics['Сделано'] / 24, 2)}</h2>", unsafe_allow_html=True)
            with metric_cols[3]:
                st.markdown(f"**Снято (Человеко-дни)**")
                st.markdown(f"<h2 style='color: {removed_color};'>{round(group_metrics['Снято'] / 24, 2)} ({removed_percentage:.1f}%)</h2>", unsafe_allow_html=True)

            # Пояснения для стрелочек
            st.info("Цвет показателя отображает его влияние на здоровье спринта")

            # Бэклог изменен
            st.markdown("#### Бэклог изменен (%)")
            st.markdown(f"<h2 style='color: {backlog_color};'>{backlog_change:.1f}%</h2>", unsafe_allow_html=True)
            st.info("Бэклог изменился на определенный процент после начала спринта.")

            # Вывод заключения по спринту
            if sprint_color == 'green':
                st.markdown("<p style='color: green;'>Команда хорошо справилась со спринтом.</p>", unsafe_allow_html=True)
            elif sprint_color == 'orange':
                st.markdown("<p style='color: orange;'>Команда средне справилась со спринтом.</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: red;'>Команде необходимо улучшить показатели в спринте.</p>", unsafe_allow_html=True)

            # Теперь работаем с отфильтрованными данными
            sprint_entities = sprint_entities.copy()
            sprint_entities['adjusted_status'] = sprint_entities.apply(adjust_status, args=(selected_date,), axis=1)
            sprint_entities['status_group'] = sprint_entities['adjusted_status'].map(status_group_mapping)

            # Добавляем расчет cycle_time для всех задач
            sprint_entities['cycle_time'] = (sprint_entities['update_date'] - sprint_entities['create_date']).dt.total_seconds() / 3600

            # ------------------ Реализация метрик по командам ------------------

            # Получение выбранных команд
            selected_areas = st.session_state.get(f"areas_{sprint_name}", ['Все'])
            if 'Все' in selected_areas or not selected_areas:
                teams_to_analyze = sprint_entities['area'].dropna().unique().tolist()
            else:
                teams_to_analyze = selected_areas

            if teams_to_analyze:
                with st.expander("**Метрики по командам**", expanded=False):
                    num_teams = len(teams_to_analyze)
                    team_cols = st.columns(num_teams)
                    for idx, team in enumerate(teams_to_analyze):
                        with team_cols[idx]:
                            team_entities = sprint_entities[sprint_entities['area'] == team]
                            if team_entities.empty:
                                continue  # Пропустить, если нет задач для команды

                            team_entities['adjusted_status'] = team_entities.apply(adjust_status, args=(selected_date,), axis=1)
                            team_entities['status_group'] = team_entities['adjusted_status'].map(status_group_mapping)

                            # Расчет метрик для команды
                            team_group_metrics = {}
                            team_total_estimation = team_entities['estimation'].sum() / 3600  # Общий объем

                            for group in ["К выполнению", "В работе", "Сделано"]:
                                group_sum = team_entities[team_entities['status_group'] == group]['estimation'].sum() / 3600
                                team_group_metrics[group] = round(group_sum, 1)

                            # Расчет "Снято" для команды
                            removed_tasks = team_entities[
                                (team_entities['status'].isin(['Закрыто', 'Выполнено'])) &
                                (team_entities['resolution'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат']))
                            ]['estimation'].sum() / 3600
                            team_group_metrics["Снято"] = round(removed_tasks, 1)

                            # Вычисление процентов и условий для команды
                            to_do_percentage = (team_group_metrics['К выполнению'] / team_total_estimation) * 100 if team_total_estimation > 0 else 0
                            removed_percentage = (team_group_metrics['Снято'] / team_total_estimation) * 100 if team_total_estimation > 0 else 0

                            # Проверка условий и установка цветов
                            red_conditions = {
                                'to_do': to_do_percentage > 20,
                                'removed': removed_percentage > 10,
                                'backlog': False  # Определим ниже
                            }

                            # Расчет бэклога изменен для команды
                            non_defects = team_entities[~team_entities['status'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат', 'Отклонен исполнителями'])]
                            tasks_before_start = non_defects[non_defects['create_date'] <= (sprint_start + pd.Timedelta(days=2))]
                            tasks_after_start = non_defects[non_defects['create_date'] > (sprint_start + pd.Timedelta(days=2))]

                            backlog_change_team = 0
                            if not tasks_before_start.empty and tasks_before_start['estimation'].sum() > 0:
                                backlog_change_team = (tasks_after_start['estimation'].sum() / tasks_before_start['estimation'].sum()) * 100

                            if backlog_change_team > 20:
                                red_conditions['backlog'] = True

                            # Определение цвета для названия команды
                            red_count = sum(red_conditions.values())
                            if red_count == 0:
                                team_color = "green"
                            elif red_count == 1 or red_count == 2:
                                team_color = "orange"
                            else:
                                team_color = "red"

                            st.markdown(f"<h4 style='color: {team_color};'><strong>{team}</strong></h4>", unsafe_allow_html=True)

                            # Вывод метрик для команды
                            # Определение цветов для метрик
                            to_do_color = "red" if red_conditions['to_do'] else "green"
                            removed_color = "red" if red_conditions['removed'] else "green"
                            backlog_color = "red" if red_conditions['backlog'] else "green"

                            st.markdown(f"**К выполнению (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: {to_do_color};'>{team_group_metrics['К выполнению']} ({to_do_percentage:.1f}%)</h2>", unsafe_allow_html=True)
                            st.markdown(f"**В работу (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: black;'>{team_group_metrics['В работе']}</h2>", unsafe_allow_html=True)
                            st.markdown(f"**Сделано (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: black;'>{team_group_metrics['Сделано']}</h2>", unsafe_allow_html=True)
                            st.markdown(f"**Снято (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: {removed_color};'>{team_group_metrics['Снято']} ({removed_percentage:.1f}%)</h2>", unsafe_allow_html=True)
                            st.markdown("**Бэклог изменен (%)**")
                            st.markdown(f"<h2 style='color: {backlog_color};'>{backlog_change_team:.1f}%</h2>", unsafe_allow_html=True)

                            # Вывод заключения по команде
                            if team_color == 'green':
                                st.markdown("<p style='color: green;'>Команда хорошо справилась со спринтом.</p>", unsafe_allow_html=True)
                            elif team_color == 'orange':
                                st.markdown("<p style='color: orange;'>Команда средне справилась со спринтом.</p>", unsafe_allow_html=True)
                            else:
                                st.markdown("<p style='color: red;'>Команде необходимо улучшить показатели в спринте.</p>", unsafe_allow_html=True)

                    # Сравнение команд внутри спринта
                    if len(teams_to_analyze) > 1:
                        st.markdown("#### Сравнение команд")

                        # Сбор данных для сравнения
                        comparison_data = []
                        for team in teams_to_analyze:
                            team_entities = sprint_entities[sprint_entities['area'] == team]
                            if team_entities.empty:
                                continue

                            team_entities['adjusted_status'] = team_entities.apply(adjust_status, args=(selected_date,), axis=1)
                            team_entities['status_group'] = team_entities['adjusted_status'].map(status_group_mapping)

                            # Расчет "Сделано" для команды
                            done_estimation = team_entities[team_entities['status_group'] == 'Сделано']['estimation'].sum() / 3600
                            comparison_data.append({'team': team, 'done_estimation': done_estimation})

                        comparison_df = pd.DataFrame(comparison_data)

                        # Построение графика
                        fig_team_comparison = go.Figure(data=[go.Bar(
                            x=comparison_df['team'],
                            y=comparison_df['done_estimation'],
                            marker_color='indianred',
                            hoverinfo='x+y',
                            hovertemplate='%{x}: %{y} Часов'
                        )])
                        fig_team_comparison.update_layout(title="Сделано по командам", xaxis_title="Команда", yaxis_title="Сделано (Человеко-часы)")
                        st.plotly_chart(fig_team_comparison, use_container_width=True)

                        # Определение лучшей команды
                        best_team_row = comparison_df.loc[comparison_df['done_estimation'].idxmax()]
                        best_team = best_team_row['team']
                        st.markdown(f"**Лучшая команда в этом спринте:** {best_team}")

                        # Информационное окно
                        st.info("Этот график показывает количество выполненной работы (в часах) каждой команды. Лучшая команда определяется по наибольшему объёму выполненной работы.")

            # ------------------ Реализация метрик по исполнителям ------------------

            # Получение выбранных исполнителей
            selected_assignees = st.session_state.get(f"assignees_{sprint_name}", ['Все'])
            show_assignee_metrics = False
            if ('Все' not in selected_areas) or ('Все' not in selected_assignees):
                show_assignee_metrics = True

            if show_assignee_metrics:
                with st.expander("**Метрики по исполнителям**", expanded=False):
                    assignees_to_analyze = sprint_entities['assignee'].dropna().unique().tolist()
                    num_assignees = len(assignees_to_analyze)
                    assignee_cols = st.columns(num_assignees)
                    for idx, assignee in enumerate(assignees_to_analyze):
                        with assignee_cols[idx]:
                            assignee_entities = sprint_entities[sprint_entities['assignee'] == assignee]
                            if assignee_entities.empty:
                                continue  # Пропустить, если нет задач для исполнителя

                            assignee_entities['adjusted_status'] = assignee_entities.apply(adjust_status, args=(selected_date,), axis=1)
                            assignee_entities['status_group'] = assignee_entities['adjusted_status'].map(status_group_mapping)

                            # Расчет метрик для исполнителя
                            assignee_group_metrics = {}
                            assignee_total_estimation = assignee_entities['estimation'].sum() / 3600  # Общий объем

                            for group in ["К выполнению", "В работе", "Сделано"]:
                                group_sum = assignee_entities[assignee_entities['status_group'] == group]['estimation'].sum() / 3600
                                assignee_group_metrics[group] = round(group_sum, 1)

                            # Расчет "Снято" для исполнителя
                            removed_tasks = assignee_entities[
                                (assignee_entities['status'].isin(['Закрыто', 'Выполнено'])) &
                                (assignee_entities['resolution'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат']))
                            ]['estimation'].sum() / 3600
                            assignee_group_metrics["Снято"] = round(removed_tasks, 1)

                            # Вычисление процентов и условий для исполнителя
                            to_do_percentage = (assignee_group_metrics['К выполнению'] / assignee_total_estimation) * 100 if assignee_total_estimation > 0 else 0
                            removed_percentage = (assignee_group_metrics['Снято'] / assignee_total_estimation) * 100 if assignee_total_estimation > 0 else 0

                            # Проверка условий и установка цветов
                            red_conditions = {
                                'to_do': to_do_percentage > 20,
                                'removed': removed_percentage > 10,
                                'backlog': False  # Определим ниже
                            }

                            # Расчет бэклога изменен для исполнителя
                            non_defects = assignee_entities[~assignee_entities['status'].isin(['Отклонено', 'Отменено инициатором', 'Дубликат', 'Отклонен исполнителями'])]
                            tasks_before_start = non_defects[non_defects['create_date'] <= (sprint_start + pd.Timedelta(days=2))]
                            tasks_after_start = non_defects[non_defects['create_date'] > (sprint_start + pd.Timedelta(days=2))]

                            backlog_change_assignee = 0
                            if not tasks_before_start.empty and tasks_before_start['estimation'].sum() > 0:
                                backlog_change_assignee = (tasks_after_start['estimation'].sum() / tasks_before_start['estimation'].sum()) * 100

                            if backlog_change_assignee > 20:
                                red_conditions['backlog'] = True

                            # Определение цвета для названия исполнителя
                            red_count = sum(red_conditions.values())
                            if red_count == 0:
                                assignee_color = "green"
                            elif red_count == 1 or red_count == 2:
                                assignee_color = "orange"
                            else:
                                assignee_color = "red"

                            st.markdown(f"<h4 style='color: {assignee_color};'><strong>{assignee}</strong></h4>", unsafe_allow_html=True)

                            # Вывод метрик для исполнителя
                            # Определение цветов для метрик
                            to_do_color = "red" if red_conditions['to_do'] else "green"
                            removed_color = "red" if red_conditions['removed'] else "green"
                            backlog_color = "red" if red_conditions['backlog'] else "green"

                            st.markdown(f"**К выполнению (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: {to_do_color};'>{assignee_group_metrics['К выполнению']} ({to_do_percentage:.1f}%)</h2>", unsafe_allow_html=True)
                            st.markdown(f"**В работу (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: black;'>{assignee_group_metrics['В работе']}</h2>", unsafe_allow_html=True)
                            st.markdown(f"**Сделано (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: black;'>{assignee_group_metrics['Сделано']}</h2>", unsafe_allow_html=True)
                            st.markdown(f"**Снято (Человеко-часы)**")
                            st.markdown(f"<h2 style='color: {removed_color};'>{assignee_group_metrics['Снято']} ({removed_percentage:.1f}%)</h2>", unsafe_allow_html=True)
                            st.markdown("**Бэклог изменен (%)**")
                            st.markdown(f"<h2 style='color: {backlog_color};'>{backlog_change_assignee:.1f}%</h2>", unsafe_allow_html=True)

                            # Вывод заключения по исполнителю
                            if assignee_color == 'green':
                                st.markdown("<p style='color: green;'>Исполнитель хорошо справился со спринтом.</p>", unsafe_allow_html=True)
                            elif assignee_color == 'orange':
                                st.markdown("<p style='color: orange;'>Исполнитель средне справился со спринтом.</p>", unsafe_allow_html=True)
                            else:
                                st.markdown("<p style='color: red;'>Исполнителю необходимо улучшить показатели в спринте.</p>", unsafe_allow_html=True)

                    # Сравнение исполнителей внутри спринта
                    if len(assignees_to_analyze) > 1:
                        st.markdown("#### Сравнение исполнителей")

                        # Сбор данных для сравнения
                        assignee_comparison_data = []
                        for assignee in assignees_to_analyze:
                            assignee_entities = sprint_entities[sprint_entities['assignee'] == assignee]
                            if assignee_entities.empty:
                                continue

                            assignee_entities['adjusted_status'] = assignee_entities.apply(adjust_status, args=(selected_date,), axis=1)
                            assignee_entities['status_group'] = assignee_entities['adjusted_status'].map(status_group_mapping)

                            # Расчет "Сделано" для исполнителя
                            done_estimation = assignee_entities[assignee_entities['status_group'] == 'Сделано']['estimation'].sum() / 3600
                            assignee_comparison_data.append({'assignee': assignee, 'done_estimation': done_estimation})

                        assignee_comparison_df = pd.DataFrame(assignee_comparison_data)

                        # Построение графика
                        fig_assignee_comparison = go.Figure(data=[go.Bar(
                            x=assignee_comparison_df['assignee'],
                            y=assignee_comparison_df['done_estimation'],
                            marker_color='indianred',
                            hoverinfo='x+y',
                            hovertemplate='%{x}: %{y} Часов'
                        )])
                        fig_assignee_comparison.update_layout(title="Сделано по исполнителям", xaxis_title="Исполнитель", yaxis_title="Сделано (Часов)")
                        st.plotly_chart(fig_assignee_comparison, use_container_width=True)

                        # Определение лучшего исполнителя
                        best_assignee_row = assignee_comparison_df.loc[assignee_comparison_df['done_estimation'].idxmax()]
                        best_assignee = best_assignee_row['assignee']
                        st.markdown(f"**Лучший исполнитель в этом спринте:** {best_assignee}")

                        # Информационное окно
                        st.info("Этот график показывает количество выполненной работы (в часах) каждым исполнителем. Лучший исполнитель определяется по наибольшему объёму выполненной работы.")

            # Продолжение основного анализа...

            # Распределение статусов задач
            with st.expander("**Распределение статусов задач**", expanded=False):
                status_counts = sprint_entities['adjusted_status'].value_counts().reindex(status_colors.keys(), fill_value=0)
                status_labels = status_counts.index.tolist()
                status_values = status_counts.values.tolist()
                fig_status = go.Figure(data=[go.Pie(
                    labels=status_labels,
                    values=status_values,
                    hoverinfo='label+percent',
                    textinfo='value',
                    marker=dict(colors=[status_colors[status] for status in status_labels]),
                    hovertemplate='%{label}: %{percent} (%{value} задач)'
                )])
                fig_status.update_layout(title="Распределение статусов задач")
                st.plotly_chart(fig_status, use_container_width=True)

                st.info("Этот график показывает распределение задач по статусам.")

            # Группировка статусов
            with st.expander("**Распределение статусов (сгруппировано)**", expanded=False):
                status_group_counts = sprint_entities['status_group'].value_counts()
                status_group_labels = status_group_counts.index.tolist()
                status_group_values = status_group_counts.values.tolist()
                fig_status_grouped = go.Figure(data=[go.Pie(
                    labels=status_group_labels,
                    values=status_group_values,
                    hoverinfo='label+percent',
                    textinfo='value',
                    marker=dict(colors=[status_group_colors.get(group, '#000000') for group in status_group_labels]),
                    hovertemplate='%{label}: %{percent} (%{value} задач)'
                )])
                fig_status_grouped.update_layout(title="Распределение задач по категориям")
                st.plotly_chart(fig_status_grouped, use_container_width=True)

                st.info("Этот график показывает распределение задач по сгруппированным категориям статусов.")

            # Распределение приоритетов
            with st.expander("**Распределение приоритетов**", expanded=False):
                priority_counts = sprint_entities['priority'].value_counts().reindex(priority_colors.keys(), fill_value=0)
                fig_priority = go.Figure(data=[go.Bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    marker_color=[priority_colors[priority] for priority in priority_counts.index],
                    hoverinfo='x+y',
                    hovertemplate='%{x}: %{y} задач'
                )])
                fig_priority.update_layout(title="Количество задач по приоритетам", xaxis_title="Приоритет", yaxis_title="Количество задач")
                st.plotly_chart(fig_priority, use_container_width=True)

            # Структура родительских задач
            with st.expander("**Структура родительских задач**", expanded=False):
                st.subheader("Равномерность разделения задач по всем спринтам")
                av_num, av_est = all_sprints_parent_ids(sprints_df, entities_df)
                perc_of_tasks = sum(av_num) / len(av_num)
                perc_of_estimation = sum(av_est) / len(av_est)
                st.metric("% числа всех подзадач в 10% родительских задач по всем спринтам",
                              f"{perc_of_tasks * 100:.2f}%")
                st.metric("% времени всех подзадач в 10% родительских задач по всем спринтам",
                              f"{perc_of_estimation * 100:.2f}%")

                sprint_tree = one_sprint_parent_ids(sprint_number, entities_df).sort_values(by=['num_tasks'], ascending=False).head(10)
                fig_tree_tasks = go.Figure(go.Treemap(
                    labels=sprint_tree['parent_id'].tolist(),
                    values=sprint_tree['num_tasks'].tolist(),
                    parents=["", "", "", "", "", "", "", "", "", ""]
                )).update_layout(title="10 самых крупных родительских задач спринта (по количеству подзадач)")
                st.plotly_chart(fig_tree_tasks, use_container_width=True)

                sprint_tree = one_sprint_parent_ids(sprint_number, entities_df).sort_values(by=['estimation'], ascending=False).head(10)
                fig_tree_time = go.Figure(go.Treemap(
                    labels=sprint_tree['parent_id'].tolist(),
                    values=sprint_tree['estimation'].tolist(),
                    parents=["", "", "", "", "", "", "", "", "", ""]
                )).update_layout(title="10 самых крупных родительских задач спринта (по времени)")
                st.plotly_chart(fig_tree_time, use_container_width=True)

            # Burndown Chart
            with st.expander("**Burndown Chart**", expanded=False):
                burndown_df = calculate_burndown(sprint_entities, sprint_start, sprint_end)

                # Добавление линии тренда
                x_values = np.arange(len(burndown_df))
                y_values = burndown_df['remaining_work']
                trend_coefficients = np.polyfit(x_values, y_values, 1)
                trend_line = np.poly1d(trend_coefficients)

                fig_burndown = go.Figure()
                fig_burndown.add_trace(go.Scatter(
                    x=burndown_df['date'],
                    y=burndown_df['remaining_work'],
                    mode='lines+markers',
                    name='Оставшаяся работа',
                    line=dict(color='#DC143C', width=4),
                    hovertemplate='Дата: %{x}<br>Оставшаяся работа: %{y} ч.'
                ))
                fig_burndown.add_trace(go.Scatter(
                    x=burndown_df['date'],
                    y=trend_line(x_values),
                    mode='lines',
                    name='Линия тренда',
                    line=dict(color='blue', dash='dash')
                ))

                # Обновление оформления графика
                fig_burndown.update_layout(
                    title="Burndown Chart",
                    xaxis_title="Дата",
                    yaxis_title="Оставшаяся работа (Часов)"
                )

                st.plotly_chart(fig_burndown, use_container_width=True)
                st.info("Burndown Chart показывает оставшуюся работу по дням спринта, включая линию тренда.")

            # BurnUp Chart
            with st.expander("**BurnUp Chart**", expanded=False):
                burnup_df = calculate_burnup(sprint_entities, sprint_start, sprint_end)

                # Добавление линии тренда
                x_values = np.arange(len(burnup_df))
                y_values = burnup_df['completed_work']
                trend_coefficients = np.polyfit(x_values, y_values, 1)
                trend_line = np.poly1d(trend_coefficients)

                fig_burnup = go.Figure()
                fig_burnup.add_trace(go.Scatter(
                    x=burnup_df['date'],
                    y=burnup_df['completed_work'],
                    mode='lines+markers',
                    name='Выполненная работа',
                    line=dict(color='#32CD32', width=4),
                    hovertemplate='Дата: %{x}<br>Выполненная работа: %{y} ч.'
                ))
                fig_burnup.add_trace(go.Scatter(
                    x=burnup_df['date'],
                    y=burnup_df['total_work'],
                    mode='lines',
                    name='Общий объем работы',
                    line=dict(color='gray', width=2, dash='dot')
                ))
                fig_burnup.add_trace(go.Scatter(
                    x=burnup_df['date'],
                    y=trend_line(x_values),
                    mode='lines',
                    name='Линия тренда',
                    line=dict(color='blue', dash='dash')
                ))

                # Обновление оформления графика
                fig_burnup.update_layout(
                    title="BurnUp Chart",
                    xaxis_title="Дата",
                    yaxis_title="Выполненная работа (Часов)"
                )

                st.plotly_chart(fig_burnup, use_container_width=True)
                st.info("BurnUp Chart показывает накопленную выполненную работу по дням спринта, включая линию тренда.")

            # Задачи, не завершённые в спринте
            with st.expander("**Незавершённые задачи**", expanded=False):
                uncompleted_tasks, total_uncompleted, percentage_uncompleted = calculate_uncompleted_tasks(sprint_entities, sprint_start, sprint_end)
                st.metric("Незавершённых задач (Человеко-часы)", f"{total_uncompleted:.1f}")
                st.metric("Процент незавершённых задач (%)", f"{percentage_uncompleted:.1f}%")
                st.info("Этот показатель показывает количество и процент задач, которые не были завершены в спринте.")
                if not uncompleted_tasks.empty:
                    # Добавление дополнительных колонок
                    st.dataframe(uncompleted_tasks[['entity_id', 'name', 'priority', 'assignee', 'status', 'estimation',
                                                    'percent_complete', 'hours_complete', 'percent_remaining', 'hours_remaining']].style.applymap(
                        lambda x: f'background-color: {priority_colors.get(x, "white")}' if x in priority_colors else '', subset=['priority']
                    ))
                else:
                    st.success("Все задачи завершены в спринте.")

            # Cumulative Flow Diagram
            with st.expander("**Cumulative Flow Diagram**", expanded=False):
                cfd_df = calculate_cfd(sprint_entities, sprint_start, sprint_end)
                fig_cfd = go.Figure()
                for status in status_colors.keys():
                    if status in cfd_df.columns:
                        fig_cfd.add_trace(go.Scatter(
                            x=cfd_df['date'],
                            y=cfd_df[status],
                            mode='lines+markers',
                            name=status,
                            line=dict(color=status_colors[status]),
                            hovertemplate='%{x}: %{y} задач'
                        ))
                fig_cfd.update_layout(title="Cumulative Flow Diagram", xaxis_title="Дата", yaxis_title="Количество задач", hovermode='x unified')
                st.plotly_chart(fig_cfd, use_container_width=True)

                st.info("Cumulative Flow Diagram отображает распределение задач по статусам с течением времени.")

            # Сгруппированный CFD
            with st.expander("**Cumulative Flow Diagram (сгруппировано)**", expanded=False):
                cfd_grouped_df = calculate_grouped_cfd(sprint_entities, sprint_start, sprint_end)
                fig_cfd_grouped = go.Figure()
                for group in status_group_colors.keys():
                    if group in cfd_grouped_df.columns:
                        fig_cfd_grouped.add_trace(go.Scatter(
                            x=cfd_grouped_df['date'],
                            y=cfd_grouped_df[group],
                            mode='lines+markers',
                            name=group,
                            line=dict(color=status_group_colors[group]),
                            hovertemplate='%{x}: %{y} задач'
                        ))
                fig_cfd_grouped.update_layout(title="Cumulative Flow Diagram (сгруппировано)", xaxis_title="Дата", yaxis_title="Количество задач", hovermode='x unified')
                st.plotly_chart(fig_cfd_grouped, use_container_width=True)

                st.info("Этот график отображает сгруппированное распределение задач по статусам с течением времени.")

            # Среднее время цикла
            with st.expander("**Среднее время цикла**", expanded=False):
                # Рассчитываем только для завершённых задач
                completed_tasks = sprint_entities[sprint_entities['status'].isin(['Закрыто', 'Выполнено'])]
                if not completed_tasks.empty:
                    average_cycle_time = completed_tasks['cycle_time'].mean()
                    st.metric("Среднее время цикла (Человеко-часы)", f"{average_cycle_time:.1f}")
                    st.info("Среднее время цикла показывает, сколько времени в среднем занимает выполнение задачи от создания до завершения.")
                else:
                    st.warning("Нет завершённых задач для расчета среднего времени цикла.")

            # Детальная аналитика задач
            detailed_tasks = sprint_entities[['entity_id', 'name', 'priority', 'assignee', 'adjusted_status', 'create_date', 'update_date', 'cycle_time']]
            with st.expander("**Детальная аналитика задач**", expanded=False):
                st.dataframe(detailed_tasks.style.applymap(
                    lambda x: f'background-color: {priority_colors.get(x, "white")}' if x in priority_colors else '', subset=['priority']
                ))

            # --- Добавленные Таблицы ЧД ---
            with st.expander("**Показатели ЧД**", expanded=False):
                # 1. Заблокировано (ЧД/шт) - Всегда нули
                st.markdown("### Заблокировано (ЧД/шт)")
                blocked_df = blocked_per_day(sprint_number)
                st.info("Сумма оценок заблокированных задач всегда равна нулю, как указано в задании.")

                # 2. Добавлено (ЧД/шт)
                st.markdown("### Добавлено (ЧД/шт)")
                added_df = added_per_day(sprint_number, sprints_df, history_df, entities_df)
                st.dataframe(added_df, use_container_width=True)
                st.info("Сумма оценок и количество добавленных задач за каждый день спринта.")

                # 3. Исключено (ЧД/шт)
                st.markdown("### Исключено (ЧД/шт)")
                excluded_df = excluded(sprint_number, sprints_df, history_df, entities_df)
                st.dataframe(excluded_df, use_container_width=True)
                st.info("Сумма оценок и количество исключенных задач за каждый день спринта.")

                # Интерактивный график динамики ЧД
                st.markdown("#### Динамика ЧД")

                # Создание общего DataFrame для графика
                combined_df = added_df[['Дата', 'Количество задач']].copy()
                combined_df = combined_df.rename(columns={'Количество задач': 'Добавлено'})
                combined_df['Исключено'] = excluded_df['Количество задач'].values
                combined_df['Заблокировано'] = blocked_df['Количество задач'].values  # Всегда ноль

                # Построение графика
                fig_chd = go.Figure()

                fig_chd.add_trace(go.Scatter(
                    x=combined_df['Дата'],
                    y=combined_df['Добавлено'],
                    mode='lines+markers',
                    name='Добавлено',
                    line=dict(color='#32CD32'),
                    hovertemplate='Дата: %{x}<br>Добавлено: %{y} задач'
                ))

                fig_chd.add_trace(go.Scatter(
                    x=combined_df['Дата'],
                    y=combined_df['Исключено'],
                    mode='lines+markers',
                    name='Исключено',
                    line=dict(color='#DC143C'),
                    hovertemplate='Дата: %{x}<br>Исключено: %{y} задач'
                ))

                fig_chd.add_trace(go.Scatter(
                    x=combined_df['Дата'],
                    y=combined_df['Заблокировано'],
                    mode='lines+markers',
                    name='Заблокировано',
                    line=dict(color='#FFD700'),
                    hovertemplate='Дата: %{x}<br>Заблокировано: %{y} задач'
                ))

                fig_chd.update_layout(
                    title="Динамика добавленных, исключенных и заблокированных задач",
                    xaxis_title="Дата",
                    yaxis_title="Количество задач",
                    hovermode='x unified'
                )

                st.plotly_chart(fig_chd, use_container_width=True)
                st.info("Этот график показывает динамику добавленных, исключенных и заблокированных задач по дням спринта.")

    # Velocity Chart
    if len(selected_sprints) > 1:
        st.markdown("### Velocity Chart")

        velocities = []
        for sprint_name in selected_sprints:
            sprint_entities = sprint_data[sprint_name]
            sprint_start = sprints_df[sprints_df['sprint_name'] == sprint_name]['sprint_start_date'].iloc[0]
            sprint_end = sprints_df[sprints_df['sprint_name'] == sprint_name]['sprint_end_date'].iloc[0]
            selected_date = st.session_state['selected_date'][sprint_name]

            sprint_entities['adjusted_status'] = sprint_entities.apply(adjust_status, args=(selected_date,), axis=1)
            completed_work = sprint_entities[
                sprint_entities['status'].isin(['Закрыто', 'Выполнено'])
            ]['estimation'].sum() / 3600  # в часах

            velocities.append({'sprint': sprint_name, 'completed_work': completed_work})

        velocity_df = pd.DataFrame(velocities)

        # Добавление линии тренда
        x_values = np.arange(len(velocity_df))
        y_values = velocity_df['completed_work']
        trend_coefficients = np.polyfit(x_values, y_values, 1)
        trend_line = np.poly1d(trend_coefficients)

        # Построение графика
        fig_velocity = go.Figure()
        fig_velocity.add_trace(go.Bar(
            x=velocity_df['sprint'],
            y=velocity_df['completed_work'],
            name='Выполненная работа',
            marker_color='blue'
        ))
        fig_velocity.add_trace(go.Scatter(
            x=velocity_df['sprint'],
            y=trend_line(x_values),
            mode='lines',
            name='Линия тренда',
            line=dict(color='red', dash='dash')
        ))
        fig_velocity.update_layout(
            title="Velocity Chart",
            xaxis_title="Спринт",
            yaxis_title="Выполненная работа (Часов)"
        )
        st.plotly_chart(fig_velocity, use_container_width=True)
        st.info("Velocity Chart показывает объем выполненной работы в каждом спринте, включая линию тренда.")

        # Определение лучшего спринта
        best_sprint_row = velocity_df.loc[velocity_df['completed_work'].idxmax()]
        best_sprint = best_sprint_row['sprint']
        st.markdown(f"**Лучший спринт по выполненной работе:** {best_sprint}")

else:
    st.info("Загрузите все файлы для начала анализа.")
