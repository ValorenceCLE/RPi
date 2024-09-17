#!/bin/bash
# GPIO Control Script

set -euo pipefail

LOGFILE="/home/admin/startup.log"

log(){
    echo "$(date +'%Y-%m-%d %H:%M:%S') [GPIO_SETUP] [$1] $2" >> "$LOGFILE"
}

if [ ! -f "$LOGFILE" ]; then
    touch "$LOGFILE"
    chmod 644 "$LOGFILE"
    log "INFO" "Log file created."
else
    log "INFO" "Log file already exists, appending to it."
fi

log "INFO" "Starting GPIO setup."
configure_gpio(){
    local pins=(21 20 16 12)
    for pin in "${pins[@]}"; do
        if ! /usr/bin/pinctrl set "$pin" op; then
            log "ERROR" "Failed to configure GPIO pin $pin as output."
            exit 1
        else
            log "INFO" "Configured GPIO pin $pin as output."
        fi
    done
}
activate_gpio(){
    local pins=(21 20)
    for pin in "${pins[@]}"; do
        if ! /usr/bin/pinctrl set "$pin" dh; then
            log "ERROR" "Failed to activate GPIO pin $pin."
            exit 1
        else
            log "INFO" "Activated GPIO pin $pin."
        fi
    done
}

configure_gpio
activate_gpio
log "INFO" "GPIO setup completed successfully."