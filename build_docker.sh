docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ghcr.io/city-of-memphis-wastewater/pipeline-eds:multi-dev \
    -f **Dockerfile.multi-dev** . \
    --push