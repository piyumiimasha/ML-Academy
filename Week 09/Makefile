SHELL := /usr/bin/env bash
.ONESHELL:

.PHONY: all clean install setup-dirs train-pipeline data-pipeline clean-kill help

# Default Python interpreter
PYTHON = python
VENV = .venv/bin/activate
MLFLOW_PORT ?= 5001

# Default target
all: help

# Help target
help:
	@echo "🚀 Production ML System with Kafka Streaming"
	@echo "============================================="
	@echo ""
	@echo "📦 Setup Commands:"
	@echo "  make install             - Install project dependencies and set up environment"
	@echo "  make setup-dirs          - Create necessary directories for pipelines"
	@echo "  make clean               - Clean up artifacts"
	@echo ""
	@echo "🔄 ML Pipeline Commands:"
	@echo "  make data-pipeline       - Run the data pipeline"
	@echo "  make train-pipeline      - Run the training pipeline (PySpark MLlib)"
	@echo "  make batch-inference     - Run the batch inference pipeline"
	@echo ""
	@echo "📊 MLflow Commands:"
	@echo "  make mlflow-ui           - Launch MLflow UI (port $(MLFLOW_PORT))"
	@echo "  make stop-all            - Stop all MLflow servers"
	@echo ""
	@echo "🌊 Kafka Streaming Commands:"
	@echo "  make kafka-install       - Install Kafka natively (first time)"
	@echo "  make kafka-validate      - Validate Kafka installation"
	@echo "  make kafka-format        - Format Kafka storage (first time)"
	@echo "  make kafka-start         - Start native Kafka broker"
	@echo "  make kafka-topics        - Create churn prediction topic"
	@echo "  make kafka-cleanup-topics - Remove unused topics"
	@echo ""
	@echo "📊 Data Production Commands:"
	@echo "  make kafka-producer-stream - Stream events (1/sec for 5 mins)"
	@echo "  make kafka-producer-batch  - Batch produce events"
	@echo ""
	@echo "🤖 ML Processing Commands:"
	@echo "  make kafka-consumer        - Batch ML consumer (process all messages)"
	@echo "  make kafka-consumer-continuous - Continuous ML consumer (real-time)"
	@echo ""
	@echo "🔧 Monitoring Commands:"
	@echo "  make kafka-check         - Check broker status"
	@echo "  make kafka-monitor       - Monitor cluster health"
	@echo "  make kafka-help          - Show all Kafka commands"
	@echo ""
	@echo "🔧 Airflow Orchestration Commands:"
	@echo "  make airflow-init        - Initialize Apache Airflow"
	@echo "  make airflow-start       - Start Airflow in standalone mode"
	@echo "  make airflow-kill        - Kill all Airflow processes"
	@echo "  make airflow-reset       - Reset Airflow database"
	@echo "  make clean-kill          - Kill all processes and clean logs/data"
	@echo ""
	@echo "💡 Quick Start (Batch Processing):"
	@echo "  1. make install && make setup-dirs"
	@echo "  2. make kafka-start-bg && make kafka-topics"
	@echo "  3. make kafka-producer-batch"
	@echo "  4. make kafka-consumer"
	@echo ""
	@echo "🔄 Real-time Streaming Demo:"
	@echo "  1. Terminal 1: make kafka-consumer-continuous"
	@echo "  2. Terminal 2: make kafka-producer-stream"
	@echo "  3. Watch real-time ML processing!"
	@echo "  4. Terminal 3: make kafka-sample-scored (view analytics)"

# ========================================================================================
# SETUP AND ENVIRONMENT COMMANDS
# ========================================================================================

# Install project dependencies and set up environment
install:
	@echo "📦 Installing project dependencies and setting up environment..."
	@echo "Creating virtual environment..."
	@python3 -m venv .venv
	@echo "Activating virtual environment and installing dependencies..."
	@source .venv/bin/activate && pip install --upgrade pip
	@source .venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Installation completed successfully!"
	@echo "To activate the virtual environment, run: source .venv/bin/activate"

