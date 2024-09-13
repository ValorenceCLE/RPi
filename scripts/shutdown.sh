#!/bin/bash


# This script is meant to be used as a part of a Cron job to shut down services and reboot the system.
# Make sure permissions are applied and that it is set up right.
# chmod +x /home/admin/MyDockerProject/scripts/shutdown.sh
# Cron Job: crontab -e -1
# 0 4 * * * /home/admin/MyDockerProject/scripts/shutdown.sh
#                       ^^^^^^^^^^^^^^^ This may be different on production deployments


# Log the script execution
# Step 1: Create a log file if it doesn't exist
LOGFILE="$HOME/shutdown.log"

# Step 1: Create or append to the log file, and clean up entries older than 90 days
if [ ! -f "$LOGFILE" ]; then
    touch "$LOGFILE"
    chmod 644 "$LOGFILE"
    echo -e "\n\n<---------$(date)--------->" >> "$LOGFILE"
    echo "Log file created." >> "$LOGFILE"
else
    echo -e"\n\n<---------$(date)--------->" >> "$LOGFILE"
    echo "Log file already exists, appending to it." >> "$LOGFILE"
fi

# Step 2: Clean up old log file or truncate if it's too large
if [ $(stat -c%s "$LOGFILE") -gt 1000000 ]; then
    truncate -s 0 "$LOGFILE"
    echo "Log file was too large and was truncated." >> "$LOGFILE"
fi

# Log the start of the script
echo "Shutdown script started." >> "$LOGFILE"

# Step 2: Perform system checks
echo "Disk space check:" >> $LOGFILE
df -h / >> $LOGFILE

# Check memory usage
echo "Memory usage check:" >> $LOGFILE
free -h >> $LOGFILE

# Check CPU load
echo "CPU load check:" >> $LOGFILE
uptime >> $LOGFILE

# Step 3: Shut down docker-compose services
cd /home/admin/MyDockerProject
if [ -f "docker-compose.yml" ]; then
    docker-compose down
    if [ $? -eq 0 ]; then
        echo "Docker Compose application shut down successfully" | tee -a $LOGFILE
    else
        echo "Error shutting down Docker Compose application" | tee -a $LOGFILE
        exit 1
    fi
else
    echo "No docker-compose.yml found, skipping Docker shutdown" | tee -a $LOGFILE
fi

# Step 4: Turn off GPIO pins
echo "Turning off GPIO pins" >> $LOGFILE
pinctrl set 13 dl # Turn off the Router GPIO pin
pinctrl set 17 dl # Turn off the Camera GPIO pin
pinctrl set 5 dl # Turn off the Strob GPIO pin
pinctrl set 27 dl # Turn off the Fan GPIO pin
if [ $? -eq 0 ]; then
    echo "GPIO pins turned off successfully" >> $LOGFILE
else
    echo "Error turning off GPIO pins" >> $LOGFILE
fi

# Step 6: Reboot the system
echo "Rebooting the system" >> $LOGFILE
sudo reboot