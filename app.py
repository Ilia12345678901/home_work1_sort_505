from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sorting_algorithms import (
    SortResult, selection_sort, bubble_sort, counting_sort, timsort,
    SORTS, make_sort_steps, validate_sort,
)
from benchmarking import (
    DISTRIBUTIONS, generate_data, benchmark_one, benchmark_suite,
    fit_complexity,
)

st.set_page_config(page_title="Анализ алгоритмов сортировки", page_icon="📊", layout="wide")
st.title("Эмпирический и теоретический анализ алгоритмов сортировки")
st.caption("Selection sort · Bubble sort с флагом · Counting sort · Timsort")

with st.sidebar:
    st.header("Параметры эксперимента")
    chosen_names = st.multiselect(
        "Алгоритмы",
        options=list(SORTS),
        default=list(SORTS),
        help="Квадратичные сортировки рекомендуется запускать на меньших N.",
    )
    distribution = st.selectbox("Распределение данных", list(DISTRIBUTIONS))
    n = st.select_slider(
        "Размер массива N",
        options=[20, 30, 100, 300, 600, 1000, 2000, 4000, 8000, 10000, 50000, 100000],
        value=1000,
    )
    repeats = st.slider("Число повторений", 1, 10, 5)
    seed = st.number_input("Начальное значение seed", min_value=0, max_value=10**9, value=42)
    run_benchmark = st.button("Запустить эксперимент", type="primary", use_container_width=True)
    st.divider()
    st.caption("Для Selection/Bubble при N > 2 000 приложение предупредит о возможном долгом запуске.")

if "benchmark_df" not in st.session_state:
    st.session_state.benchmark_df = pd.DataFrame()
if "benchmark_summary" not in st.session_state:
    st.session_state.benchmark_summary = pd.DataFrame()

if run_benchmark:
    if not chosen_names:
        st.error("Выберите хотя бы один алгоритм.")
    elif n > 2000 and any(name in chosen_names for name in ("Selection sort", "Bubble sort (optimized)")):
        st.warning("Квадратичные алгоритмы на таком размере могут выполняться долго. Для полного сравнения уменьшите N или снимите их выбор.")
    else:
        with st.spinner("Выполняются замеры..."):
            raw, summary = benchmark_suite(
                chosen_names, n, distribution, repeats, int(seed)
            )
            st.session_state.benchmark_df = raw
            st.session_state.benchmark_summary = summary
        st.success(f"Готово: {len(raw)} измерений.")

summary = st.session_state.benchmark_summary
raw = st.session_state.benchmark_df

if not summary.empty:
    st.subheader("Результаты эксперимента")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(summary, x="Алгоритм", y="Среднее время, мс",
                     error_y="Стандартное отклонение, мс",
                     title="Среднее время выполнения")
        fig.update_layout(xaxis_title="Алгоритм", yaxis_title="Время, мс")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(summary, x="Алгоритм", y="Пиковая память, КБ",
                     title="Пиковая дополнительная память")
        fig.update_layout(xaxis_title="Алгоритм", yaxis_title="Память, КБ")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Сырые замеры")
    st.dataframe(raw, use_container_width=True, hide_index=True)
    csv = raw.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Скачать CSV с замерами", csv, "benchmark_raw.csv", "text/csv")

st.divider()
st.header("Сравнение зависимости времени от N")
st.write("Серия экспериментов для выбранных размеров. Время генерации входного массива и его копирования не входит в измеряемый интервал.")
with st.expander("Настройки серии измерений", expanded=False):
    series_algorithms = st.multiselect("Алгоритмы для серии", list(SORTS), default=list(SORTS), key="series_algorithms")
    series_distribution = st.selectbox("Распределение для серии", list(DISTRIBUTIONS), key="series_distribution")
    series_repeats = st.slider("Повторений на точку", 1, 10, 5, key="series_repeats")
    series_sizes = st.multiselect(
        "Размеры N",
        [100, 300, 600, 1000, 2000, 4000, 8000, 10000, 50000, 100000],
        default=[100, 300, 600, 1000, 2000],
    )
    if st.button("Построить серию"):
        if any(a in series_algorithms for a in ("Selection sort", "Bubble sort (optimized)")) and any(x > 2000 for x in series_sizes):
            st.error("Для квадратичных алгоритмов ограничьте размеры N значением 2000.")
        elif not series_algorithms or not series_sizes:
            st.error("Нужно выбрать алгоритмы и хотя бы один размер.")
        else:
            records = []
            bar = st.progress(0)
            total = len(series_algorithms) * len(series_sizes)
            done = 0
            for algo in series_algorithms:
                for size in sorted(series_sizes):
                    _, one = benchmark_suite([algo], size, series_distribution, series_repeats, int(seed) + size)
                    records.extend(one.to_dict("records"))
                    done += 1
                    bar.progress(done / total)
            st.session_state.series_df = pd.DataFrame(records)
            bar.empty()

