#!/bin/bash

# Install Kafka for Week 09 Production ML System
# This script installs Apache Kafka natively (without Docker)

set -e

echo "🚀 Installing Apache Kafka for ML Pipeline"
echo "==========================================="

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📍 Detected macOS - using Homebrew"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "☕ Installing Java 17 (required for Kafka)..."
    brew install openjdk@17 || echo "Java might already be installed"
    
    echo "📦 Installing Apache Kafka..."
    brew install kafka
    
    # Get the Kafka installation path
    KAFKA_PATH="$(brew --prefix kafka)/libexec"
    
    echo "✅ Kafka installed at: $KAFKA_PATH"
    echo ""
    echo "🔧 Setting up environment variables..."
    
    # Add to shell profile
    SHELL_PROFILE=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_PROFILE="$HOME/.bashrc"
    fi
    
    if [[ -n "$SHELL_PROFILE" ]]; then
        echo "# Apache Kafka for ML Pipeline" >> "$SHELL_PROFILE"
        echo "export KAFKA_HOME=\"$KAFKA_PATH\"" >> "$SHELL_PROFILE"
        echo "export PATH=\"\$KAFKA_HOME/bin:\$PATH\"" >> "$SHELL_PROFILE"
        echo ""
        echo "✅ Added environment variables to $SHELL_PROFILE"
        echo ""
        echo "🔄 To apply changes immediately, run:"
        echo "   export KAFKA_HOME=\"$KAFKA_PATH\""
        echo "   export PATH=\"\$KAFKA_HOME/bin:\$PATH\""
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📍 Detected Linux - manual installation"
    
    # Check if Java is installed
    if ! command -v java &> /dev/null; then
        echo "☕ Installing Java 17..."
        sudo apt update
        sudo apt install -y openjdk-17-jdk
    fi
    
    echo "📦 Downloading Apache Kafka..."
    KAFKA_VERSION="3.7.0"
    cd ~
    
    # Download if not already present
    if [[ ! -f "kafka_2.13-$KAFKA_VERSION.tgz" ]]; then
        curl -O "https://downloads.apache.org/kafka/$KAFKA_VERSION/kafka_2.13-$KAFKA_VERSION.tgz"
    fi
    
    echo "📁 Extracting Kafka..."
    tar -xzf "kafka_2.13-$KAFKA_VERSION.tgz"
    
    # Move to standard location
    if [[ -d "kafka" ]]; then
        rm -rf kafka_old
        mv kafka kafka_old
    fi
    mv "kafka_2.13-$KAFKA_VERSION" kafka
    
    KAFKA_PATH="$HOME/kafka"
    echo "✅ Kafka installed at: $KAFKA_PATH"
    
    # Add to shell profile
    SHELL_PROFILE="$HOME/.bashrc"
    echo "# Apache Kafka for ML Pipeline" >> "$SHELL_PROFILE"
    echo "export KAFKA_HOME=\"$KAFKA_PATH\"" >> "$SHELL_PROFILE"
    echo "export PATH=\"\$KAFKA_HOME/bin:\$PATH\"" >> "$SHELL_PROFILE"
    
    echo "✅ Added environment variables to $SHELL_PROFILE"
    echo ""
    echo "🔄 To apply changes immediately, run:"
    echo "   export KAFKA_HOME=\"$KAFKA_PATH\""
    echo "   export PATH=\"\$KAFKA_HOME/bin:\$PATH\""
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install Kafka manually from: https://kafka.apache.org/downloads"
    exit 1
fi

echo ""
echo "🎉 Kafka installation completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Restart your terminal or source your shell profile"
echo "   2. Run: make kafka-validate"
echo "   3. Run: make kafka-format"  
echo "   4. Run: make kafka-start"
echo ""
echo "📚 For more details, see: README_KAFKA.md"
