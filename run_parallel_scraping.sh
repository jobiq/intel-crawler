#!/bin/bash

# Script to run N docker containers for M pages in parallel
# Usage: ./run_parallel_scraping.sh <num_containers> <pages_per_container>
# Example: ./run_parallel_scraping.sh 4 10

set -e

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <num_containers> <pages_per_container>"
    echo "Example: $0 4 10"
    echo "This will run 4 containers, each scraping 10 pages"
    exit 1
fi

NUM_CONTAINERS=$1
PAGES_PER_CONTAINER=$2

# Validate inputs are positive integers
if ! [[ "$NUM_CONTAINERS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Number of containers must be a positive integer"
    exit 1
fi

if ! [[ "$PAGES_PER_CONTAINER" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Pages per container must be a positive integer"
    exit 1
fi

echo "Starting $NUM_CONTAINERS containers, each scraping $PAGES_PER_CONTAINER pages..."
echo "Total pages to scrape: $((NUM_CONTAINERS * PAGES_PER_CONTAINER))"
echo "----------------------------------------"

# Array to store background process PIDs
PIDS=()

# Function to cleanup background processes on script exit
cleanup() {
    echo "Cleaning up background processes..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start containers in parallel
for i in $(seq 1 $NUM_CONTAINERS); do
    echo "Starting container $i/$NUM_CONTAINERS..."
    
    # Run docker container in background
    docker run --rm \
        --platform=linux/amd64 \
        -v "$(pwd)":/app \
        -w /app \
        jobiq-scraper \
        python -m scrape --pages $PAGES_PER_CONTAINER --scrapers 1 &
    
    # Store the PID of the background process
    CURRENT_PID=$!
    PIDS+=($CURRENT_PID)
    
    echo "Container $i started with PID $CURRENT_PID"
    
    # Small delay to avoid overwhelming the system
    sleep 1
done

echo "----------------------------------------"
echo "All $NUM_CONTAINERS containers started. Waiting for completion..."

# Wait for all background processes to complete
FAILED_COUNT=0
for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"
    container_num=$((i + 1))
    
    echo "Waiting for container $container_num (PID: $pid)..."
    
    if wait "$pid"; then
        echo "✓ Container $container_num completed successfully"
    else
        echo "✗ Container $container_num failed"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done

echo "----------------------------------------"
echo "All containers finished!"
echo "Successful: $((NUM_CONTAINERS - FAILED_COUNT))/$NUM_CONTAINERS"
echo "Failed: $FAILED_COUNT/$NUM_CONTAINERS"

if [ $FAILED_COUNT -eq 0 ]; then
    echo "All scraping tasks completed successfully! 🎉"
    exit 0
else
    echo "Some scraping tasks failed. Check the logs above for details."
    exit 1
fi
