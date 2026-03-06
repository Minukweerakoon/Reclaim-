import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directory exists
output_dir = "paper/figures"
os.makedirs(output_dir, exist_ok=True)

# Set style
plt.style.use('ggplot')
colors = ['#ced4da', '#4dabf7', '#d63384']  # Grey, Blue, Pink (Ours)

# --- Chart 1: Accuracy Comparison (Bar Chart) ---
def plot_accuracy_gap():
    systems = ['YOLOv8', 'LostNet (SOTA)', 'Our System']
    accuracy = [75, 96.8, 100.0]
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(systems, accuracy, color=colors, width=0.6)
    
    # Add values on top
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}%',
                 ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.ylim(0, 110)
    plt.ylabel('Accuracy (%)')
    plt.title('Accuracy Gap Analysis: Moving Beyond State-of-the-Art')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save
    plt.savefig(os.path.join(output_dir, "gap_accuracy_comparison.png"), dpi=300, bbox_inches='tight')
    print("Generated gap_accuracy_comparison.png")

# --- Chart 2: Feature Radar Chart (Gap Filling) ---
def plot_radar_chart():
    # Metrics
    categories = ['Domain Accuracy', 'Voice Support', 'XAI Explainability', 'Cross-Modal Check', 'Real-time Viability']
    N = len(categories)
    
    # Data (Normalized 0-1 or 0-10 scale)
    # LostNet: High accuracy, but no voice, no XAI, no cross-modal
    yolo_stats = [7.5, 0, 0, 0, 10]
    lostnet_stats = [9.7, 0, 0, 0, 9] 
    ours_stats = [10.0, 10, 10, 10, 9] # Latency slightly higher than simple YOLO, but still real-time
    
    # Angles
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    yolo_stats += yolo_stats[:1]
    lostnet_stats += lostnet_stats[:1]
    ours_stats += ours_stats[:1]
    
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)
    
    # Draw one axe per variable + labels
    plt.xticks(angles[:-1], categories)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([2,4,6,8,10], ["2","4","6","8","10"], color="grey", size=7)
    plt.ylim(0, 10)
    
    # Plot YOLO
    ax.plot(angles, yolo_stats, linewidth=1, linestyle='solid', label='YOLOv8 (Baseline)', color='#ced4da')
    ax.fill(angles, yolo_stats, '#ced4da', alpha=0.1)
    
    # Plot LostNet
    ax.plot(angles, lostnet_stats, linewidth=2, linestyle='solid', label='LostNet (SOTA)', color='#4dabf7')
    ax.fill(angles, lostnet_stats, '#4dabf7', alpha=0.1)
    
    # Plot Ours
    ax.plot(angles, ours_stats, linewidth=2, linestyle='solid', label='Our System', color='#d63384')
    ax.fill(angles, ours_stats, '#d63384', alpha=0.25)
    
    plt.title('Capability Gap: Bridging Unaddressed Modalities', size=15, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # Save
    plt.savefig(os.path.join(output_dir, "gap_feature_radar.png"), dpi=300, bbox_inches='tight')
    print("Generated gap_feature_radar.png")

if __name__ == "__main__":
    plot_accuracy_gap()
    plot_radar_chart()
