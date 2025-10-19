#!/bin/bash
# Kafka Environment Setup Script
# This script sets up Kafka environment variables for the current session

echo "🔧 Setting up Kafka environment variables..."

# Set KAFKA_HOME
export KAFKA_HOME=/opt/homebrew/opt/kafka/libexec
echo "✅ KAFKA_HOME set to: $KAFKA_HOME"

# Add Kafka bin to PATH
export PATH=$PATH:$KAFKA_HOME/bin
echo "✅ Added Kafka bin to PATH"

# Verify setup
if command -v kafka-topics.sh &> /dev/null; then
    echo "✅ Kafka commands are now available!"
    echo "📋 Available Kafka commands:"
    echo "   - kafka-topics.sh"
    echo "   - kafka-server-start.sh"
    echo "   - kafka-console-producer.sh"
    echo "   - kafka-console-consumer.sh"
else
    echo "❌ Kafka commands not found. Please check your Kafka installation."
    exit 1
fi

echo ""
echo "🎉 Kafka environment setup complete!"
echo "💡 To make this permanent, you need to add these lines to your ~/.zshrc:"
echo "   export KAFKA_HOME=/opt/homebrew/opt/kafka/libexec"
echo "   export PATH=\$PATH:\$KAFKA_HOME/bin"
echo ""
echo "🔧 To fix .zshrc ownership issue, run:"
echo "   sudo chown \$(whoami):staff ~/.zshrc"
echo ""