# Create necessary directories
setup-dirs:
	@echo "📁 Creating necessary directories..."
	@mkdir -p artifacts/data artifacts/models artifacts/encode
	@mkdir -p artifacts/mlflow_run_artifacts artifacts/mlflow_training_artifacts
	@mkdir -p artifacts/inference_batches
	@mkdir -p data/processed data/raw runtime/kafka-logs runtime/pids
	@echo "✅ Directories created successfully!"

# Clean up
clean:
	@echo "🧹 Cleaning up artifacts..."
	rm -rf artifacts/* mlruns
	@echo "✅ Cleanup completed!"

# ========================================================================================
# ML PIPELINE COMMANDS (PySpark MLlib Only)
# ========================================================================================

# Run data pipeline
data-pipeline: setup-dirs
	@echo "🔄 Start running data pipeline..."
	@source $(VENV) && $(PYTHON) pipelines/data_pipeline.py
	@echo "✅ Data pipeline completed successfully!"

# Run training pipeline (PySpark MLlib)
train-pipeline: setup-dirs
	@echo "🎯 Running PySpark MLlib training pipeline..."
	@source $(VENV) && $(PYTHON) pipelines/training_pipeline.py
	@echo "✅ Training pipeline completed successfully!"

# Run streaming inference pipeline
batch-inference: setup-dirs
	@echo "🔮 Running batch inference pipeline..."
	@source $(VENV) && $(PYTHON) pipelines/batch_inference_pipeline.py
	@echo "✅ Batch inference completed successfully!"

# Comprehensive cleanup and kill command
clean-kill:
	@echo "🧹 Comprehensive cleanup and kill operation..."
	@echo "=============================================="
	@echo "⚠️  This will kill all processes and remove logs/data (NOT code)"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo ""
	@echo "🛑 Killing all processes..."
	@pkill -f kafka || echo "No Kafka processes found"
	@pkill -f airflow || echo "No Airflow processes found"
	@pkill -f mlflow || echo "No MLflow processes found"
	@pkill -f spark || echo "No Spark processes found"
	@pkill -f java.*kafka || echo "No Java Kafka processes found"
	@echo ""
	@echo "🗑️  Removing logs and data directories..."
	@rm -rf runtime/kafka-logs/ || echo "Kafka logs not found"
	@rm -rf runtime/pids/ || echo "PID files not found"
	@rm -rf runtime/kafka.log || echo "Kafka log file not found"
	@echo "🗃️  Completely removing Airflow directory (clears all execution history)..."
	@rm -rf .airflow/ || echo "Airflow directory not found"
	@rm -rf mlruns/ || echo "MLflow runs not found"
	@rm -rf artifacts/mlflow_*/ || echo "MLflow artifacts not found"
	@rm -rf artifacts/data/streaming_checkpoints/ || echo "Streaming checkpoints not found"
	@find . -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -path "./.venv" -prune -o -name "*.pyc" -delete 2>/dev/null || true
	@echo ""
	@echo "🔍 Freeing up ports..."
	@lsof -ti:5000,8080,8793,8794,9092,9093 | xargs kill -9 2>/dev/null || echo "No processes using ML/Kafka ports"
	@echo ""
	@echo "✅ Cleanup completed successfully!"
	@echo "Ready for fresh start with: make setup"

# ========================================================================================
# MLFLOW COMMANDS
# ========================================================================================

mlflow-ui:
	@echo "📊 Launching MLflow UI..."
	@echo "MLflow UI will be available at: http://localhost:$(MLFLOW_PORT)"
	@echo "Press Ctrl+C to stop the server"
	@source $(VENV) && mlflow ui --host 0.0.0.0 --port $(MLFLOW_PORT)

# Stop all running MLflow servers
stop-all:
	@echo "🛑 Stopping all MLflow servers..."
	@echo "Finding MLflow processes on port $(MLFLOW_PORT)..."
	@-lsof -ti:$(MLFLOW_PORT) | xargs kill -9 2>/dev/null || true
	@echo "Finding other MLflow UI processes..."
	@-ps aux | grep '[m]lflow ui' | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@-ps aux | grep '[g]unicorn.*mlflow' | awk '{print $$2}' | xargs kill -9 2>/dev/null || true
	@echo "✅ All MLflow servers have been stopped"

