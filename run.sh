#!/bin/bash

# Try different Python commands in order
PYTHON_COMMANDS=("python3" "python" "python3.9" "python3.10" "python3.11" "python3.7")

for cmd in "${PYTHON_COMMANDS[@]}"; do
  if command -v $cmd &> /dev/null; then
    echo "Using Python command: $cmd"
    $cmd main.py
    exit $?
  fi
done

# If we get here, no Python command was found
echo "Error: Could not find a working Python command. Please install Python 3.6+ and try again."
echo "You can try running one of these commands to install Python:"
echo "  brew install python  # on macOS with Homebrew"
echo "  conda install python # if you're using Anaconda/Miniconda"
exit 1
