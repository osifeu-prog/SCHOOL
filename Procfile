web: gunicorn bot.main:flask_app --workers=2 --threads=4 --timeout=120 --bind=0.0.0.0:$PORT
worker: python -m bot.worker