# ========================================================================================
# NATIVE KAFKA STREAMING COMMANDS
# ========================================================================================

# Configuration
KAFKA_CONF := kafka/server.properties
KAFKA_LOG_DIR := runtime/kafka-logs
PID_DIR := runtime/pids

kafka-format:
	@echo "🔧 Formatting native Kafka storage (KRaft mode)..."
	@if [ -z "$$KAFKA_HOME" ]; then \
		echo "❌ KAFKA_HOME not set. Please install Kafka natively and set KAFKA_HOME"; \
		echo "💡 Installation guide: README_KAFKA.md"; \
		exit 1; \
	fi
	@echo "📁 Creating runtime directories..."
	@mkdir -p runtime/kafka-logs runtime/pids
	@echo "🔑 Generating cluster UUID..."
	@CLUSTER_ID=$$($${KAFKA_HOME}/bin/kafka-storage.sh random-uuid); \
	echo "Using Cluster ID: $$CLUSTER_ID"; \
	$${KAFKA_HOME}/bin/kafka-storage.sh format -t $$CLUSTER_ID -c "$(KAFKA_CONF)"
	@echo "✅ Native Kafka storage formatted successfully"

kafka-start-bg:
	@echo "🚀 Starting native Kafka broker in background..."
	@if [ -z "$$KAFKA_HOME" ]; then \
		echo "❌ KAFKA_HOME not set"; \
		exit 1; \
	fi
	@mkdir -p $(PID_DIR)
	@nohup $${KAFKA_HOME}/bin/kafka-server-start.sh "$(KAFKA_CONF)" > runtime/kafka.log 2>&1 & \
	echo $$! > $(PID_DIR)/kafka.pid
	@echo "✅ Kafka broker started in background (PID: $$(cat $(PID_DIR)/kafka.pid))"
	@echo "📄 Logs: runtime/kafka.log"

kafka-stop:
	@echo "🛑 Stopping native Kafka broker..."
	@if [ -z "$$KAFKA_HOME" ]; then \
		echo "❌ KAFKA_HOME not set"; \
		exit 1; \
	fi
	@if [ -f "$(PID_DIR)/kafka.pid" ]; then \
		PID=$$(cat $(PID_DIR)/kafka.pid); \
		echo "🔍 Found Kafka PID: $$PID"; \
		kill $$PID || true; \
		rm -f $(PID_DIR)/kafka.pid; \
		echo "✅ Kafka broker stopped"; \
	else \
		echo "⚠️ PID file not found, trying graceful shutdown..."; \
		$${KAFKA_HOME}/bin/kafka-server-stop.sh || true; \
	fi

kafka-topics:
	@echo "📋 Creating churn prediction topics on native broker..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker at localhost:9092"; \
		echo "💡 Please start broker with 'make kafka-start' in another terminal"; \
		exit 1; \
	fi
	@echo "🔮 Creating churn_predictions topic..."
	@kafka-topics.sh --bootstrap-server localhost:9092 --create --topic churn_predictions --partitions 1 --replication-factor 1 --if-not-exists
	@echo "🔮 Creating churn_predictions_scored topic..."
	@kafka-topics.sh --bootstrap-server localhost:9092 --create --topic churn_predictions_scored --partitions 1 --replication-factor 1 --if-not-exists
	@echo "✅ Churn predictions topics created successfully"
	@echo "📋 Current topics on native broker:"
	@kafka-topics.sh --bootstrap-server localhost:9092 --list

kafka-producer-stream:
	@echo "🌊 Starting Kafka streaming producer (real data sampling)..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker"; \
		echo "💡 Please start broker with 'make kafka-start'"; \
		exit 1; \
	fi
	@echo "🎯 Streaming real customer events to localhost:9092 (1 event/sec for 5 mins)"
	@source $(VENV) && python pipelines/kafka_producer.py --mode streaming --rate 1 --duration 300


kafka-producer-batch:
	@echo "📦 Starting Kafka batch producer (real data sampling)..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker"; \
		echo "💡 Please start broker with 'make kafka-start'"; \
		exit 1; \
	fi
	@echo "📊 Batch processing 100 real customer events to localhost:9092"
	@source $(VENV) && python pipelines/kafka_producer.py --mode batch --num-events 100

