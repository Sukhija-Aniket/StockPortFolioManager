#!/bin/bash

# Build script that reads version from shared/setup.py and builds Docker containers

# Function to extract version from setup.py
get_version_from_setup() {
    local setup_file="shared/setup.py"
    if [ -f "$setup_file" ]; then
        # Extract version from setup.py using grep and sed
        local version=$(grep -o "version=['\"][^'\"]*['\"]" "$setup_file" | sed "s/version=['\"]//;s/['\"]//")
        echo "$version"
    else
        echo "v0.1.14"  # Default fallback
    fi
}

# Get the current version
VERSION=$(get_version_from_setup)
echo "Building with shared library version: $VERSION"

# Export the version as environment variable
export SHARED_VERSION="$VERSION"

# Build the containers
echo "Building Docker containers..."
docker-compose build

echo "Build completed with version: $VERSION"