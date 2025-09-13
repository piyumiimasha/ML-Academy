# Enhanced MLflow Artifact Tracking for ML Pipelines

This project demonstrates production-ready machine learning pipelines with comprehensive MLflow artifact tracking, focusing on customer churn prediction.

## 🎯 Project Overview

A complete ML system with enhanced MLflow tracking that provides:
- **Comprehensive Data Lineage**: Track data from raw input to final model predictions
- **Rich Artifact Management**: Automated logging of datasets, models, visualizations, and metadata
- **Production-Ready Monitoring**: Real-time inference tracking and performance monitoring
- **Complete Reproducibility**: All artifacts needed to reproduce experiments and results

## 📁 Project Structure

```
Week 05_06/
├── README.md                          # This file - comprehensive project documentation
├── Makefile                           # Build and deployment automation
├── config.yaml                        # Central configuration management
├── requirements.txt                   # Python dependencies
├── stepplan.md                       # Task planning and dependency tracking
│
├── artifacts/                         # Generated artifacts and models
│   ├── data/                         # Processed datasets
│   │   ├── X_train.csv               # Training features
│   │   ├── X_test.csv                # Testing features
│   │   ├── Y_train.csv               # Training labels
│   │   └── Y_test.csv                # Testing labels
│   ├── encode/                       # Feature encoders
│   │   ├── Gender_encoder.json       # Gender feature encoder
│   │   └── Geography_encoder.json    # Geography feature encoder
│   ├── models/                       # Trained models
│   │   └── churn_analysis.joblib     # Main trained model
│   └── mlflow_run_artifacts/         # MLflow-specific artifacts
│       └── {run_id}/                 # Run-specific artifacts
│           ├── visualizations_*/     # Data visualizations by stage
│           └── final_csv_files/      # Final dataset metadata
│
├── data/                             # Data storage
│   ├── raw/                          # Original raw data
│   │   └── ChurnModelling.csv        # Raw customer churn dataset
│   └── processed/                    # Intermediate processed data
│       └── imputed.csv               # Data after missing value handling
│
├── mlruns/                           # MLflow tracking storage
│   ├── 0/                           # Default experiment
│   ├── models/                      # MLflow model registry
│   └── {experiment_id}/             # Experiment-specific runs
│       └── {run_id}/                # Individual run artifacts
│           ├── artifacts/           # Run artifacts
│           ├── metrics/             # Logged metrics
│           ├── params/              # Logged parameters
│           └── tags/                # Run tags and metadata
│
├── pipelines/                        # ML pipeline implementations
│   ├── __pycache__/                 # Python cache files
│   ├── data_pipeline.py             # ✨ Enhanced data processing pipeline
│   ├── training_pipeline.py         # ✨ Enhanced model training pipeline
│   └── streaming_inference_pipeline.py # ✨ Enhanced inference pipeline
│
├── src/                             # Core ML modules
│   ├── __pycache__/                 # Python cache files
│   ├── __init__.py                  # Package initialization
│   ├── data_ingestion.py            # Data loading and validation
│   ├── data_spiltter.py             # Train/test splitting strategies
│   ├── feature_binning.py           # Feature binning transformations
│   ├── feature_encoding.py          # Feature encoding strategies
│   ├── feature_scaling.py           # Feature scaling transformations
│   ├── handle_missing_values.py     # Missing value handling strategies
│   ├── model_building.py            # Model architecture definitions
│   ├── model_evaluation.py          # Model evaluation metrics
│   ├── model_inference.py           # Model inference and prediction
│   ├── model_training.py            # Model training orchestration
│   └── outlier_detection.py         # Outlier detection and handling
│
└── utils/                           # Utility modules
    ├── __pycache__/                 # Python cache files
    ├── config.py                    # Configuration management
    └── mlflow_utils.py              # MLflow tracking utilities
```

## 🚀 Key Enhancements Implemented

### 1. **Enhanced Data Pipeline** (`pipelines/data_pipeline.py`)

