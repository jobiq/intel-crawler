#!/bin/bash

# Script to run N docker containers for M pages in parallel with tiled display
# Usage: ./run_parallel_scraping.sh <num_containers> <pages_per_container>
# Example: ./run_parallel_scraping.sh 4 10
# Requires: tmux

set -e

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required but not installed."
    echo "Install with: brew install tmux (macOS) or apt-get install tmux (Ubuntu)"
    exit 1
fi

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <num_containers> <pages_per_container>"
    echo "Example: $0 4 10"
    echo "This will run 4 containers, each scraping 10 pages"
    exit 1
fi

# Function to calculate optimal grid dimensions
calculate_grid() {
    local total=$1
    local rows=1
    local cols=1
    
    # Find the best rows x cols that can fit total containers
    # Try to make it as square as possible
    for ((r=1; r*r<=total; r++)); do
        if ((total % r == 0)); then
            rows=$r
            cols=$((total / r))
        else
            # Find the closest fit
            local c=$((total / r))
            if (((r * c) < total)); then
                c=$((c + 1))
            fi
            if (((r * c) >= total && (r * c) < (rows * cols))); then
                rows=$r
                cols=$c
            fi
        fi
    done
    
    # Make sure we have enough cells
    while ((rows * cols < total)); do
        if ((rows <= cols)); then
            rows=$((rows + 1))
        else
            cols=$((cols + 1))
        fi
    done
    
    echo "$rows $cols"
}

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

# Calculate grid dimensions
read -r ROWS COLS <<< "$(calculate_grid $NUM_CONTAINERS)"
echo "Grid layout: ${ROWS}x${COLS}"
echo "----------------------------------------"

# Create logs directory if it doesn't exist
mkdir -p logs

# Create unique session name
SESSION_NAME="scraper-$(date +%s)"

# Create tmux session
tmux new-session -d -s "$SESSION_NAME" -x 120 -y 40

# Function to create tiled layout
setup_tmux_grid() {
    local session=$1
    local total_containers=$2
    local rows=$3
    local cols=$4
    
    # Create additional panes
    for ((i=1; i<total_containers; i++)); do
        tmux split-window -t "$session" -v
        tmux select-layout -t "$session" tiled
    done
    
    # Adjust layout to be more organized
    tmux select-layout -t "$session" tiled
}

# Setup the grid
setup_tmux_grid "$SESSION_NAME" "$NUM_CONTAINERS" "$ROWS" "$COLS"

# Start containers in each pane
for ((i=0; i<NUM_CONTAINERS; i++)); do
    container_num=$((i + 1))
    pane_id="${SESSION_NAME}:0.$i"
    
    echo "Starting container $container_num in pane $i..."
    
    # Create unique container name and log file
    CONTAINER_NAME="scraper-$container_num-$(date +%s)"
    LOG_FILE="logs/container-$container_num.log"
    
    # Send command to specific pane
    tmux send-keys -t "$pane_id" "echo 'Container $container_num - Scraping $PAGES_PER_CONTAINER pages'" C-m
    tmux send-keys -t "$pane_id" "echo 'Log file: $LOG_FILE'" C-m
    tmux send-keys -t "$pane_id" "echo '--- Starting Docker container ---'" C-m
    tmux send-keys -t "$pane_id" "docker run --rm --name \"$CONTAINER_NAME\" --platform=linux/amd64 -v \"\$(pwd)\":/app -w /app jobiq-scraper python -m scrape --pages $PAGES_PER_CONTAINER --scrapers 1 2>&1 | tee \"$LOG_FILE\"" C-m
    
    # Small delay to avoid overwhelming the system
    sleep 0.5
done

echo "----------------------------------------"
echo "All $NUM_CONTAINERS containers started in tmux session: $SESSION_NAME"
echo "Grid layout: ${ROWS}x${COLS}"
echo "Logs are being written to the logs/ directory"
echo ""
echo "To attach to the tmux session: tmux attach -t $SESSION_NAME"
echo "To detach from tmux session: Ctrl+B, then D"
echo "To kill the session: tmux kill-session -t $SESSION_NAME"
echo "----------------------------------------"

# Attach to the tmux session
echo "Attaching to tmux session..."
tmux attach -t "$SESSION_NAME"

# After detaching or session ends, check results
echo ""
echo "Tmux session ended. Checking results..."
echo "Container logs are available in the logs/ directory:"
for i in $(seq 1 $NUM_CONTAINERS); do
    if [ -f "logs/container-$i.log" ]; then
        LOG_SIZE=$(wc -l < "logs/container-$i.log")
        echo "  - logs/container-$i.log ($LOG_SIZE lines)"
    fi
done

echo ""
echo "All scraping tasks have completed! 🎉"
echo ""
echo "Session '$SESSION_NAME' has ended."
echo "You can review the logs in the logs/ directory or restart the session if needed."

exit 0