series = st.session_state.get("series_df", pd.DataFrame())
if not series.empty:
    st.subheader("График 1. Линейная шкала")
    fig = px.line(series, x="N", y="Среднее время, мс", color="Алгоритм",
                  error_y="Стандартное отклонение, мс", markers=True)
    fig.update_layout(xaxis_title="Размер массива, N (элементов)", yaxis_title="Время выполнения, T (мс)")
    fig.update_xaxes(type="linear")
    fig.update_yaxes(type="linear")
    fig.update_layout(legend_title="Алгоритм")
    fig.update_xaxes(showgrid=True); fig.update_yaxes(showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("График 2. Двойной логарифмический масштаб")
    logfig = px.scatter(series[series["Среднее время, мс"] > 0], x="N", y="Среднее время, мс",
                        color="Алгоритм", error_y="Стандартное отклонение, мс", trendline=None)
    for algo, part in series.groupby("Алгоритм"):
        part = part[part["Среднее время, мс"] > 0]
        if len(part) >= 2:
            logfig.add_trace(go.Scatter(x=part["N"], y=part["Среднее время, мс"],
                                        mode="lines+markers", name=algo))
    logfig.update_xaxes(type="log", title="Размер массива, N (элементов)")
    logfig.update_yaxes(type="log", title="Время выполнения, T (мс)")
    logfig.update_layout(legend_title="Алгоритм")
    st.plotly_chart(logfig, use_container_width=True)

    st.subheader("График 3. Теоретическая аппроксимация")
    fit_rows = []
    fitfig = go.Figure()
    for algo, part in series.groupby("Алгоритм"):
        part = part.sort_values("N")
        fitfig.add_trace(go.Scatter(x=part["N"], y=part["Среднее время, мс"],
                                    mode="markers", name=f"{algo}: эксперимент"))
        complexity, coefficient, exponent = fit_complexity(algo, part["N"].tolist(), part["Среднее время, мс"].tolist())
        xs = sorted(part["N"].tolist())
        ys = [coefficient * (x*x if complexity == "N²" else (x * __import__("math").log2(max(x, 2)) if complexity == "N log₂N" else x)) for x in xs]
        fitfig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=f"{algo}: fitting {complexity}"))
        fit_rows.append({"Алгоритм": algo, "Модель": complexity, "Коэффициент c": coefficient,
                         "Наклон log-log (оценка)": exponent})
    fitfig.update_layout(xaxis_title="Размер массива, N (элементов)", yaxis_title="Время выполнения, T (мс)",
                         xaxis_type="log", yaxis_type="log")
    fitfig.update_xaxes(showgrid=True); fitfig.update_yaxes(showgrid=True)
    st.plotly_chart(fitfig, use_container_width=True)
    st.dataframe(pd.DataFrame(fit_rows), use_container_width=True, hide_index=True)

st.divider()
st.header("Пошаговая визуализация сортировки")
st.caption("Для наглядности используется массив из 20–30 элементов. Каждый шаг показывает сравнение или перестановку.")
anim_algo = st.selectbox("Алгоритм визуализации", list(SORTS), key="anim_algo")
anim_n = st.slider("Количество элементов", 20, 30, 20)
anim_seed = st.number_input("Seed визуализации", min_value=0, value=7, key="anim_seed")
if st.button("Сформировать шаги"):
    anim_data = generate_data(anim_n, "Случайный массив", int(anim_seed))
    st.session_state.anim_steps = make_sort_steps(anim_data, anim_algo)
    st.session_state.anim_original = anim_data
    st.session_state.anim_index = 0

if "anim_steps" in st.session_state:
    steps = st.session_state.anim_steps
    idx = st.slider("Шаг", 0, len(steps)-1, min(st.session_state.get("anim_index", 0), len(steps)-1))
    st.session_state.anim_index = idx
    step = steps[idx]
    st.write(step["description"])
    values = step["array"]
    colors = ["#2ca02c" if i in step["sorted"] else "#ff7f0e" if i in step["active"] else "#4c78a8" for i in range(len(values))]
    fig = go.Figure(go.Bar(x=list(range(len(values))), y=values, marker_color=colors,
                           text=values, textposition="outside"))
    fig.update_layout(xaxis_title="Индекс", yaxis_title="Значение", showlegend=False,
                      title=f"Шаг {idx+1} из {len(steps)}")
    st.plotly_chart(fig, use_container_width=True)
    a, b = st.columns(2)
    with a:
        if st.button("← Предыдущий", disabled=idx == 0):
            st.session_state.anim_index = idx - 1
            st.rerun()
    with b:
        if st.button("Следующий →", disabled=idx == len(steps)-1):
            st.session_state.anim_index = idx + 1
            st.rerun()

st.divider()
st.header("Проверка корректности")
if st.button("Запустить набор assert-тестов"):
    try:
        validate_sort()
        st.success("Все тесты пройдены: пустой массив, один элемент, дубликаты, отрицательные числа, случайные данные.")
    except AssertionError as exc:
        st.exception(exc)

st.info("Важно: результаты зависят от оборудования, версии Python и фоновой нагрузки. Для защиты объясните счётчики операций, устройство run-ов Timsort и методику замеров.")
