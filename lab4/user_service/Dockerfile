FROM python:3.9-slim

WORKDIR /user

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

#EXPOSE 8000

CMD ["uvicorn", "test_user:app", "--host", "0.0.0.0", "--port", "8000"]