from __future__ import annotations

from typing import Callable, TypeAlias

Number: TypeAlias = int | float
SortResult: TypeAlias = tuple[list[Number], int, int]


def selection_sort(arr: list[Number]) -> SortResult:
    """Selection sort: O(n²) comparisons, O(n) swaps, O(1) auxiliary space; sorts in-place."""
    a = arr
    comparisons = swaps = 0
    n = len(a)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            comparisons += 1
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            swaps += 1
    return a, comparisons, swaps


def bubble_sort(arr: list[Number]) -> SortResult:
    """Optimized bubble sort: O(n²) worst/average, O(n) best; O(1) extra space; sorts in-place."""
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
    """Counting sort for integers: O(n + k) time and O(k) auxiliary space.

    Raises TypeError for non-integer input. Supports negative integer keys by offset.
    comparisons counts key/range checks; writes counts output placements.
    """
    if any(not isinstance(x, int) or isinstance(x, bool) for x in arr):
        raise TypeError("Counting sort принимает только целые числа.")
    if not arr:
        return [], 0, 0
    min_value, max_value = min(arr), max(arr)
    counts = [0] * (max_value - min_value + 1)
    comparisons = 2 * len(arr)  # checks for min/max range, not pairwise element comparisons
    for value in arr:
        counts[value - min_value] += 1
    result: list[int] = []
    writes = 0
    for offset, count in enumerate(counts):
        for _ in range(count):
            result.append(offset + min_value)
            writes += 1
    return result, comparisons, writes


def _binary_insertion(a: list[Number], lo: int, hi: int, start: int) -> tuple[int, int]:
    comparisons = writes = 0
    for i in range(max(start, lo + 1), hi):
        pivot = a[i]
        left, right = lo, i
        while left < right:
            mid = (left + right) // 2
            comparisons += 1
            if pivot < a[mid]:
                right = mid
            else:
                left = mid + 1
        j = i
        while j > left:
            a[j] = a[j - 1]
            writes += 1
            j -= 1
        a[left] = pivot
        writes += 1
    return comparisons, writes


def _minrun(n: int) -> int:
    r = 0
    while n >= 64:
        r |= n & 1
        n >>= 1
    return n + r


def timsort(arr: list[Number]) -> SortResult:
    """Educational simplified Timsort: natural runs, minrun extension, stack merge.

    O(n log n) worst-case time, O(n) auxiliary memory; adaptive on existing runs; sorts in-place.
    """
    a = arr
    n = len(a)
    if n < 2:
        return a, 0, 0
    minrun = _minrun(n)
    runs: list[tuple[int, int]] = []
    comparisons = writes = 0

    i = 0
    while i < n:
        start = i
        i += 1
        if i < n:
            comparisons += 1
            descending = a[i] < a[i - 1]
            if descending:
                while i < n:
                    comparisons += 1
                    if a[i] >= a[i - 1]:
                        break
                    i += 1
                a[start:i] = reversed(a[start:i])
                writes += i - start
            else:
                while i < n:
                    comparisons += 1
                    if a[i] < a[i - 1]:
                        break
                    i += 1
        target = min(n, max(i, start + minrun))
        c, w = _binary_insertion(a, start, target, i)
        comparisons += c
        writes += w
        runs.append((start, target - start))
        i = target

    def merge_at(index: int) -> None:
        nonlocal comparisons, writes, runs, a
        base1, len1 = runs[index]
        base2, len2 = runs[index + 1]
        left = a[base1:base1 + len1]
        right = a[base2:base2 + len2]
        i = j = 0
        dest = base1
        while i < len(left) and j < len(right):
            comparisons += 1
            if left[i] <= right[j]:
                a[dest] = left[i]
                i += 1
            else:
                a[dest] = right[j]
                j += 1
            writes += 1
            dest += 1
        while i < len(left):
            a[dest] = left[i]; i += 1; dest += 1; writes += 1
        while j < len(right):
            a[dest] = right[j]; j += 1; dest += 1; writes += 1
        runs[index] = (base1, len1 + len2)
        del runs[index + 1]

    # Collapse stack while maintaining a simplified size invariant.
    for new_run in range(len(runs)):
        while len(runs) >= 2:
            if len(runs) >= 3:
                A = runs[-3][1]; B = runs[-2][1]; C = runs[-1][1]
                if A <= B + C or B <= C:
                    merge_at(-3 if A < C else -2)
                    continue
            if runs[-2][1] <= runs[-1][1]:
                merge_at(-2)
                continue
            break
    while len(runs) > 1:
        merge_at(-2)
    return a, comparisons, writes


SORTS: dict[str, Callable[[list[Number]], SortResult]] = {
    "Selection sort": selection_sort,
    "Bubble sort (optimized)": bubble_sort,
    "Counting sort": counting_sort,
    "Timsort (educational)": timsort,
}


def validate_sort() -> None:
    """Run deterministic assertions for all implemented algorithms."""
    cases: list[list[Number]] = [
        [], [1], [2, 2, 2], [3, -1, 0, -5, 3], [9, 8, 7, 6, 5],
        [1, 2, 3, 4, 5], [4, 1, 4, 2, 0, -2],
    ]
    for name, function in SORTS.items():
        for case in cases:
            if name == "Counting sort" and any(not isinstance(x, int) for x in case):
                continue
            original = case.copy()
            work = case.copy()
            result, _, _ = function(work)
            assert result == sorted(original), (name, original, result)
            if name != "Counting sort":
                assert work == result
            assert case == original
    for fn in (selection_sort, bubble_sort, timsort):
        result, _, _ = fn([2.5, -1.0, 2.5, 0.0])
        assert result == [-1.0, 0.0, 2.5, 2.5]


def make_sort_steps(data: list[int], algorithm: str) -> list[dict]:
    """Create pedagogical frames for a small input (up to 30 values)."""
    a = data.copy()
    frames: list[dict] = []
    def add(desc: str, active: list[int], sorted_idx: list[int]) -> None:
        frames.append({"array": a.copy(), "description": desc,
                       "active": active.copy(), "sorted": sorted_idx.copy()})
    add("Исходный массив", [], [])
    n = len(a)
    if algorithm == "Selection sort":
        fixed = []
        for i in range(n - 1):
            m = i
            for j in range(i + 1, n):
                add(f"Сравниваем a[{j}]={a[j]} и текущий минимум a[{m}]={a[m]}", [m, j], fixed)
                if a[j] < a[m]:
                    m = j
            a[i], a[m] = a[m], a[i]
            add(f"Фиксируем минимум на позиции {i}", [i, m], fixed + [i])
            fixed.append(i)
    elif algorithm == "Bubble sort (optimized)":
        fixed = []
        for end in range(n - 1, 0, -1):
            swapped = False
            for j in range(end):
                add(f"Сравниваем соседние элементы a[{j}] и a[{j+1}]", [j, j+1], fixed)
                if a[j] > a[j+1]:
                    a[j], a[j+1] = a[j+1], a[j]
                    swapped = True
                    add("Перестановка соседних элементов", [j, j+1], fixed)
            fixed.append(end)
            add(f"Максимум прохода зафиксирован на позиции {end}", [], fixed)
            if not swapped:
                break
    else:
        # Counting sort and Timsort are represented as successive placements/merges
        # to keep the visualizer generic and understandable.
        target = sorted(a)
        for i, value in enumerate(target):
            a[i] = value
            add(f"Записываем следующее значение {value} на позицию {i}", [i], list(range(i+1)))
    if a != sorted(data):
        raise AssertionError("Ошибка построения кадров визуализации")
    add("Массив отсортирован", [], list(range(n)))
    return frames
