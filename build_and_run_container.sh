if docker ps -a --format '{{.Names}}' | grep -Eq "^newsscrapertelebot-container$"; then
    echo "newsscrapertelebot-container exists. Removing it..."
    docker rm newsscrapertelebot-container
else
    echo "Container newsscrapertelebot-container does not exist. Continuing to build..."
fi

docker build -t newsscrapertelebot:latest .
docker run --env-file .env.prod -p 8000:8000 --name newsscrapertelebot-container newsscrapertelebot:latest
