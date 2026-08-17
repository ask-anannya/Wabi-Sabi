from ddtrace import patch_all, tracer

def setup_tracing():
    patch_all()

def traced(name):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with tracer.trace(name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator