FROM python:3.9

WORKDIR /app

RUN python -m pip install --upgrade pip && pip install gunicorn==20.01.0 --no-cache-dir

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:9001", "foodgram.wsgi"]