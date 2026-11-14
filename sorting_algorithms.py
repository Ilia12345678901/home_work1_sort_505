from __future__ import annotations

from typing import Callable, TypeAlias

Number: TypeAlias = int | float
SortResult: TypeAlias = tuple[list[Number], int, int]


def selection_sort(arr: list[Number]) -> SortResult:
    """Selection sort: O(n²) comparisons, O(n) swaps, O(1) extra space."""
    a = arr
    comparisons = swaps = 0
    n = len(a)

    for i in range(n - 1):
        min_index = i
        for j in range(i + 1, n):
            comparisons += 1
            if a[j] < a[min_index]:
                min_index = j
        if min_index != i:
            a[i], a[min_index] = a[min_index], a[i]
            swaps += 1

    return a, comparisons, swaps


def bubble_sort(arr: list[Number]) -> SortResult:
    """Optimized bubble sort: O(n²) worst/average, O(n) best, O(1) extra space."""
    a = arr
    comparisons = swaps = 0
    n = len(a)

    for end in range(n - 1, 0, -1):
        swapped = False
        for j in range(end):
            comparisons += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
                swapped = True
        if not swapped:
            break

    return a, comparisons, swaps


def counting_sort(arr: list[Number]) -> SortResult:
    """Counting sort for integers, including negative values: O(n + k) time, O(k) space."""
    if any(not isinstance(x, int) or isinstance(x, bool) for x in arr):
        raise TypeError("Counting sort принимает только целые числа.")
    if not arr:
        return [], 0, 0

    min_value = min(arr)
    max_value = max(arr)
    counts = [0] * (max_value - min_value + 1)

    for value in arr:
        counts[value - min_value] += 1

    result: list[int] = []
    writes = 0
    for offset, count in enumerate(counts):
        for _ in range(count):
            result.append(offset + min_value)
            writes += 1

    # Counting Sort does not compare pairs of elements.
    comparisons = 0
    return result, comparisons, writes


SORTS: dict[str, Callable[[list[Number]], SortResult]] = {
    "Selection sort": selection_sort,
    "Bubble sort (optimized)": bubble_sort,
    "Counting sort": counting_sort,
}


def validate_sort() -> None:
    """Run deterministic correctness checks for all implemented algorithms."""
    cases: list[list[Number]] = [
        [], [1], [2, 2, 2], [3, -1, 0, -5, 3], [9, 8, 7, 6, 5],
        [1, 2, 3, 4, 5], [4, 1, 4, 2, 0, -2],
    ]

    for name, function in SORTS.items():
        for case in cases:
            if name == "Counting sort" and any(
                not isinstance(x, int) or isinstance(x, bool) for x in case
            ):
                continue
            original = case.copy()
            work = case.copy()
            result, _, _ = function(work)
            assert result == sorted(original), (name, original, result)
            if name != "Counting sort":
                assert work == result
            assert case == original

    for function in (selection_sort, bubble_sort):
        result, _, _ = function([2.5, -1.0, 2.5, 0.0])
        assert result == [-1.0, 0.0, 2.5, 2.5]


def make_sort_steps(data: list[int], algorithm: str) -> list[dict]:
    """Create visualization frames for Selection, Bubble, or Counting Sort."""
    a = data.copy()
    frames: list[dict] = []

    def add(desc: str, active: list[int], sorted_idx: list[int]) -> None:
        frames.append({
            "array": a.copy(),
            "description": desc,
            "active": active.copy(),
            "sorted": sorted_idx.copy(),
        })

    add("Исходный массив", [], [])
    n = len(a)

    if algorithm == "Selection sort":
        fixed: list[int] = []
        for i in range(n - 1):
            min_index = i
            for j in range(i + 1, n):
                add(
                    f"Сравниваем a[{j}]={a[j]} и текущий минимум "
                    f"a[{min_index}]={a[min_index]}",
                    [min_index, j], fixed,
                )
                if a[j] < a[min_index]:
                    min_index = j
            if min_index != i:
                a[i], a[min_index] = a[min_index], a[i]
            add(f"Фиксируем минимум на позиции {i}", [i, min_index], fixed + [i])
            fixed.append(i)

    elif algorithm == "Bubble sort (optimized)":
        fixed: list[int] = []
        for end in range(n - 1, 0, -1):
            swapped = False
            for j in range(end):
                add(
                    f"Сравниваем соседние элементы a[{j}] и a[{j + 1}]",
                    [j, j + 1], fixed,
                )
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
                    swapped = True
                    add("Перестановка соседних элементов", [j, j + 1], fixed)
            fixed.append(end)
            add(f"Максимум прохода зафиксирован на позиции {end}", [], fixed)
            if not swapped:
                break

    elif algorithm == "Counting sort":
        if any(not isinstance(x, int) or isinstance(x, bool) for x in a):
            raise TypeError("Для визуализации Counting Sort нужны целые числа.")
        if a:
            min_value = min(a)
            max_value = max(a)
            counts = [0] * (max_value - min_value + 1)
            for value in a:
                counts[value - min_value] += 1
                add(f"Увеличиваем частоту значения {value}", [], [])

            output_index = 0
            for offset, count in enumerate(counts):
                value = offset + min_value
                for _ in range(count):
                    a[output_index] = value
                    add(
                        f"Записываем значение {value} на позицию {output_index}",
                        [output_index], list(range(output_index + 1)),
                    )
                    output_index += 1
    else:
        raise ValueError(
            f"Неизвестный алгоритм: {algorithm}. "
            f"Доступные алгоритмы: {', '.join(SORTS.keys())}"
        )

    if a != sorted(data):
        raise AssertionError("Ошибка построения кадров визуализации")
    add("Массив отсортирован", [], list(range(n)))
    return frames
