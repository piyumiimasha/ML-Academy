```yaml
tasks:
  - id: 1
    description: Create PySpark utility modules (spark_session.py, spark_utils.py)
    status: DONE
    dependencies: []
    subtasks:
      - Create spark_session.py for centralized SparkSession management
      - Create spark_utils.py for common PySpark utility functions

  - id: 2
    description: Migrate data_ingestion.py from pandas to PySpark
    status: DONE
    dependencies: [1]
    subtasks:
      - Refactor DataIngestor abstract class for PySpark
      - Implement PySpark CSV reader
      - Implement PySpark Excel reader
      - Add Parquet support

  - id: 3
    description: Migrate data processing modules
    status: DONE
    dependencies: [1, 2]
    subtasks:
      - Migrate handle_missing_values.py to PySpark
      - Migrate outlier_detection.py to PySpark
      - Migrate data_splitter.py to PySpark

  - id: 4
    description: Migrate feature engineering modules
    status: DONE
    dependencies: [1, 3]
    subtasks:
      - Migrate feature_binning.py to PySpark (Bucketizer)
      - Migrate feature_encoding.py to PySpark (StringIndexer, OneHotEncoder)
      - Migrate feature_scaling.py to PySpark (MinMaxScaler)

  - id: 5
    description: Update data_pipeline.py to use PySpark modules
    status: IN_PROGRESS
    dependencies: [2, 3, 4]
    subtasks:
      - Replace pandas imports with PySpark modules
      - Update pipeline logic for PySpark DataFrames
      - Add Parquet output support
      - Save fitted preprocessing models

  - id: 6
    description: Update training and inference pipelines
    status: PENDING
    dependencies: [5]
    subtasks:
      - Update training_pipeline.py to support Parquet data
      - Update streaming_inference_pipeline.py for PySpark preprocessing
      - Ensure backward compatibility with CSV format

  - id: 7
    description: Test complete PySpark pipeline
    status: PENDING
    dependencies: [6]
    subtasks:
      - Test data pipeline with sample data
      - Verify output format compatibility
      - Performance benchmarking
      - Validate model training with new data

  - id: 8
    description: Update all files to show both pandas and PySpark implementations
    status: IN_PROGRESS
    dependencies: [1, 2, 3, 4, 5]
    subtasks:
      - Add pandas code as comments
      - Keep PySpark implementation active
      - Add clear section headers
      - Ensure educational clarity for students
```
