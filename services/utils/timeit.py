import time


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed = end - start
        print(f"Время выполнения функции '{func.__name__}': {elapsed:.6f} секунд")
        return result

    return wrapper

