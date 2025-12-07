import time
import functools
from typing import Callable, Any
from config.config import Config

def retry_with_exponential_backoff(
    max_retries: int = Config.MAX_RETRIES,
    base_delay: float = Config.RETRY_DELAY,
    max_delay: float = 60.0,
    exponential_base: float = 2
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    retries += 1

                    if retries >= max_retries:
                        print(f"❌ Max retries ({max_retries}) reached for {func.__name__}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (retries - 1)), max_delay)

                    print(f"⚠️ Attempt {retries} failed: {str(e)}")
                    print(f"🔄 Retrying in {delay:.1f} seconds...")

                    time.sleep(delay)

            return None

        return wrapper
    return decorator


def timeout_handler(timeout_seconds: int):
    """
    Decorator to add timeout to functions (simplified version)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")

            # Set alarm (Unix-like systems only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            except AttributeError:
                # Windows doesn't support signal.SIGALRM, just run normally
                return func(*args, **kwargs)

        return wrapper
    return decorator

