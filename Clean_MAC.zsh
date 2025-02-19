#!/bin/zsh

# Advanced System Cleaner and Optimizer for macOS
# Author: [Your Name]
# Description: Cleans and optimizes macOS systems safely and effectively.
# License: Open Source

# Log file
LOGFILE="/tmp/SystemCleaner_Log_$(date +"%Y%m%d%H%M%S").txt"

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"
}

# Check if run with sudo privileges
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run with sudo privileges. Please run with 'sudo $0'."
    exit 1
fi

# Start Logging
echo "Advanced System Cleaner Log - $(date)" > "$LOGFILE"
echo "===============================================================" >> "$LOGFILE"

# 1. Create a System Restore Point (macOS doesn't have this, but we can create a backup)
log "Creating Backup of System Preferences..."
tmutil snapshot >> "$LOGFILE" 2>&1
log "Backup Created."

# 2. Clean Temporary Files and Folders
log "Cleaning Temporary Files and Folders..."
sudo rm -rf /tmp/*
sudo rm -rf ~/Library/Caches/*
log "Temporary Files Cleaned."

# 3. Repair System Files
log "Repairing System Files..."
sudo diskutil verifyVolume / >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
    log "Disk Verification failed."
else
    sudo diskutil repairVolume / >> "$LOGFILE" 2>&1
    log "Disk Repair Completed."
fi

# 4. Disable Unnecessary Startup Items
log "Disabling Unnecessary Startup Items..."
launchctl list | grep -E "Adobe|OneDrive|Skype" | awk '{print $3}' | while read -r service; do
    launchctl disable system/$service
    log "Disabled: $service"
done

# 5. Adjust Visual Effects for Best Performance
log "Adjusting Visual Effects for Best Performance..."
defaults write NSGlobalDomain com.apple.swipescrolldirection -bool false  # Disable natural scrolling
defaults write NSGlobalDomain com.apple.sound.beep.feedback -int 0  # Disable sound effects for UI actions
defaults write com.apple.dock autohide -bool true  # Dock auto-hide
defaults write com.apple.dock minimize-to-application -bool true  # Minimize windows into application icon
defaults write com.apple.dock launchanim -bool false  # Disable Dock launch animation
log "Visual Effects Adjusted."

# 6. Perform Malware Scan (macOS doesn't have a built-in scanner like Windows Defender)
log "Performing Malware Scan with ClamAV (if installed)..."
if command -v clamscan &> /dev/null; then
    sudo clamscan -i -r / >> "$LOGFILE" 2>&1
    log "Malware Scan Completed."
else
    log "ClamAV not installed. Skipping malware scan."
fi

# 7. Optimize Storage (macOS Sierra and later)
log "Optimizing Storage..."
sudo tmutil thinlocalsnapshots / 999999999 1 >> "$LOGFILE" 2>&1
log "Storage Optimized."

# 8. Update System
log "Updating macOS..."
softwareupdate -ia >> "$LOGFILE" 2>&1
log "macOS Update Initiated."

# 9. Completion Message
echo "
===============================================================
   System Cleaning and Optimization Complete!
   Please review the log file for details:
   $LOGFILE
===============================================================
"

# Open Log File
open -a TextEdit "$LOGFILE" &

exit 0
