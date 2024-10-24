docker build -t newsscrapertelebot:latest .
docker run --env-file .env.prod -p 8000:8000 --name newsscrapertelebot-container newsscrapertelebot:latest
