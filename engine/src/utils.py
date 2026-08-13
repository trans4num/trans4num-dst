import time


class Colors:
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
    CYAN = "\u001b[36m"
    ENDC = "\033[0m"


def print_runtime(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Record the start time
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # Record the end time
        runtime = end_time - start_time  # Calculate the runtime
        print(f"Runtime of {func.__name__}: {runtime:.4f} seconds")  # Print the runtime
        return result  # Return the result of the function call

    return wrapper