#### **📊 Comprehensive Data Profiling**
- **Stage-wise Tracking**: Profiles data at each processing stage (raw → missing_handled → outliers_removed → encoded → final)
- **Rich Visualizations**: Automatic generation of distribution plots, correlation matrices
- **Dataset Artifacts**: Proper MLflow dataset tracking with lineage and versioning

#### **🔍 Data Quality Monitoring**
- **Metrics Tracking**: Rows, columns, missing values, memory usage at each stage
- **Transformation Logging**: Before/after metrics for each transformation step
- **Error Handling**: Graceful handling of processing failures with detailed logging

#### **📁 Artifact Management**
```python
# Example: Data profiling and visualization
create_data_visualizations(df, 'raw', run_artifacts_dir)
log_stage_metrics(df, 'raw')

# MLflow dataset tracking
raw_dataset = mlflow.data.from_pandas(df, source=data_path, name="raw_churn_data")
mlflow.log_input(raw_dataset, context="raw_data")
```

### 2. **Enhanced Training Pipeline** (`pipelines/training_pipeline.py`)

#### **🎯 Model Performance Tracking**
- **Comprehensive Visualizations**: Confusion matrices, ROC curves, feature importance plots
- **Training Metadata**: Training time, model size, complexity metrics
- **Performance Analytics**: Detailed model performance analysis and comparison

#### **📈 Model Artifacts**
```python
# Example: Model performance visualization
create_model_performance_visualizations(model, X_test, y_test, evaluation_results, 
                                      run_artifacts_dir, 'XGboost')

# Model metadata logging
log_model_metadata(model, 'XGboost', model_params, training_time, run_artifacts_dir)
```

### 3. **Enhanced Inference Pipeline** (`pipelines/streaming_inference_pipeline.py`)

#### **⚡ Real-time Monitoring**
- **Batch Processing**: Configurable batch sizes for efficient logging (default: 100 predictions)
- **Performance Tracking**: Inference time, prediction distributions, risk categorization
- **Production Monitoring**: Real-time model performance metrics

#### **📊 Prediction Analytics**
```python
# Example: Inference tracking
class InferenceTracker:
    def track_prediction(self, input_data, prediction_result, inference_time):
        # Tracks individual predictions with metadata
        # Logs batches automatically when batch size is reached
```

## 🛠️ MLflow Artifacts Generated

### **Data Pipeline Artifacts**
```
MLflow Run Artifacts:
├── raw_data/                         # Original dataset
├── visualizations/                   # Stage-wise data visualizations
│   ├── raw/                         # Raw data distributions
│   ├── encoded/                     # Post-encoding visualizations  
│   └── final/                       # Final processed data plots
├── final_datasets/                   # Train/test CSV files with metadata
│   ├── X_train.csv, X_test.csv      # Feature datasets
│   ├── Y_train.csv, Y_test.csv      # Label datasets
│   └── final_csv_metadata.json      # Comprehensive metadata
└── processed_datasets/               # Final processed datasets
```

### **Training Pipeline Artifacts**
```
MLflow Run Artifacts:
├── model_performance/                # Model performance analysis
│   ├── XGboost/                     # Model-specific artifacts
│   │   ├── confusion_matrix_XGboost.png
│   │   ├── roc_curve_XGboost.png
│   │   ├── feature_importance_XGboost.png
│   │   └── prediction_distribution_XGboost.png
├── model_metadata/                   # Model metadata and information
│   └── model_metadata_XGboost.json
├── trained_models/                   # Actual model files
│   └── churn_analysis.joblib
└── training_summary/                 # Complete training summary
    └── training_summary.json
```

### **Inference Pipeline Artifacts**
```
MLflow Run Artifacts:
├── inference_batches/                # Prediction batch logs
│   ├── inference_batch_20241219_143022.json
│   └── inference_batch_20241219_143122.json
└── prediction_analytics/             # Inference performance metrics
```

## 📊 MLflow Tracking Features

### **Dataset Tracking**
- **MLflow Datasets**: Proper dataset versioning and lineage tracking
- **Schema Evolution**: Automatic tracking of schema changes
- **Data Lineage**: Complete traceability from raw data to final models

