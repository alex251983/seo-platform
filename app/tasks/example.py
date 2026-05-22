from app.tasks.celery_app import celery_app

@celery_app.task(name="tasks.example")
def example_task():
    return "Hello from Celery"
