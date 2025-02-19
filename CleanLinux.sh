#!/bin/bash

# Advanced System Cleaner and Optimizer for Linux
# Author: [Your Name]
# Description: Cleans and optimizes Linux systems safely and effectively.
# License: Open Source

# Log file
LOGFILE="/tmp/SystemCleaner_Log_$(date +"%Y%m%d%H%M%S").txt"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"
}

# Check if run with root privileges
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run with sudo or as root. Please run with 'sudo $0'."
    exit 1
fi

# Start Logging
echo "Advanced System Cleaner Log - $(date)" > "$LOGFILE"
echo "===============================================================" >> "$LOGFILE"

# 1. Clean Temporary Files and Folders
log "Cleaning Temporary Files and Folders..."
rm -rf /tmp/*
rm -rf /var/tmp/*
log "Temporary Files Cleaned."

# 2. Clear System Logs (except current run logs)
log "Clearing Old System Logs..."
find /var/log -type f -name "*.log" -not -name "*.gz" -exec truncate -s 0 {} \;
log "System Logs Cleared."

# 3. Remove Old Kernel Versions (Debian/Ubuntu based systems)
if [ -f /etc/debian_version ]; then
    log "Removing Old Kernel Versions..."
    apt-get remove --purge -y $(dpkg -l 'linux-*' | sed '/^ii/!d;/'"$(uname -r | sed "s/\(.*\)-\([^0-9]\+\)/\1/")"'/d;s/^[^ ]* [^ ]* \([^ ]*\).*/\1/;/[0-9]/!d' | head -n -1) >> "$LOGFILE" 2>&1
    log "Old Kernels Removed."
fi

# 4. Clean Package Manager Cache
if [ -f /etc/debian_version ]; then
    log "Cleaning APT Cache..."
    apt-get clean -y >> "$LOGFILE" 2>&1
    log "APT Cache Cleaned."
elif [ -f /etc/redhat-release ]; then
    log "Cleaning YUM/DNF Cache..."
    yum clean all -y >> "$LOGFILE" 2>&1 || dnf clean all -y >> "$LOGFILE" 2>&1
    log "YUM/DNF Cache Cleaned."
fi

# 5. Optimize System Services
log "Optimizing System Services..."
systemctl disable cups.service bluetooth.service avahi-daemon.service >> "$LOGFILE" 2>&1
systemctl stop cups.service bluetooth.service avahi-daemon.service >> "$LOGFILE" 2>&1
log "Services Optimized."

# 6. Update System
log "Updating System..."
if [ -f /etc/debian_version ]; then
    apt-get update && apt-get upgrade -y >> "$LOGFILE" 2>&1
elif [ -f /etc/redhat-release ]; then
    yum update -y >> "$LOGFILE" 2>&1 || dnf update -y >> "$LOGFILE" 2>&1
fi
log "System Update Initiated."

# 7. Clear Thumbnails Cache
log "Clearing Thumbnails Cache..."
rm -rf ~/.cache/thumbnails/* >> "$LOGFILE" 2>&1
log "Thumbnails Cache Cleared."

# 8. Optimize Swap Usage
log "Optimizing Swap Usage..."
echo "vm.swappiness=10" >> /etc/sysctl.conf
sysctl -p >> "$LOGFILE" 2>&1
log "Swap Optimization Applied."

# 9. Completion Message
echo "
===============================================================
   System Cleaning and Optimization Complete!
   Please review the log file for details:
   $LOGFILE
==============================================================="

# Open Log File
less "$LOGFILE"

exit 0