### **Metrics Logged**
```python
# Data Pipeline Metrics
- raw_rows, raw_columns, raw_missing_values, raw_memory_mb
- missing_handled_rows_removed, outliers_removed_count
- final_train_samples, final_test_samples, final_features
- train_class_0, train_class_1, test_class_0, test_class_1

# Training Pipeline Metrics  
- training_time_seconds, model_size_mb, model_complexity
- accuracy, precision, recall, f1, roc_auc
- XGboost_training_time_seconds, XGboost_model_size_mb

# Inference Pipeline Metrics
- batch_size, avg_inference_time_ms, avg_churn_probability
- high_risk_predictions, medium_risk_predictions, low_risk_predictions
```

### **Parameters Logged**
```python
# Pipeline Configuration
- final_feature_names, preprocessing_steps, data_pipeline_version
- model_type, training_strategy, sklearn_version
- feature_encoding_applied, feature_scaling_applied

# Model Parameters
- n_estimators, max_depth, random_state
- test_size, missing_value_strategy, outlier_detection_method
```

## 🚀 Getting Started

### **Prerequisites**
```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### **Running the Pipelines**

#### **1. Data Pipeline**
```bash
# Run data processing pipeline
python pipelines/data_pipeline.py

# Or using Makefile
make data-pipeline
```

#### **2. Training Pipeline**
```bash
# Run model training pipeline
python pipelines/training_pipeline.py

# Or using Makefile  
make train-model
```

#### **3. Inference Pipeline**
```bash
# Run streaming inference
python pipelines/streaming_inference_pipeline.py

# Or using Makefile
make inference
```

### **MLflow UI**
```bash
# Start MLflow UI to view experiments and artifacts
mlflow ui

# Access at: http://localhost:5000
```

## 📈 Key Benefits

### **🔍 Enhanced Observability**
- **Complete Lineage**: Track data and model lineage from raw input to predictions
- **Rich Visualizations**: Automatic generation of insightful plots and charts
- **Comprehensive Metrics**: Detailed metrics at every pipeline stage

### **🚀 Production Ready**
- **Error Handling**: Robust error handling with graceful degradation
- **Monitoring**: Real-time inference monitoring and performance tracking  
- **Reproducibility**: Complete artifact tracking for experiment reproduction

### **⚡ Developer Experience**
- **Automated Tracking**: Minimal code changes for maximum tracking benefit
- **Rich Metadata**: Comprehensive metadata for all artifacts
- **Easy Debugging**: Quick access to intermediate results and visualizations

## 🔧 Configuration

The system is configured through `config.yaml`:

```yaml
mlflow:
  tracking_uri: "file:./mlruns"
  experiment_name: "Zuu Crew Churn Analysis"  
  model_registry_name: "churn_prediction"
  artifact_path: "model"
  run_name_prefix: "churn_run"
  tags:
    project: "customer_churn_prediction"
    team: "ml_engineering" 
    environment: "development"
  autolog: true
```

## 📊 Performance Optimizations

### **Code Efficiency**
- **68% Code Reduction**: Optimized from ~950 lines to ~300 lines in data pipeline
- **Consolidated Functions**: Streamlined helper functions for better maintainability
- **Essential Visualizations**: Focus on most valuable plots and metrics

### **Resource Management**
- **Memory Efficient**: Efficient handling of large datasets with cleanup
- **Batch Processing**: Configurable batch sizes for inference tracking
- **Error Recovery**: Graceful fallbacks when artifact logging fails

## 🎯 Future Enhancements

- **Data Drift Detection**: Monitor for data drift in production
- **Model Registry Management**: Automated model stage transitions  
- **Advanced Monitoring**: Additional performance and quality metrics
- **Integration Testing**: Comprehensive pipeline testing framework

## 📝 Development Notes

This enhanced MLflow tracking system provides:
- **Production-grade logging** throughout all modules
- **Comprehensive error handling** and input validation  
- **Enhanced type safety** and documentation
- **Complete artifact traceability** for ML operations

The implementation follows clean architecture principles with separation of concerns and comprehensive observability for production ML systems.

---

**Built with ❤️ for production-ready machine learning systems**
