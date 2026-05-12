from app.tasks.celery_app import celery

@celery.task(name="tasks.example")
def example_task():
    return "Hello from Celery"