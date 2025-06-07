#!/bin/bash
# Unreal Speech Test Launcher

echo "🚀 Unreal Speech POC Test Launcher"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Change to script directory
cd "$(dirname "$0")"

# Check for API key
if [ -z "$UNREALSPEECH_API_KEY" ] || [ "$UNREALSPEECH_API_KEY" = "YOUR_API_KEY_HERE" ]; then
    echo "⚠️  No API key found!"
    echo ""
    echo "Running in OFFLINE/SIMULATION mode..."
    echo ""
    echo "To get full functionality:"
    echo "1. Sign up at https://unrealspeech.com"
    echo "2. Get your API key (250K characters free)"
    echo "3. Run: export UNREALSPEECH_API_KEY='your_key_here'"
    echo ""
fi

# Install requirements if needed
echo "📦 Checking requirements..."
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null

# Menu
while true; do
    echo ""
    echo "Select a test to run:"
    echo "1. Quick Test (no API key needed)"
    echo "2. Behavior Simulation (no API key needed)"
    echo "3. Offline Demo UI (no API key needed)"
    echo "4. Interactive Test Runner"
    echo "0. Exit"
    echo ""
    read -p "Enter choice (0-4): " choice

    case $choice in
        1)
            echo "Running quick test..."
            python3 quick_test.py
            ;;
        2)
            echo "Running behavior simulation..."
            python3 simulate_behavior.py
            ;;
        3)
            echo "Starting offline demo server..."
            echo "Opening http://localhost:5004 in your browser..."
            python3 offline_demo.py &
            SERVER_PID=$!
            sleep 2
            
            # Try to open browser
            if command -v open &> /dev/null; then
                open http://localhost:5004
            elif command -v xdg-open &> /dev/null; then
                xdg-open http://localhost:5004
            else
                echo "Please open http://localhost:5004 in your browser"
            fi
            
            echo ""
            echo "Press Enter to stop the server..."
            read
            kill $SERVER_PID 2>/dev/null
            echo "Server stopped"
            ;;
        4)
            echo "Starting interactive test runner..."
            python3 run_tests.py
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read
done
