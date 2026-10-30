# imagem leve com Python
FROM python:3.12-slim

WORKDIR /app

# instala as dependencias primeiro 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia o resto do codigo
COPY . .

# faz o log aparecer na hora no docker logs
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
CMD ["python", "app.py"]