kafka-consumer:
	@echo "🌊 Starting Kafka batch consumer with ML predictions..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker"; \
		echo "💡 Please start broker with 'make kafka-start'"; \
		exit 1; \
	fi
	@echo "🎯 Processing messages in batches with ML predictions"
	@source $(VENV) && python pipelines/kafka_batch_consumer.py

kafka-consumer-continuous:
	@echo "🔄 Starting continuous Kafka consumer monitoring..."
	@echo "📡 Monitoring for NEW messages (real-time ML processing)"
	@echo "🛑 Press Ctrl+C to stop monitoring"
	@source $(VENV) && python pipelines/kafka_batch_consumer.py --continuous --poll-interval 5
	
kafka-check:
	@echo "🔍 Checking native Kafka broker status..."
	@if kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "✅ Native Kafka broker is running at localhost:9092"; \
		echo "📋 Available topics:"; \
		kafka-topics.sh --bootstrap-server localhost:9092 --list; \
		echo "📊 Broker information:"; \
		kafka-broker-api-versions.sh --bootstrap-server localhost:9092 | head -1; \
	else \
		echo "❌ Cannot connect to native Kafka broker at localhost:9092"; \
		echo "💡 Please start with 'make kafka-start' in another terminal"; \
		echo "💡 Or check installation with 'make kafka-validate'"; \
	fi
	
kafka-sample-scored:
	@echo "📊 Analyzing churn prediction results..."
	@if kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q churn_predictions_scored; then \
		source $(VENV) && python scripts/kafka_analytics.py; \
	else \
		echo "❌ churn_predictions_scored topic not found. Run 'make kafka-topics' first."; \
	fi

kafka-cleanup-topics:
	@echo "🧹 Cleaning up unused Kafka topics..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker"; \
		echo "💡 Please start broker with 'make kafka-start'"; \
		exit 1; \
	fi
	@echo "Removing unused topics (keeping only churn_predictions)..."
	@for topic in customer_events model_updates data_quality_alerts; do \
		if kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q "$$topic"; then \
			echo "🗑️ Deleting topic: $$topic"; \
			kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic "$$topic"; \
		else \
			echo "✅ Topic $$topic not found (already clean)"; \
		fi; \
	done
	@echo "✅ Topic cleanup completed"
	@echo "📋 Remaining topics:"
	@kafka-topics.sh --bootstrap-server localhost:9092 --list

kafka-flush-messages:
	@echo "🗑️ Flushing all messages from Kafka topics..."
	@if ! kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then \
		echo "❌ Cannot connect to native Kafka broker"; \
		echo "💡 Please start broker with 'make kafka-start'"; \
		exit 1; \
	fi
	@echo "Deleting and recreating topics to flush all messages..."
	@kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic churn_predictions 2>/dev/null || echo "Topic churn_predictions not found"
	@kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic churn_predictions_scored 2>/dev/null || echo "Topic churn_predictions_scored not found"
	@sleep 2
	@echo "🔮 Creating churn_predictions topic..."
	@kafka-topics.sh --bootstrap-server localhost:9092 --create --topic churn_predictions --partitions 1 --replication-factor 1
	@echo "🔮 Creating churn_predictions_scored topic..."
	@kafka-topics.sh --bootstrap-server localhost:9092 --create --topic churn_predictions_scored --partitions 1 --replication-factor 1
	@echo "✅ All messages flushed - topics are now empty"
	@echo "📋 Current topics:"
	@kafka-topics.sh --bootstrap-server localhost:9092 --list

kafka-reset:
	@echo "🧹 Resetting Kafka data (destructive operation)..."
	@read -p "⚠️ This will delete all Kafka data. Continue? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "🛑 Stopping all Kafka processes..."
	@pkill -f kafka || echo "No Kafka processes found"
	@sleep 2
	@echo "🔧 Force killing port users..."
	@lsof -ti:9092,9093 | xargs kill -9 2>/dev/null || echo "Ports already free"
	@sleep 1
	@echo "🗑️ Removing Kafka data directory..."
	@rm -rf $(KAFKA_LOG_DIR)
	@echo "🗑️ Removing PID files..."
	@rm -f $(PID_DIR)/kafka.pid
	@echo "✅ Kafka reset completed. Run 'make kafka-format' to reinitialize"

