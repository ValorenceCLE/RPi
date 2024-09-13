#!/bin/bash

# This script is meant to be used on startup to bring up services and reconfigure GPIOs.
# Make sure permissions are applied and that it is set up right.
# chmod +x /home/admin/MyDockerProject/scripts/startup.sh
# This can be run automatically on reboot using either systemd or cron with @reboot

# Log file for recording startup events
LOGFILE="$HOME/startup.log"

# Step 1: Create or append to the log file, and clean up entries older than 90 days
if [ ! -f "$LOGFILE" ]; then
    touch "$LOGFILE"
    chmod 644 "$LOGFILE"
    echo -e "\n\n<---------$(date)--------->" >> "$LOGFILE"
    echo "Log file created." >> "$LOGFILE"
else
    echo -e "\n\n<---------$(date)--------->" >> "$LOGFILE"
    echo "Log file already exists, appending to it." >> "$LOGFILE"
fi

# Step 2: Clean up old log file or truncate if it's too large
if [ $(stat -c%s "$LOGFILE") -gt 1000000 ]; then
    truncate -s 0 "$LOGFILE"
    echo "$(date): Log file was too large and was truncated." >> "$LOGFILE"
fi

# Log the start of the script
echo "Startup script started." >> "$LOGFILE"

# Step 3: Drive GPIO pins (turn them on to power up the router)
echo "Powering the system." >> $LOGFILE
pinctrl set 13 op # Configure the Router GPIO pin as output
pinctrl set 17 op # Configure the Camera GPIO pin as output
pinctrl set 5 op  # Configure the Strobe GPIO pin as output
pinctrl set 27 op # Configure the Fan GPIO pin as output

pinctrl set 13 dh # Turn on the Router GPIO pin
pinctrl set 17 dh # Turn on the Camera GPIO pin

if [ $? -eq 0 ]; then
    echo "GPIO pins turned on successfully." >> $LOGFILE
else
    echo "Error turning on GPIO pins. Exiting." >> $LOGFILE
    exit 1
fi

# Step 4: Ensure the network is up before starting services
echo "Waiting for network to be up..." >> $LOGFILE
MAX_WAIT=300  # Maximum wait time in seconds (5 minutes)
WAIT_TIME=10  # Time to wait between checks
TOTAL_WAIT=0

while ! ping -c 1 8.8.8.8 &>/dev/null; do
    echo "$(date): Network not ready, waiting..." >> $LOGFILE
    sleep $WAIT_TIME
    TOTAL_WAIT=$((TOTAL_WAIT + WAIT_TIME))

    # If it's been more than 5 minutes, reset the router GPIOs
    if [ $TOTAL_WAIT -ge $MAX_WAIT ]; then
        echo "Network still not online after 5 minutes. Resetting router GPIO..." >> $LOGFILE
        pinctrl set 13 dl  # Turn off the Router GPIO pin
        sleep 3            # Wait for 3 seconds before turning it back on
        pinctrl set 13 dh  # Turn on the Router GPIO pin again
        TOTAL_WAIT=0       # Reset the wait timer after resetting the router
        echo "Router GPIO reset complete, continuing to check network..." >> $LOGFILE
    fi
done

echo "$(date): Network is up. Proceeding to start Docker services." >> $LOGFILE

# Step 4: Start docker-compose services
cd /home/admin/MyDockerProject
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
    if [ $? -eq 0 ]; then
        echo "Docker Compose application started successfully." >> $LOGFILE
    else
        echo "Error starting Docker Compose application." >> $LOGFILE
        docker-compose down # Attempt to shut down any running services
        sleep 3           # Wait for 3 seconds before exiting
        docker-compose up -d # Retry starting the services
        if [ $? -eq 0 ]; then
            echo "Docker Compose application started successfully on retry." >> $LOGFILE
        else
            echo "Error starting Docker Compose application on retry." >> $LOGFILE
            exit 1
        fi
    fi
else
    echo "No docker-compose.yml found, skipping Docker startup." >> $LOGFILE
fi

echo "Startup script completed." >> $LOGFILE