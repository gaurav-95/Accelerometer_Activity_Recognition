FROM python:3.8.5

WORKDIR /usr/src/app

COPY activity_detectv9.h5 .
COPY realtime_activity.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./realtime_activity.py"]