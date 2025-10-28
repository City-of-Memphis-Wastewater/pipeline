# --- Configuration ---
# Your GHCR path based on the document
# FIX: To prevent GHCR from creating the nested package name (pipeline/pipeline-eds),
# we must remove the repository name from the image path, allowing it to be
# correctly named 'pipeline-eds' while still being associated with the 'pipeline' repo.
GHCR_PATH="ghcr.io/city-of-memphis-wastewater/pipeline-eds"
LOCAL_IMAGE_NAME="pipeline-eds"

# --- 1. Define the Tag ---
# Use the latest Git tag available. If no tag exists, it falls back to a short commit SHA.
IMAGE_TAG=$(git describe --tags --always)

# Uncomment the line below and comment the line above if you prefer using a short commit SHA instead:
# IMAGE_TAG=$(git rev-parse --short HEAD)

if [ -z "$IMAGE_TAG" ]; then
    echo "Error: Could not determine an IMAGE_TAG. Ensure you are in a git repository or use a fixed tag." >&2
    exit 1
fi

echo "--- Publishing Image with Tag: $IMAGE_TAG ---"

# --- 2. Tag and Push the Versioned Image ---
# Apply the full registry path and the version tag
echo "Tagging image as $GHCR_PATH:$IMAGE_TAG"
docker tag $LOCAL_IMAGE_NAME $GHCR_PATH:$IMAGE_TAG

# Push the version tag
echo "Pushing $GHCR_PATH:$IMAGE_TAG..."
docker push $GHCR_PATH:$IMAGE_TAG


# --- 3. Tag and Push the 'latest' Image (Recommended) ---
# Tag the image again with the 'latest' alias
echo "Tagging image as $GHCR_PATH:latest"
docker tag $LOCAL_IMAGE_NAME $GHCR_PATH:latest

# Push the 'latest' tag
echo "Pushing $GHCR_PATH:latest..."
docker push $GHCR_PATH:latest

echo "Image is now available at: $GHCR_PATH:$IMAGE_TAG and $GHCR_PATH:latest"
