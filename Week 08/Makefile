SHELL := /usr/bin/env bash
.ONESHELL:

.PHONY: all clean install setup-dirs train-pipeline data-pipeline streaming-inference run-all help re-run-all

# Default Python interpreter
PYTHON = python
VENV = .venv/bin/activate
MLFLOW_PORT ?= 5001

# Default target
all: help

# Help target
help:
	@echo "Available targets:"
	@echo "  make install             - Install project dependencies and set up environment"
	@echo "  make setup-dirs          - Create necessary directories for pipelines"
	@echo "  make data-pipeline       - Run the data pipeline"
	@echo "  make train-pipeline      - Run the training pipeline (PySpark MLlib)"
	@echo "  make train-sklearn       - Run the training pipeline (scikit-learn)"
	@echo "  make train-pyspark       - Run the training pipeline (PySpark MLlib)"
	@echo "  make test-pyspark        - Test PySpark MLlib pipeline"
	@echo "  make streaming-inference - Run the streaming inference pipeline with the sample JSON"
	@echo "  make run-all             - Run all pipelines in sequence"
	@echo "  make clean               - Clean up artifacts"
	@echo "  make airflow-init        - Initialize Apache Airflow"
	@echo "  make airflow-standalone  - Start Airflow in standalone mode"
	@echo "  make airflow-start       - Start Airflow webserver and scheduler"
	@echo "  make airflow-webserver   - Start Airflow webserver only"
	@echo "  make airflow-scheduler   - Start Airflow scheduler only"
	@echo "  make airflow-dags-list   - List all available DAGs"
	@echo "  make airflow-test-data-pipeline    - Test data pipeline DAG"
	@echo "  make airflow-test-training-pipeline - Test training pipeline DAG"
	@echo "  make airflow-test-inference-pipeline - Test inference pipeline DAG"
	@echo "  make airflow-clean       - Clean Airflow database and logs"
	@echo "  make airflow-delete-dags - Delete all DAGs from Airflow UI"
	@echo "  make airflow-kill        - Kill all running Airflow processes"
	@echo "  make airflow-trigger-all - Trigger all DAGs manually for testing"
	@echo "  make airflow-generate-graphs - Generate DAG graph visualizations"
	@echo "  make airflow-health      - Check Airflow health status"
	@echo "  make airflow-clear-stuck - Clear stuck/long-running tasks"
	@echo "  make airflow-reset       - Reset Airflow database and fix login issues"

# Install project dependencies and set up environment
install:
	@echo "Installing project dependencies and setting up environment..."
	@echo "Creating virtual environment..."
	@python3 -m venv .venv
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && pip install --upgrade pip
	@source .venv/bin/activate && pip install -r requirements.txt
	@echo "Installation completed successfully!"
	@echo "To activate the virtual environment, run: source .venv/bin/activate"

# Create necessary directories
setup-dirs:
	@echo "Creating necessary directories..."
	@mkdir -p artifacts/data
	@mkdir -p artifacts/models
	@mkdir -p artifacts/encode
	@mkdir -p artifacts/mlflow_run_artifacts
	@mkdir -p artifacts/mlflow_training_artifacts
	@mkdir -p artifacts/inference_batches
	@mkdir -p data/processed
	@mkdir -p data/raw
	@echo "Directories created successfully!"

