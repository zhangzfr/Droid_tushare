#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Define a safe test database directory within the project
TEST_DB_ROOT="$PROJECT_ROOT/test_db_data"

# Create the directory if it doesn't exist
mkdir -p "$TEST_DB_ROOT"

echo "========================================================"
echo "          Tushare DuckDB Safe Test Mode"
echo "========================================================"
echo "Production Data Path: (IGNORED) /Users/robert/Developer/DuckDB"
echo "Test Data Path:       $TEST_DB_ROOT"
echo ""
echo "This session will ONLY read/write to the Test Data Path."
echo "Your production databases are safe."
echo "========================================================"

# Export the DB_ROOT environment variable to override config
export DB_ROOT="$TEST_DB_ROOT"

# Run the python module
# Use the python from the specific conda env if available, else default python
PYTHON_CMD="python"
if [ -f "/Users/robert/miniconda3/envs/qlib-py39/bin/python" ]; then
    PYTHON_CMD="/Users/robert/miniconda3/envs/qlib-py39/bin/python"
fi

"$PYTHON_CMD" -m src.tushare_duckdb.main
