#!/bin/bash

# Configuration
RESTART_COUNT_FILE="/tmp/restart_count"

# Initialize restart count
if [ -f "$RESTART_COUNT_FILE" ]; then
    RESTART_COUNT=$(cat "$RESTART_COUNT_FILE")
else
    RESTART_COUNT=0
fi

# Main loop
while true; do
    start_time=$(date +%s)
    echo "Starting Python script at $(date)"
    # Run the Python script
    sudo python3 /usr/local/bin/sentinel_mrhat_cam_main.py
    EXIT_CODE=$?
    
    end_time=$(date +%s)
    runtime=$((end_time - start_time))
    echo "Python script exited with code $EXIT_CODE after $runtime seconds"

    # Handle different exit codes
    case $EXIT_CODE in
        0)
            echo "Script exited normally with code 0. Shutting down..."
            RESTART_COUNT=0
            echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"
            exit 0
            ;;
        1)
            if [ $runtime -ge 600 ]; then
                echo "Script ran for 10+ minutes. Resetting restart count."
                RESTART_COUNT=0
            else
                RESTART_COUNT=$((RESTART_COUNT + 1))
            fi
            echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"
            
            if [ $RESTART_COUNT -ge 5 ]; then
                echo "Restarted 5 consecutive times. Rebooting system..."
                sudo reboot
            else
                echo "Script exited with code 1. Restarting Python script (Restart count: $RESTART_COUNT)..."
                continue
            fi
            ;;
        2)
            echo "Script exited with code 2. Rebooting system..."
            sudo reboot
            ;;
        *)
            echo "Script exited with unexpected code $EXIT_CODE. Rebooting system..."
            sudo reboot
            ;;
    esac
done