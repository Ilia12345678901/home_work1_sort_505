from __future__ import annotations

import random
import statistics
import time
import tracemalloc
import math
from typing import Callable

import pandas as pd
from sorting_algorithms import SORTS

DISTRIBUTIONS = [
    "Случайный массив",
    "Уже отсортированный",
    "Обратно отсортированный",
    "Почти отсортированный (5%)",
    "Много дубликатов (5 значений)",
]


def generate_data(n: int, distribution: str, seed: int = 42) -> list[int]:
    """Generate a deterministic test case; generation is outside timed sections."""
    rng = random.Random(seed)
    if distribution == "Случайный массив":
        return [rng.randint(-n, n) for _ in range(n)]
    if distribution == "Уже отсортированный":
        return list(range(n))
    if distribution == "Обратно отсортированный":
        return list(range(n, 0, -1))
    if distribution == "Почти отсортированный (5%)":
        data = list(range(n))
        swaps = max(1, int(n * 0.05)) if n else 0
        for _ in range(swaps):
            if n > 1:
                i, j = rng.randrange(n), rng.randrange(n)
                data[i], data[j] = data[j], data[i]
        return data
    if distribution == "Много дубликатов (5 значений)":
        return [rng.randint(1, 5) for _ in range(n)]
    raise ValueError(f"Неизвестное распределение: {distribution}")


def benchmark_one(function: Callable, data: list[int], repeats: int, seed: int = 0) -> dict:
    """Measure execution only; copying and generation occur outside perf_counter interval."""
    samples: list[float] = []
    comparisons = writes = 0
    peak_values: list[int] = []
    expected = sorted(data)  # validation reference, outside timed interval
    for repeat in range(repeats):
        test = data.copy()
        start = time.perf_counter()
        result, cmp_count, write_count = function(test)
        elapsed = time.perf_counter() - start
        if result != expected:
            raise AssertionError(f"{function.__name__} returned an incorrect result")
        samples.append(elapsed * 1000)
        comparisons, writes = cmp_count, write_count
        # Memory is measured separately to avoid tracemalloc distorting timing.
        memory_input = data.copy()
        tracemalloc.start()
        function(memory_input)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_values.append(peak)
    return {
        "mean_ms": statistics.mean(samples),
        "std_ms": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "comparisons": comparisons,
        "writes": writes,
        "peak_kb": statistics.mean(peak_values) / 1024,
        "samples_ms": samples,
    }


def benchmark_suite(names: list[str], n: int, distribution: str, repeats: int, seed: int):
    raw_records = []
    summary_records = []
    for name in names:
        data = generate_data(n, distribution, seed)
        result = benchmark_one(SORTS[name], data, repeats, seed)
        summary_records.append({
            "Алгоритм": name, "N": n, "Распределение": distribution,
            "Повторений": repeats, "Среднее время, мс": result["mean_ms"],
            "Стандартное отклонение, мс": result["std_ms"],
            "Сравнения": result["comparisons"], "Записи/перестановки": result["writes"],
            "Пиковая память, КБ": result["peak_kb"],
        })
        for repeat, sample_ms in enumerate(result["samples_ms"], start=1):
            raw_records.append({"Алгоритм": name, "N": n, "Распределение": distribution,
                                "Повтор": repeat, "Время, мс": sample_ms,
                                "Сравнения": result["comparisons"], "Записи/перестановки": result["writes"]})
    return pd.DataFrame(raw_records), pd.DataFrame(summary_records)


def fit_complexity(name: str, sizes: list[int], times: list[float]):
    """Least-squares fit to a theoretical family; returns c and log-log slope."""
    if name in ("Selection sort", "Bubble sort (optimized)"):
        model = "N²"
        features = [n*n for n in sizes]
    elif name == "Counting sort":
        model = "N"
        features = [float(n) for n in sizes]
    else:
        model = "N log₂N"
        features = [n * math.log2(max(n, 2)) for n in sizes]
    denominator = sum(x*x for x in features)
    coefficient = sum(x*y for x, y in zip(features, times)) / denominator if denominator else 0.0
    valid = [(math.log(n), math.log(t)) for n, t in zip(sizes, times) if n > 0 and t > 0]
    if len(valid) >= 2:
        xs, ys = zip(*valid)
        xbar, ybar = statistics.mean(xs), statistics.mean(ys)
        denom = sum((x-xbar)**2 for x in xs)
        slope = sum((x-xbar)*(y-ybar) for x, y in valid) / denom if denom else float("nan")
    else:
        slope = float("nan")
    return model, coefficient, slope
