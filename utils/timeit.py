import time


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()  # время начала
        result = func(*args, **kwargs)  # вызов оригинальной функции
        end = time.time()  # время окончания
        elapsed = end - start
        print(f"Время выполнения функции '{func.__name__}': {elapsed:.6f} секунд")
        return result

    return wrapper