# Clean up
clean:
	@echo "Cleaning up artifacts..."
	rm -rf artifacts/*
	rm -rf mlruns
	@echo "Cleanup completed!"

# Run data pipeline
data-pipeline: setup-dirs
	@echo "Start running data pipeline..."
	@source $(VENV) && $(PYTHON) pipelines/data_pipeline.py
	@echo "Data pipeline completed successfully!"

.PHONY: data-pipeline-rebuild
data-pipeline-rebuild: setup-dirs
	@source $(VENV) && $(PYTHON) -c "from pipelines.data_pipeline import data_pipeline; data_pipeline(force_rebuild=True)"

# Run training pipeline (PySpark MLlib by default)
train-pipeline: setup-dirs
	@echo "Running PySpark MLlib training pipeline..."
	@source $(VENV) && $(PYTHON) pipelines/training_pipeline.py

# Run training pipeline with scikit-learn
train-sklearn: setup-dirs
	@echo "Running scikit-learn training pipeline..."
	@source $(VENV) && TRAINING_ENGINE=sklearn $(PYTHON) pipelines/training_pipeline.py

# Run training pipeline with PySpark MLlib
train-pyspark: setup-dirs
	@echo "Running PySpark MLlib training pipeline..."
	@source $(VENV) && TRAINING_ENGINE=pyspark $(PYTHON) pipelines/training_pipeline.py

# Test PySpark MLlib pipeline
test-pyspark: setup-dirs
	@echo "Testing PySpark MLlib pipeline..."
	@source $(VENV) && $(PYTHON) test_pyspark_pipeline.py

# Run streaming inference pipeline with sample JSON
streaming-inference: setup-dirs
	@echo "Running streaming inference pipeline with sample JSON..."
	@source $(VENV) && $(PYTHON) pipelines/streaming_inference_pipeline.py

# Run all pipelines in sequence
run-all: setup-dirs
	@echo "Running all pipelines in sequence..."
	@echo "========================================"
	@echo "Step 1: Running data pipeline"
	@echo "========================================"
	@source $(VENV) && $(PYTHON) pipelines/data_pipeline.py
	@echo "\n========================================"
	@echo "Step 2: Running training pipeline"
	@echo "========================================"
	@source $(VENV) && $(PYTHON) pipelines/training_pipeline.py
	@echo "\n========================================"
	@echo "Step 3: Running streaming inference pipeline"
	@echo "========================================"
	@source $(VENV) && $(PYTHON) pipelines/streaming_inference_pipeline.py
	@echo "\n========================================"
	@echo "All pipelines completed successfully!"
	@echo "========================================"

mlflow-ui:
	@echo "Launching MLflow UI..."
	@echo "MLflow UI will be available at: http://localhost:$(MLFLOW_PORT)"
	@echo "Press Ctrl+C to stop the server"
	@source $(VENV) && mlflow ui --host 0.0.0.0 --port $(MLFLOW_PORT)

# Stop all running MLflow servers
stop-all:
	@echo "Stopping all MLflow servers..."
	@echo "Finding MLflow processes on port $(MLFLOW_PORT)..."
	@-lsof -ti:$(MLFLOW_PORT) | xargs kill -9 2>/dev/null || true
	@echo "Finding other MLflow UI processes..."
	@-ps aux | grep '[m]lflow ui' | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@-ps aux | grep '[g]unicorn.*mlflow' | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@echo "✅ All MLflow servers have been stopped"

# ========================================================================================
# APACHE AIRFLOW ORCHESTRATION TARGETS
# ========================================================================================

airflow-init: ## Initialize Apache Airflow
	@echo "Initializing Apache Airflow..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	source $(VENV) && \
	pip install "apache-airflow>=2.10.0,<3.0.0" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.9.txt" && \
	pip install apache-airflow-providers-apache-spark && \
	airflow db migrate && \
	airflow users create -u admin -p admin -r Admin -e admin@example.com -f Admin -l User && \
	mkdir -p .airflow/dags && find dags -name "*.py" -exec cp {} .airflow/dags/ \;
	@echo "Airflow initialized successfully!"

airflow-webserver: ## Start Airflow webserver
	@echo "Starting Airflow webserver on http://localhost:8080..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	source $(VENV) && \
	airflow webserver --port 8080

airflow-scheduler: ## Start Airflow scheduler
	@echo "Starting Airflow scheduler..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	source $(VENV) && \
	airflow scheduler

airflow-start: ## Start Airflow in standalone mode (simpler for local dev)
	@echo "Checking for port conflicts..."
	@if lsof -ti:8080,8793,8794 >/dev/null 2>&1; then \
		echo "⚠️  Airflow ports are in use. Cleaning up first..."; \
		$(MAKE) airflow-kill; \
		sleep 3; \
	fi
	@echo "Ensuring DAGs are copied..."
	@find dags -name "*.py" -exec cp {} .airflow/dags/ \; 2>/dev/null || true
	@echo "Starting Airflow in standalone mode..."
	@echo "Webserver will be available at http://localhost:8080"
	@echo "Login with: admin / admin"
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow standalone

airflow-start-separate: ## Start Airflow webserver and scheduler separately
	@echo "Starting Airflow webserver and scheduler..."
	@echo "Webserver will be available at http://localhost:8080"
	@echo "Login with: admin / admin"
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	trap "kill 0" INT TERM EXIT && \
	airflow webserver --port 8080 & \
	airflow scheduler

airflow-dags-list: ## List all available DAGs
	@echo "Listing Airflow DAGs..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	source $(VENV) && \
	airflow dags list

airflow-test-data-pipeline: ## Test data pipeline DAG
	@echo "Testing data pipeline DAG..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow tasks test data_pipeline_dag run_data_pipeline 2025-01-01

airflow-test-training-pipeline: ## Test training pipeline DAG
	@echo "Testing training pipeline DAG..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow tasks test training_pipeline_dag run_training_pipeline 2025-01-01

airflow-test-inference-pipeline: ## Test inference pipeline DAG
	@echo "Testing inference pipeline DAG..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow tasks test inference_dag run_inference_pipeline 2025-01-01

airflow-clean: ## Clean Airflow database and logs
	@echo "Cleaning Airflow database and logs..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	rm -rf .airflow/airflow.db .airflow/logs/*

airflow-delete-dags: ## Delete all DAGs from Airflow UI (removes example DAGs too)
	@echo "Stopping Airflow if running..."
	@pkill -f airflow || true
	@echo "Configuring Airflow to hide example DAGs..."
	@source .venv/bin/activate && export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	if ! grep -q "load_examples = False" .airflow/airflow.cfg; then \
		sed -i '' 's/load_examples = True/load_examples = False/g' .airflow/airflow.cfg 2>/dev/null || \
		echo "load_examples = False" >> .airflow/airflow.cfg; \
	fi
	@echo "Deleting project DAG files..."
	@if [ -d ".airflow/dags" ]; then \
		rm -rf .airflow/dags/*; \
	fi
	@echo "All DAGs deleted. Example DAGs will be hidden on next start."
	@echo "To re-add your project DAGs, run: cp dags/* .airflow/dags/"
	@echo "To start Airflow without example DAGs, run: make airflow-standalone"

airflow-kill: ## Kill all running Airflow processes and free ports
	@echo "Killing all Airflow processes..."
	@pkill -f airflow || echo "No Airflow processes found"
	@sleep 2
	@echo "Force killing any remaining Airflow processes..."
	@pkill -9 -f airflow || echo "No remaining processes"
	@sleep 1
	@echo "Freeing Airflow ports (8080, 8793, 8794)..."
	@lsof -ti:8080,8793,8794 | xargs kill -9 2>/dev/null || echo "No processes using Airflow ports"
	@sleep 1
	@echo "Cleaning up PID files..."
	@rm -f .airflow/airflow-webserver.pid .airflow/airflow-scheduler.pid .airflow/airflow-triggerer.pid
	@echo "All Airflow processes killed and ports freed successfully!"

airflow-trigger-all: ## Trigger all DAGs manually for testing
	@echo "Triggering all DAGs..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	echo "Triggering data pipeline..." && \
	airflow dags trigger data_pipeline_dag && \
	echo "Triggering training pipeline..." && \
	airflow dags trigger training_pipeline_dag && \
	echo "Triggering inference pipeline..." && \
	airflow dags trigger inference_dag
	@echo "✅ All DAGs triggered! Check the Web UI at http://localhost:8080"

airflow-health: ## Check Airflow health status
	@echo "Checking Airflow health status..."
	@curl -s http://localhost:8080/health | python -m json.tool || echo "❌ Airflow not responding"
	@echo ""
	@echo "Checking running processes..."
	@ps aux | grep airflow | grep -v grep || echo "❌ No Airflow processes found"

airflow-reset: ## Reset Airflow database and fix login issues
	@echo "Resetting Airflow database and fixing login issues..."
	@$(MAKE) airflow-kill
	@echo "Removing old database and logs..."
	@rm -rf .airflow/airflow.db .airflow/logs/*
	@find . -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -path "./.venv" -prune -o -name "*.pyc" -delete 2>/dev/null || true
	@echo "Reinitializing database..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow db migrate
	@echo "Creating admin user..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow users create -u admin -f Admin -l User -p admin -r Admin -e admin@example.com
	@echo "Copying DAGs..."
	@find dags -name "*.py" -exec cp {} .airflow/dags/ \;
	@echo "✓ Airflow reset complete! Login: admin/admin"
	@echo "Start with: make airflow-standalone"

	@echo "Airflow cleaned successfully!"

re-run-all: ## 🔄 Complete reset: kill processes, clean everything, restart fresh
	@echo "🔄 Starting complete system reset and restart..."
	@echo "=================================================="
	@echo "Step 1/6: Killing all Airflow processes..."
	@$(MAKE) airflow-kill
	@echo ""
	@echo "Step 2/6: Cleaning database, logs, and Python cache files..."
	@rm -rf .airflow/airflow.db .airflow/logs/* .airflow/dags/* 2>/dev/null || true
	@find . -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -path "./.venv" -prune -o -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Database, logs, and Python cache files cleaned"
	@echo ""
	@echo "Step 3/6: Reinitializing Airflow database..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow db migrate
	@echo "✅ Database reinitialized"
	@echo ""
	@echo "Step 4/6: Creating admin user..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow users create -u admin -f Admin -l User -p admin -r Admin -e admin@example.com 2>/dev/null || echo "Admin user already exists"
	@echo "✅ Admin user ready (admin/admin)"
	@echo ""
	@echo "Step 5/6: Copying fresh DAGs..."
	@find dags -name "*.py" -exec cp {} .airflow/dags/ \;
	@echo "✅ DAGs copied:"
	@ls -la .airflow/dags/*.py
	@echo ""
	@echo "Step 6/6: Starting Airflow in standalone mode..."
	@echo "🚀 Starting Airflow standalone..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	export PYTHONPATH="$(shell pwd):$$PYTHONPATH" && \
	source $(VENV) && \
	echo "=== ENVIRONMENT READY ===" && \
	echo "AIRFLOW_HOME: $$AIRFLOW_HOME" && \
	echo "PYTHONPATH: $$PYTHONPATH" && \
	echo "=== STARTING AIRFLOW STANDALONE ===" && \
	echo "🌐 Web UI will be available at: http://localhost:8080" && \
	echo "🔑 Login: admin / admin" && \
	echo "📊 DAGs: data_pipeline_dag (5min), training_pipeline_dag (daily), inference_dag (1min)" && \
	echo "=== AIRFLOW STARTING... ===" && \
	airflow standalone &
	@echo ""
	@echo "=================================================="
	@echo "✅ COMPLETE RESET AND RESTART FINISHED!"
	@echo "🌐 Web UI: http://localhost:8080"
	@echo "🔑 Login: admin / admin"
	@echo "📊 Scheduling:"
	@echo "   - Data Pipeline: Every 5 minutes"
	@echo "   - Training Pipeline: Daily at 1 AM IST"
	@echo "   - Inference Pipeline: Every minute"
	@echo "=================================================="
	@echo "💡 Use 'make airflow-kill' to stop all processes"
	@echo "💡 Use 'make airflow-health' to check status"