kafka-help:
	@echo "🔧 Native Kafka Commands Help"
	@echo "=================================================="
	@echo "Installation Commands:"
	@echo "  kafka-install    - Install Kafka natively (first time)"
	@echo "  kafka-validate   - Validate installation"
	@echo ""
	@echo "Setup Commands:"
	@echo "  kafka-format     - Format Kafka storage (first time)"
	@echo "  kafka-start      - Start native Kafka broker"
	@echo "  kafka-start-bg   - Start broker in background"
	@echo "  kafka-stop       - Stop native Kafka broker"
	@echo "  kafka-topics     - Create churn prediction topic"
	@echo "  kafka-cleanup-topics - Remove unused topics"
	@echo ""
	@echo "Data Commands:"
	@echo "  kafka-producer-stream  - Start streaming producer (real data)"
	@echo "  kafka-producer-batch   - Start batch producer (real data)"
	@echo "  kafka-consumer         - Start batch ML consumer"
	@echo "  kafka-consumer-continuous - Start continuous ML consumer"
	@echo ""
	@echo "Monitoring Commands:"
	@echo "  kafka-check      - Check broker status"
	@echo "  kafka-monitor    - Monitor cluster health"
	@echo "  kafka-sample     - Sample input topic messages"
	@echo "  kafka-sample-scored - Show prediction analytics & statistics"
	@echo "  kafka-sample-raw - Sample raw scored messages"
	@echo "  kafka-test-event-driven - Test event-driven DAG logic"
	@echo ""
	@echo "Utility Commands:"
	@echo "  kafka-demo       - Show demo instructions"
	@echo "  kafka-reset      - Reset all Kafka data"
	@echo "  kafka-clean-restart - Complete cleanup and restart"
	@echo "  kafka-help       - Show this help"
	@echo ""
	@echo "📚 For detailed setup: README_KAFKA.md"

# ========================================================================================
# APACHE AIRFLOW ORCHESTRATION COMMANDS
# ========================================================================================

airflow-init:
	@echo "🔧 Initializing Apache Airflow..."
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONPATH="$(shell pwd):$$PYTHONPATH" && \
	source $(VENV) && \
	pip install "apache-airflow>=2.10.0,<3.0.0" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.9.txt" && \
	pip install apache-airflow-providers-apache-spark && \
	airflow db migrate && \
	airflow users create -u admin -p admin -r Admin -e admin@example.com -f Admin -l User && \
	mkdir -p .airflow/dags && find dags -name "*.py" -exec cp {} .airflow/dags/ \;
	@echo "✅ Airflow initialized successfully!"

airflow-start:
	@echo "🚀 Starting Airflow in standalone mode..."
	@echo "Checking for port conflicts..."
	@if lsof -ti:8080,8793,8794 >/dev/null 2>&1; then \
		echo "⚠️  Airflow ports are in use. Cleaning up first..."; \
		$(MAKE) airflow-kill; \
		sleep 3; \
	fi
	@echo "Ensuring DAGs are copied..."
	@find dags -name "*.py" -exec cp {} .airflow/dags/ \; 2>/dev/null || true
	@echo "Starting Airflow in standalone mode..."
	@echo "🌐 Webserver will be available at http://localhost:8080"
	@echo "🔑 Login with: admin / admin"
	@export AIRFLOW_HOME="$(shell pwd)/.airflow" && \
	export PYTHONPATH="$(shell pwd):$$PYTHONPATH" && \
	export PYTHONWARNINGS="ignore::DeprecationWarning" && \
	source $(VENV) && \
	airflow standalone

airflow-kill:
	@echo "🛑 Killing all Airflow processes..."
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
	@echo "✅ All Airflow processes killed and ports freed successfully!"

airflow-reset:
	@echo "🔄 Resetting Airflow database and fixing login issues..."
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
	@echo "✅ Airflow reset complete! Login: admin/admin"
	@echo "Start with: make airflow-start"

# Re-run-all command removed - use individual commands instead
