# PowerShell script to replace make commands for Week 07
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("help", "all", "install", "setup-dirs", "data-pipeline", "data-pipeline-rebuild", "train-pipeline", "streaming-inference", "run-all", "clean", "mlflow-ui", "stop-all")]
    [string]$Target = "help"
)

# Ensure we're in the right directory
Set-Location $PSScriptRoot

# MLflow configuration
$MLFLOW_PORT = 5001

switch ($Target) {
    "help" {
        Write-Host "Available targets:"
        Write-Host "  .\make.ps1 install             - Install project dependencies and set up environment"
        Write-Host "  .\make.ps1 setup-dirs          - Create necessary directories for pipelines"
        Write-Host "  .\make.ps1 data-pipeline       - Run the data pipeline"
        Write-Host "  .\make.ps1 data-pipeline-rebuild - Run data pipeline with force rebuild"
        Write-Host "  .\make.ps1 train-pipeline      - Run the training pipeline"
        Write-Host "  .\make.ps1 streaming-inference - Run the streaming inference pipeline with the sample JSON"
        Write-Host "  .\make.ps1 run-all             - Run all pipelines in sequence"
        Write-Host "  .\make.ps1 clean               - Clean up artifacts"
        Write-Host "  .\make.ps1 mlflow-ui           - Launch MLflow UI"
        Write-Host "  .\make.ps1 stop-all            - Stop all MLflow servers"
    }
    "all" {
        # Default target - call help
        & $PSCommandPath help
    }
    "install" {
        Write-Host "Installing project dependencies and setting up environment..."
        if (-not (Test-Path ".venv")) {
            Write-Host "Creating virtual environment..."
            python -m venv .venv
        }
        Write-Host "Activating virtual environment and installing dependencies..."
        .\.venv\Scripts\Activate.ps1
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        Write-Host "Installation completed successfully!"
        Write-Host "To activate the virtual environment, run: .\.venv\Scripts\Activate.ps1"
    }
    "setup-dirs" {
        Write-Host "Creating necessary directories..."
        New-Item -ItemType Directory -Force -Path "artifacts/data" | Out-Null
        New-Item -ItemType Directory -Force -Path "artifacts/models" | Out-Null
        New-Item -ItemType Directory -Force -Path "artifacts/encode" | Out-Null
        New-Item -ItemType Directory -Force -Path "artifacts/mlflow_run_artifacts" | Out-Null
        New-Item -ItemType Directory -Force -Path "artifacts/mlflow_training_artifacts" | Out-Null
        New-Item -ItemType Directory -Force -Path "artifacts/inference_batches" | Out-Null
        New-Item -ItemType Directory -Force -Path "data/processed" | Out-Null
        New-Item -ItemType Directory -Force -Path "data/raw" | Out-Null
        Write-Host "Directories created successfully!"
    }
    "data-pipeline" {
        Write-Host "Start running data pipeline..."
        & $PSCommandPath setup-dirs
        .\.venv\Scripts\Activate.ps1
        python pipelines/data_pipeline.py
        Write-Host "Data pipeline completed successfully!"
    }
    "data-pipeline-rebuild" {
        Write-Host "Running data pipeline with force rebuild..."
        & $PSCommandPath setup-dirs
        .\.venv\Scripts\Activate.ps1
        python -c "from pipelines.data_pipeline import data_pipeline; data_pipeline(force_rebuild=True)"
    }
    "train-pipeline" {
        Write-Host "Running training pipeline..."
        & $PSCommandPath setup-dirs
        .\.venv\Scripts\Activate.ps1
        python pipelines/training_pipeline.py
    }
    "streaming-inference" {
        Write-Host "Running streaming inference pipeline with sample JSON..."
        & $PSCommandPath setup-dirs
        .\.venv\Scripts\Activate.ps1
        python pipelines/streaming_inference_pipeline.py
    }
    "run-all" {
        Write-Host "Running all pipelines in sequence..."
        & $PSCommandPath setup-dirs
        Write-Host "========================================"
        Write-Host "Step 1: Running data pipeline"
        Write-Host "========================================"
        .\.venv\Scripts\Activate.ps1
        python pipelines/data_pipeline.py
        Write-Host "`n========================================"
        Write-Host "Step 2: Running training pipeline"
        Write-Host "========================================"
        python pipelines/training_pipeline.py
        Write-Host "`n========================================"
        Write-Host "Step 3: Running streaming inference pipeline"
        Write-Host "========================================"
        python pipelines/streaming_inference_pipeline.py
        Write-Host "`n========================================"
        Write-Host "All pipelines completed successfully!"
        Write-Host "========================================"
    }
    "clean" {
        Write-Host "Cleaning up artifacts..."
        Remove-Item -Recurse -Force "artifacts\*" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "mlruns" -ErrorAction SilentlyContinue
        Write-Host "Cleanup completed!"
    }
    "mlflow-ui" {
        Write-Host "Launching MLflow UI..."
        Write-Host "MLflow UI will be available at: http://localhost:$MLFLOW_PORT"
        Write-Host "Press Ctrl+C to stop the server"
        .\.venv\Scripts\Activate.ps1
        mlflow ui --host 0.0.0.0 --port $MLFLOW_PORT
    }
    "stop-all" {
        Write-Host "Stopping all MLflow servers..."
        Write-Host "Finding MLflow processes on port $MLFLOW_PORT..."
        
        # Find and kill processes on MLflow port
        $processes = Get-NetTCPConnection -LocalPort $MLFLOW_PORT -ErrorAction SilentlyContinue
        if ($processes) {
            $processes | ForEach-Object {
                $processId = (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Id
                if ($processId) {
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                }
            }
        }
        
        # Find and kill MLflow UI processes by name
        Get-Process -Name "*mlflow*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Get-Process -Name "*gunicorn*" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*mlflow*" } | Stop-Process -Force -ErrorAction SilentlyContinue
        
        Write-Host "✅ All MLflow servers have been stopped"
    }
}
