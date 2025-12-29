"""
Simple script to view SQLite database contents
"""
import sqlite3
import json
from tabulate import tabulate

DB_PATH = "data/validation.db"

def view_validation_results(limit=10):
    """View recent validation results"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("RECENT VALIDATION RESULTS")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            request_id,
            timestamp,
            input_types,
            overall_confidence,
            routing,
            action
        FROM validation_results
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    headers = ["Request ID", "Timestamp", "Input Types", "Confidence", "Routing", "Action"]
    
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal records: {len(rows)}")
    else:
        print("No validation results found.")
    
    conn.close()

def view_spatial_temporal_patterns():
    """View learned spatial-temporal patterns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("LEARNED SPATIAL-TEMPORAL PATTERNS")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            item_type,
            location,
            time_period,
            observation_count,
            updated_at
        FROM spatial_temporal_patterns
        ORDER BY observation_count DESC
    """)
    
    rows = cursor.fetchall()
    headers = ["Item Type", "Location", "Time Period", "Count", "Last Updated"]
    
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal patterns: {len(rows)}")
    else:
        print("No patterns learned yet.")
    
    conn.close()

def view_feedback_logs(limit=10):
    """View active learning feedback"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("ACTIVE LEARNING FEEDBACK")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            modality,
            predicted_label,
            user_correction,
            is_correct,
            timestamp
        FROM feedback_logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    headers = ["Modality", "Predicted", "Corrected To", "Was Correct?", "Timestamp"]
    
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal feedback entries: {len(rows)}")
    else:
        print("No feedback logged yet.")
    
    conn.close()

def get_statistics():
    """Show database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    
    # Total validations
    cursor.execute("SELECT COUNT(*) FROM validation_results")
    total_validations = cursor.fetchone()[0]
    
    # High confidence validations
    cursor.execute("SELECT COUNT(*) FROM validation_results WHERE routing = 'high_quality'")
    high_quality = cursor.fetchone()[0]
    
    # Average confidence
    cursor.execute("SELECT AVG(overall_confidence) FROM validation_results")
    avg_confidence = cursor.fetchone()[0] or 0
    
    print(f"Total Validations: {total_validations}")
    print(f"High Quality: {high_quality} ({high_quality/max(total_validations, 1)*100:.1f}%)")
    print(f"Average Confidence: {avg_confidence:.2%}")
    
    conn.close()

if __name__ == "__main__":
    try:
        get_statistics()
        view_validation_results(limit=5)
        view_spatial_temporal_patterns()
        view_feedback_logs(limit=5)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the database exists at: data/validation.db")
