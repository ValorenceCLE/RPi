#!/bin/bash

# Install necessary packages (Samba)
echo "Installing Samba..."
sudo apt install samba -y

# Prompt the user for SSD drive path
echo "Please enter the SSD device path (e.g., /dev/sda1):"
read ssd_path

# Create a mount point for the SSD
echo "Creating mount point..."
sudo mkdir -p /mnt/ssd

# Mount the SSD
echo "Mounting SSD..."
sudo mount $ssd_path /mnt/ssd

# Add the SSD to fstab for automatic mounting on boot
echo "Adding SSD to fstab..."
echo "$ssd_path /mnt/ssd ext4 defaults 0 0" | sudo tee -a /etc/fstab

# Configure Samba
echo "Configuring Samba..."
sudo tee -a /etc/samba/smb.conf > /dev/null <<EOT

[SSD]
path = /mnt/ssd
writeable = yes
browseable = yes
create mask = 0777
directory mask = 0777
public = yes
EOT

# Set Samba password for user pi
echo "Setting Samba password for user pi..."
sudo smbpasswd -a pi

# Restart Samba to apply changes
echo "Restarting Samba..."
sudo systemctl restart smbd

# Display the IP address of the Raspberry Pi
pi_ip=$(hostname -I | awk '{print $1}')
echo "Setup complete! You can access the SSD at \\$pi_ip\SSD"

# Final message to configure camera
echo "Now log into your Axis Q6135 IP camera, go to Setup > Storage > Network Share, and configure the following details:"
echo "Address: \\\\$pi_ip\\SSD"
echo "Username: pi"
echo "Password: (the password you set for Samba)"
echo "Done!"
