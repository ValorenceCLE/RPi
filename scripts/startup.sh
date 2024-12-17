#!/bin/bash

# Configuration
ROOT_DIR="/home/admin/RPi"
REPO_URL="https://github.com/ValorenceCLE/RPi.git"
BRANCH="main"
LOG_FILE="/home/admin/startup.log"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') [SYSTEM_STARTUP] [$1] $2" | tee -a "$LOG_FILE"
}

# Ensure log file exists
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    log "INFO" "Log file created."
fi

wait_for_network() {
    log "INFO" "Waiting for network to be up..."
    MAX_WAIT=600
    WAIT_TIME=10
    TOTAL_WAIT=0

    while true; do
        if /bin/ping -c 1 192.168.1.1 &> /dev/null; then
            log "INFO" "Network is up."
            break
        else
            log "WARNING" "Network not ready, waiting..."
            sleep "$WAIT_TIME"
            TOTAL_WAIT=$((TOTAL_WAIT + WAIT_TIME))
        fi

        if [ "$TOTAL_WAIT" -ge "$MAX_WAIT" ]; then
            log "ERROR" "Network did not come online after $((MAX_WAIT / 60)) minutes."
            exit 1
        fi
    done
}

update_repository() {
    log "INFO" "Starting repository update process..."

    # Ensure Git is installed
    if ! command -v git &> /dev/null; then
        log "INFO" "Git is not installed. Installing..."
        sudo apt-get install -y git
    fi

    # Ensure HOME is set for Git operations
    if [ -z "$HOME" ]; then
        export HOME="/home/admin"
        log "INFO" "Setting HOME environment variable to $HOME"
    fi

    # Ensure global safe directory configuration
    sudo git config --global --add safe.directory "$ROOT_DIR"

    # Navigate to the repository directory
    if [ ! -d "$ROOT_DIR" ]; then
        log "ERROR" "Repository directory $ROOT_DIR does not exist."
        exit 1
    fi
    cd "$ROOT_DIR" || { log "ERROR" "Failed to change directory to $ROOT_DIR."; exit 1; }
    log "INFO" "Changed to repository directory: $ROOT_DIR"

    # Initialize Git repository if it doesn't exist
    if [ ! -d ".git" ]; then
        log "INFO" "No Git repository found. Initializing..."
        git init
        git remote add origin "$REPO_URL"
        git fetch origin
        git checkout -b "$BRANCH" || git checkout "$BRANCH"
        log "INFO" "Git repository initialized and connected to remote."
    else
        log "INFO" "Git repository already initialized."
    fi

    # Fetch updates and reset to the latest state
    log "INFO" "Fetching updates from remote repository..."
    OUTPUT=$(git fetch origin 2>&1)
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to fetch updates. Output: $OUTPUT"
        exit 1
    else
        log "INFO" "Fetch output: $OUTPUT"
    fi

    log "INFO" "Resetting repository to latest state on branch $BRANCH..."
    OUTPUT=$(git reset --hard origin/$BRANCH 2>&1)
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to reset repository. Output: $OUTPUT"
        exit 1
    else
        log "INFO" "Reset output: $OUTPUT"
    fi

    log "INFO" "Repository successfully updated to the latest version."
}

start_docker_services() {
    log "INFO" "Starting Docker services..."
    if [ -f "$ROOT_DIR/docker-compose.yml" ]; then
        docker-compose -f "$ROOT_DIR/docker-compose.yml" up -d
        log "INFO" "Docker Compose application started successfully."
    else
        log "WARNING" "No docker-compose.yml found. Skipping Docker startup."
    fi
}

wait_for_network
update_repository
start_docker_services
log "INFO" "Startup process completed successfully."
