FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

CMD ["celery", "-A", "DjangoWeatherReminder", "worker", "-l", "info", "-Q", "celery"]