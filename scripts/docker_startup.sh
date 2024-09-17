#!/bin/bash
# Docker Startup 

LOGFILE="/home/admin/startup.log"
log(){
    echo "$(date +'%Y-%m-%d %H:%M:%S') [DOCKER_STARTUP] [$1] $2" >> "$LOGFILE"
}

if [ ! -f "$LOGFILE" ]; then
    touch "$LOGFILE"
    chmod 644 "$LOGFILE"
    log "INFO" "Log file created."
else
    log "INFO" "Log file already exists, appending to it."
fi

log "INFO" "Starting Docker services."

wait_for_network(){
    log "INFO" "Waiting for network to be up..."
    MAX_WAIT=300  # Maximum wait time in seconds (5 minutes)
    WAIT_TIME=10  # Time to wait between checks
    TOTAL_WAIT=0
    MAX_RETRIES=5  # Maximum number of retries for network check
    RETRIES=0

    while true; do 
        if /bin/ping -c 1 8.8.8.8 &>/dev/null; then
            log "INFO" "Network is up."
            break
        else
            log "WARNING" "Network not ready, waiting..."
            sleep $WAIT_TIME
            TOTAL_WAIT=$((TOTAL_WAIT + WAIT_TIME))
        fi

        if [ "$TOTAL_WAIT" -ge "$MAX_WAIT" ]; then
            if [ "$RETRIES" -ge "$MAX_RETRIES" ]; then
                log "ERROR" "Network did not come online after maximum retries."
                exit 1
            fi
            log "WARNING" "Network still not online after $((TOTAL_WAIT / 60)) minutes. Retrying..."
            /usr/bin/pinctrl set 21 dl  # Turn off the Router GPIO pin
            sleep 3                       # Wait for 3 seconds before turning it back on
            /usr/bin/pinctrl set 21 dh  # Turn on the Router GPIO pin again
            TOTAL_WAIT=0                  # Reset the wait timer after resetting the router
            RETRIES=$((RETRIES + 1))      # Increment the retry counter
            log "INFO" "Router GPIO reset complete, continuing to check network..."
        fi
    done
}
start_docker_services(){
    #cd /home/admin/RPi
    cd /home/admin/MyDockerProject || {
        log "ERROR" "Failed to change directory to MyDockerProject."
        exit 1
    }
    if [ -f "docker-compose.yml" ]; then
        if docker-compose up -d; then
            log "INFO" "Docker Compose application started successfully."
        else
            log "ERROR" "Error starting Docker Compose application."
            log "INFO" "Attempting to restart Docker Compose application."
            docker-compose down
            sleep 3
            if docker-compose up -d; then
                log "INFO" "Docker Compose application started successfully on retry."
            else
                log "ERROR" "Error starting Docker Compose application on retry."
                exit 1
            fi
        fi
    else
        log "WARN" "No docker-compose.yml found, skipping Docker startup."
    fi
}

wait_for_network
start_docker_services
log "INFO" "Docker services started successfully."