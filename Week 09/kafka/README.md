# Native Kafka Setup (No Docker)

This directory contains configuration for running Apache Kafka natively on your system using KRaft mode (no ZooKeeper required).

## Prerequisites

- **Java 17 or higher**: Required for Kafka runtime
- **Apache Kafka 3.7+**: Native installation (not Docker)
- **Python 3.8+**: For the ML pipeline components

## Installation Options

### Option 1: macOS with Homebrew (Recommended for macOS)

```bash
# Install Java 17
brew install openjdk@17

# Install Kafka
brew install kafka

# Set environment variables (add to ~/.zshrc or ~/.bash_profile)
export KAFKA_HOME="$(brew --prefix kafka)/libexec"
export PATH="$KAFKA_HOME/bin:$PATH"

# Verify installation
kafka-topics.sh --version
```

### Option 2: Linux (Ubuntu/Debian)

```bash
# Install Java 17
sudo apt update
sudo apt install -y openjdk-17-jdk

# Download and install Kafka
export KAFKA_VER=3.7.0
cd ~
curl -O https://downloads.apache.org/kafka/$KAFKA_VER/kafka_2.13-$KAFKA_VER.tgz
tar -xzf kafka_2.13-$KAFKA_VER.tgz
mv kafka_2.13-$KAFKA_VER kafka

# Set environment variables (add to ~/.bashrc or ~/.profile)
export KAFKA_HOME="$HOME/kafka"
export PATH="$KAFKA_HOME/bin:$PATH"

# Verify installation
$KAFKA_HOME/bin/kafka-topics.sh --version
```

### Option 3: Manual Download (All Platforms)

1. **Download Kafka**: Visit https://kafka.apache.org/downloads
2. **Choose**: Binary downloads for Scala 2.13 (kafka_2.13-3.7.0.tgz)
3. **Extract**: To your preferred location (e.g., `/opt/kafka` or `~/kafka`)
4. **Set Environment Variables**:
   ```bash
   export KAFKA_HOME="/path/to/your/kafka"
   export PATH="$KAFKA_HOME/bin:$PATH"
   ```

### Option 4: Linux Package Managers

#### CentOS/RHEL/Fedora:
```bash
# Install Java
sudo dnf install -y java-17-openjdk

# Install Kafka (if available in repos)
sudo dnf install -y kafka
```

#### Arch Linux:
```bash
# Install from AUR
yay -S apache-kafka
```

## Quick Start Commands

### 1. Format Storage (First Time Only)
```bash
# Navigate to project directory
cd /path/to/Week_09

# Format Kafka storage directory
make kafka-format
```

### 2. Start Kafka Broker
```bash
# Start the native Kafka broker
make kafka-start

# This runs in foreground - keep terminal open
# Or run in background: make kafka-start &
```

### 3. Create Topics
```bash
# In a new terminal, create required topics
make kafka-topics
```

### 4. Run Streaming Demo
```bash
# Terminal 1: Start streaming consumer
make kafka-consumer

# Terminal 2: Start data producer  
make kafka-producer

# Terminal 3: Monitor system
make kafka-check
```

## Verification Steps

### Check Installation
```bash
# Verify Java installation
java -version
# Should show Java 17 or higher

# Verify Kafka installation
kafka-topics.sh --version
# Should show Kafka version 3.7+

# Check environment variables
echo $KAFKA_HOME
echo $PATH | grep kafka
```

### Test Kafka Broker
```bash
# Start broker (if not running)
make kafka-start

# In another terminal, test connection
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Should connect without errors and show topic list
```

### Test Producer/Consumer
```bash
# Create test topic
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic test --partitions 1 --replication-factor 1

# Start consumer (terminal 1)
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning

# Start producer (terminal 2)
kafka-console-producer.sh --bootstrap-server localhost:9092 --topic test

# Type messages in producer terminal - they should appear in consumer terminal
```

## Directory Structure

After setup, you'll have:

```
Week 09/
├── kafka/
│   ├── server.properties          # KRaft broker configuration
│   └── README.md                  # This file
├── runtime/
│   └── kafka-logs/               # Kafka data directory (auto-created)
│       ├── __cluster_metadata-0/ # KRaft metadata
│       └── customer_events-0/    # Topic data files
```

## Configuration Details

### KRaft Mode Benefits
- **No ZooKeeper**: Simplified architecture
- **Faster Startup**: Reduced dependencies
- **Better Performance**: Lower latency operations
- **Easier Management**: Single process to manage

### Network Configuration
- **Broker Port**: 9092 (for client connections)
- **Controller Port**: 9093 (for internal KRaft operations)
- **Host**: localhost (development setup)

### Storage Configuration
- **Data Directory**: `runtime/kafka-logs/` (relative to project)
- **Retention**: 7 days (168 hours)
- **Compression**: Gzip for efficiency

## Troubleshooting

### Common Issues

#### 1. Java Not Found
```bash
# Install Java 17+
# macOS: brew install openjdk@17
# Linux: sudo apt install openjdk-17-jdk

# Verify installation
java -version
```

#### 2. Kafka Commands Not Found
```bash
# Check KAFKA_HOME
echo $KAFKA_HOME

# If empty, set it:
export KAFKA_HOME="/path/to/kafka"
export PATH="$KAFKA_HOME/bin:$PATH"

# Add to shell profile for persistence
```

#### 3. Permission Denied
```bash
# Make sure Kafka scripts are executable
chmod +x $KAFKA_HOME/bin/*.sh

# Check directory permissions
ls -la runtime/kafka-logs/
```

#### 4. Port Already in Use
```bash
# Check what's using port 9092
lsof -i :9092

# Kill existing process if needed
kill -9 <PID>
```

#### 5. Storage Format Issues
```bash
# Clean and reformat storage
rm -rf runtime/kafka-logs/
make kafka-format
```

### Log Locations

- **Kafka Logs**: Check `$KAFKA_HOME/logs/server.log`
- **Data Directory**: `runtime/kafka-logs/`
- **Application Logs**: Console output from make commands

### Performance Tuning

For production environments, consider adjusting:

```properties
# Increase for better performance
num.partitions=3
num.replica.fetchers=4
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400

# Adjust retention based on requirements
log.retention.hours=168
log.retention.bytes=1073741824
```

## Next Steps

1. **Install Kafka natively** using one of the options above
2. **Set environment variables** (KAFKA_HOME and PATH)
3. **Run verification steps** to ensure proper installation
4. **Use make commands** to start and manage Kafka
5. **Proceed with ML streaming pipeline** setup

## Support

If you encounter issues:

1. **Check Prerequisites**: Ensure Java 17+ and Kafka are properly installed
2. **Verify Environment**: Check KAFKA_HOME and PATH variables
3. **Test Connection**: Use `kafka-topics.sh --bootstrap-server localhost:9092 --list`
4. **Check Logs**: Review `$KAFKA_HOME/logs/server.log` for errors
5. **Clean Setup**: Try `rm -rf runtime/kafka-logs/` and `make kafka-format`

## Educational Notes

### Why Native Kafka?

1. **Learning Focus**: Understand Kafka concepts without container complexity
2. **Development Efficiency**: Direct access to tools and logs
3. **Production Similarity**: Many production environments use native installations
4. **Resource Efficiency**: Lower overhead than containerized solutions

### KRaft vs ZooKeeper

- **KRaft** (Kafka Raft): Modern consensus protocol built into Kafka
- **ZooKeeper**: Legacy external coordination service
- **Migration**: Industry is moving from ZooKeeper to KRaft
- **Benefits**: Simpler operations, better performance, reduced complexity
