#!/bin/bash

# Configuration
ROOT_DIR="/home/admin/RPi"
REPO_URL="https://github.com/ValorenceCLE/RPi.git"
BRANCH="main"
LOG_FILE="/home/admin/startup.log"

# Step 1: Create or append to the log file with a timestamped header
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    echo -e "\n\n<---------$(date)--------->" >> "$LOG_FILE"
    echo "Log file created." >> "$LOG_FILE"
else
    echo -e "\n\n<---------$(date)--------->" >> "$LOG_FILE"
    echo "Log file already exists, appending to it." >> "$LOG_FILE"
fi

# Step 2: Clean up log file if it's too large
if [ $(stat -c%s "$LOG_FILE") -gt 1000000 ]; then
    truncate -s 0 "$LOG_FILE"
    echo "Log file was too large and was truncated." >> "$LOG_FILE"
fi

# Function for logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYSTEM_STARTUP] [$1] $2" | tee -a "$LOG_FILE"
}

# Step 3: Perform system checks
system_checks() {
    log "INFO" "Performing system checks..."
    echo "Disk space check:" >> "$LOG_FILE"
    df -h / >> "$LOG_FILE"

    echo "Memory usage check:" >> "$LOG_FILE"
    free -h >> "$LOG_FILE"

    echo "CPU load check:" >> "$LOG_FILE"
    uptime >> "$LOG_FILE"
    log "INFO" "System checks completed."
}

# Step 4: Wait for network to come online
wait_for_network() {
    local MAX_WAIT_LOCAL=300  # Max wait time for local network (5 minutes)
    local MAX_WAIT_INTERNET=180  # Max wait time for external internet (3 minutes)
    local WAIT_TIME=10
    local TOTAL_WAIT=0

    # Wait for local network
    log "INFO" "Waiting for local network (192.168.1.1) to come online..."
    while ! /bin/ping -c 1 192.168.1.1 &> /dev/null; do
        sleep "$WAIT_TIME"
        TOTAL_WAIT=$((TOTAL_WAIT + WAIT_TIME))
        if [ "$TOTAL_WAIT" -ge "$MAX_WAIT_LOCAL" ]; then
            log "ERROR" "Local network did not come online after $((MAX_WAIT_LOCAL / 60)) minutes."
            exit 1
        fi
    done
    log "INFO" "Local network is online. Waited $TOTAL_WAIT seconds."

    # Reset wait timer for external internet check
    TOTAL_WAIT=0
    log "INFO" "Checking external internet connectivity (8.8.8.8)..."
    while ! /bin/ping -c 1 8.8.8.8 &> /dev/null; do
        sleep "$WAIT_TIME"
        TOTAL_WAIT=$((TOTAL_WAIT + WAIT_TIME))
        if [ "$TOTAL_WAIT" -ge "$MAX_WAIT_INTERNET" ]; then
            log "WARNING" "Internet is not accessible after $((MAX_WAIT_INTERNET / 60)) minutes. Proceeding without repository updates."
            INTERNET_DOWN=true
            return
        fi
    done
    log "INFO" "External internet is online. Waited $TOTAL_WAIT seconds."
}

# Step 5: Update the repository and check for rebuild
update_repository() {
    if [ "$INTERNET_DOWN" = true ]; then
        log "WARNING" "Skipping repository update due to lack of internet connectivity."
        return
    fi

    log "INFO" "Starting repository update process..."
    cd "$ROOT_DIR" || { log "ERROR" "Failed to change directory to $ROOT_DIR."; exit 1; }
    log "INFO" "Changed to repository directory: $ROOT_DIR"

    # Ensure directory is marked safe
    sudo git config --global --add safe.directory "$ROOT_DIR"

    # Fetch updates
    log "INFO" "Fetching updates from remote repository..."
    git fetch origin
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/$BRANCH)

    if [ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]; then
        log "INFO" "No updates found. Repository is already up to date."
        UPDATE_FOUND=false
    else
        log "INFO" "Updates found. Pulling changes..."
        git reset --hard origin/$BRANCH
        UPDATE_FOUND=true
    fi

    # Check for rebuild trigger
    if [ "$UPDATE_FOUND" = true ]; then
        log "INFO" "Checking if updates require a Docker rebuild..."
        CHANGED_FILES=$(git diff --name-only "$LOCAL_COMMIT" "$REMOTE_COMMIT")

        if echo "$CHANGED_FILES" | grep -q -E '(Dockerfile|docker-compose.yml|requirements.txt)'; then
            log "INFO" "Changes detected in files that require a Docker rebuild:"
            echo "$CHANGED_FILES" | tee -a "$LOG_FILE"
            REBUILD_REQUIRED=true
        else
            log "INFO" "No changes requiring a Docker rebuild."
            REBUILD_REQUIRED=false
        fi
    fi
}

# Step 6: Start Docker services
start_docker_services() {
    log "INFO" "Starting Docker services..."
    if [ -f "$ROOT_DIR/docker-compose.yml" ]; then
        if [ "$REBUILD_REQUIRED" = true ]; then
            log "INFO" "Rebuilding Docker images due to updates..."
            if docker-compose -f "$ROOT_DIR/docker-compose.yml" build; then
                log "INFO" "Docker images rebuilt successfully."
            else
                log "ERROR" "Failed to rebuild Docker images."
                exit 1
            fi
        fi

        log "INFO" "Starting Docker containers..."
        if docker-compose -f "$ROOT_DIR/docker-compose.yml" up -d; then
            log "INFO" "Docker Compose services started successfully."
        else
            log "ERROR" "Failed to start Docker Compose services."
            exit 1
        fi
    else
        log "WARNING" "No docker-compose.yml found. Skipping Docker startup."
    fi
}

# Main Execution
system_checks
wait_for_network
update_repository
start_docker_services
system_checks  # Final system checks after startup

log "INFO" "Startup process completed successfully."
