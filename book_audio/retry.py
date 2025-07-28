import logging
import time

log = logging.getLogger("book_audio")


def is_quota_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def with_retries(fn, attempts=5, base_delay=2.0, sleep=time.sleep):
    """Call fn(); on a quota / rate-limit error wait base_delay * 2**n seconds and try again.
    Other errors are raised immediately."""
    for n in range(attempts):
        try:
            return fn()
        except Exception as exc:                    # noqa: BLE001 - we re-raise what we do not retry
            if not is_quota_error(exc) or n == attempts - 1:
                raise
            wait = base_delay * (2 ** n)
            log.warning("quota error (%s), retry %d/%d in %.0fs", str(exc)[:80], n + 1, attempts - 1, wait)
            sleep(wait)
