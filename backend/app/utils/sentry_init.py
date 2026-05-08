import os

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
    except Exception:
        # Graceful fallback if sentry not installed
        pass
