# syntax=docker/dockerfile:1

# TODO oleksandr: is this source image ok ?
FROM python:3.11

# TODO oleksandr: do we need this ?
ENV PYTHONDONTWRITEBYTECODE=1

# TODO oleksandr: do we need this ?
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# publish port 8000
EXPOSE 8000

# run the server
CMD ["uvicorn", "swipy_on_gpt.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
