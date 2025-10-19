#!/usr/bin/env python3
"""
Kafka Analytics Script
Analyzes churn prediction results with time-based statistics
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

def get_all_scored_messages() -> List[Dict[str, Any]]:
    """Get all messages from churn_predictions_scored topic"""
    try:
        cmd = [
            'kafka-console-consumer.sh',
            '--bootstrap-server', 'localhost:9092',
            '--topic', 'churn_predictions_scored',
            '--from-beginning',
            '--timeout-ms', '10000'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        messages = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip() and line.startswith('{'):
                    try:
                        data = json.loads(line)
                        messages.append(data)
                    except json.JSONDecodeError:
                        continue
        
        return messages
        
    except Exception as e:
        print(f"❌ Error fetching messages: {e}")
        return []

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp"""
    try:
        # Handle different timestamp formats
        if 'T' in timestamp_str:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now()

def analyze_predictions(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze prediction statistics by time periods"""
    
    if not messages:
        return {"error": "No messages found"}
    
    now = datetime.now()
    
    # Time periods
    periods = {
        '10_minutes': now - timedelta(minutes=10),
        '1_hour': now - timedelta(hours=1),
        '1_day': now - timedelta(days=1),
        'all_time': datetime.min
    }
    
    stats = {}
    
    for period_name, cutoff_time in periods.items():
        period_stats = {
            'total_predictions': 0,
            'churn_predictions': 0,
            'retain_predictions': 0,
            'churn_rate': 0.0,
            'avg_confidence': 0.0,
            'high_risk_customers': [],
            'geography_breakdown': defaultdict(int),
            'age_groups': defaultdict(int),
            'latest_predictions': []
        }
        
        period_messages = []
        confidences = []
        
        for msg in messages:
            # Parse timestamp
            processed_at = msg.get('processed_at', '')
            msg_time = parse_timestamp(processed_at)
            
            if msg_time >= cutoff_time:
                period_messages.append(msg)
                
                # Extract prediction info
                prediction = msg.get('prediction', {})
                status = prediction.get('Status', 'Unknown')
                confidence_str = prediction.get('Confidence', '0%')
                
                # Parse confidence percentage
                try:
                    confidence = float(confidence_str.replace('%', ''))
                    confidences.append(confidence)
                except:
                    confidence = 0.0
                
                # Count predictions
                period_stats['total_predictions'] += 1
                if 'Churn' in status:
                    period_stats['churn_predictions'] += 1
                    
                    # High risk customers (>70% confidence)
                    if confidence > 70:
                        customer_id = msg.get('customer_id', 'Unknown')
                        original_data = msg.get('original_data', {})
                        period_stats['high_risk_customers'].append({
                            'customer_id': customer_id,
                            'confidence': confidence,
                            'geography': original_data.get('Geography', 'Unknown'),
                            'age': original_data.get('Age', 'Unknown'),
                            'credit_score': original_data.get('CreditScore', 'Unknown')
                        })
                else:
                    period_stats['retain_predictions'] += 1
                
                # Geography breakdown
                original_data = msg.get('original_data', {})
                geography = original_data.get('Geography', 'Unknown')
                period_stats['geography_breakdown'][geography] += 1
                
                # Age groups
                age = original_data.get('Age', 0)
                if isinstance(age, (int, float)):
                    if age < 30:
                        age_group = 'Under 30'
                    elif age < 50:
                        age_group = '30-50'
                    else:
                        age_group = 'Over 50'
                    period_stats['age_groups'][age_group] += 1
        
        # Calculate rates and averages
        if period_stats['total_predictions'] > 0:
            period_stats['churn_rate'] = (period_stats['churn_predictions'] / 
                                        period_stats['total_predictions']) * 100
            
            if confidences:
                period_stats['avg_confidence'] = sum(confidences) / len(confidences)
        
        # Get latest predictions (last 5)
        period_messages.sort(key=lambda x: parse_timestamp(x.get('processed_at', '')), reverse=True)
        period_stats['latest_predictions'] = period_messages[:5]
        
        stats[period_name] = period_stats
    
    return stats

def print_analytics(stats: Dict[str, Any]):
    """Print formatted analytics"""
    
    if 'error' in stats:
        print(f"❌ {stats['error']}")
        return
    
    print("📊 KAFKA CHURN PREDICTION ANALYTICS")
    print("=" * 80)
    print(f"📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Summary table
    print("\n📈 PREDICTION SUMMARY BY TIME PERIOD")
    print("-" * 80)
    print(f"{'Period':<12} {'Total':<8} {'Churn':<8} {'Retain':<8} {'Churn %':<10} {'Avg Conf':<10}")
    print("-" * 80)
    
    for period_name, data in stats.items():
        if data['total_predictions'] > 0:
            period_display = period_name.replace('_', ' ').title()
            print(f"{period_display:<12} {data['total_predictions']:<8} "
                  f"{data['churn_predictions']:<8} {data['retain_predictions']:<8} "
                  f"{data['churn_rate']:<9.1f}% {data['avg_confidence']:<9.1f}%")
    
    # Detailed analysis for last hour
    hour_data = stats.get('1_hour', {})
    if hour_data.get('total_predictions', 0) > 0:
        print("\n🕐 LAST HOUR DETAILED ANALYSIS")
        print("-" * 80)
        
        # Geography breakdown
        print("📍 By Geography:")
        for geo, count in hour_data['geography_breakdown'].items():
            percentage = (count / hour_data['total_predictions']) * 100
            print(f"   {geo:<10}: {count:>3} predictions ({percentage:>5.1f}%)")
        
        # Age groups
        print("\n👥 By Age Group:")
        for age_group, count in hour_data['age_groups'].items():
            percentage = (count / hour_data['total_predictions']) * 100
            print(f"   {age_group:<10}: {count:>3} predictions ({percentage:>5.1f}%)")
        
        # High risk customers
        high_risk = hour_data['high_risk_customers']
        if high_risk:
            print(f"\n🚨 HIGH RISK CUSTOMERS (>70% churn probability):")
            print("   Customer   | Geography | Age | Credit | Confidence")
            print("   " + "-" * 50)
            for customer in high_risk[:10]:  # Show top 10
                print(f"   {str(customer['customer_id']):<10} | "
                      f"{str(customer['geography']):<9} | "
                      f"{str(customer['age']):<3} | "
                      f"{str(customer['credit_score']):<6} | "
                      f"{customer['confidence']:<6.1f}%")
        else:
            print("\n✅ No high-risk customers in the last hour")
    
    # Latest predictions
    latest = stats.get('10_minutes', {}).get('latest_predictions', [])
    if latest:
        print(f"\n🕘 LATEST PREDICTIONS (Last 10 minutes)")
        print("-" * 80)
        print("Time     | Customer   | Prediction | Confidence | Geography")
        print("-" * 80)
        
        for pred in latest[:10]:
            processed_at = pred.get('processed_at', '')
            time_str = processed_at.split('T')[1][:8] if 'T' in processed_at else 'Unknown'
            
            customer_id = str(pred.get('customer_id', 'N/A'))[:8]
            prediction_info = pred.get('prediction', {})
            status = prediction_info.get('Status', 'Unknown')[:6]
            confidence = prediction_info.get('Confidence', '0%')[:6]
            
            original_data = pred.get('original_data', {})
            geography = str(original_data.get('Geography', 'Unknown'))[:7]
            
            status_emoji = "🔴" if 'Churn' in status else "🟢"
            print(f"{time_str} | {customer_id:<10} | {status_emoji} {status:<6} | {confidence:<10} | {geography}")
    
    print("\n" + "=" * 80)
    print("💡 Use 'make kafka-sample-scored' for detailed message inspection")
    print("🔄 Run this again to see updated statistics")

def main():
    """Main analytics function"""
    try:
        print("📊 Fetching churn prediction data...")
        messages = get_all_scored_messages()
        
        if not messages:
            print("❌ No prediction data found")
            print("💡 Run 'make kafka-producer-batch && make kafka-consumer' first")
            return 1
        
        print(f"✅ Found {len(messages)} prediction records")
        
        # Analyze data
        stats = analyze_predictions(messages)
        
        # Print results
        print_analytics(stats)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Analytics interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Analytics error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
