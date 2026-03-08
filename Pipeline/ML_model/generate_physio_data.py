import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_authentic_physio_data(days=30, freq_min=10):
    """
    Generates synthetic but physiologically authentic data based on WESAD research.
    It simulates daily cycles (sleep, rest, exercise).
    """
    print(f"🧬 Generating authentic physiological data for {days} days...")
    
    start_date = datetime.now() - timedelta(days=days)
    timestamps = pd.date_range(start=start_date, periods=days*24*(60//freq_min), freq=f'{freq_min}T')
    
    data = []
    
    for ts in timestamps:
        hour = ts.hour
        
        # Determine state based on time of day
        if 0 <= hour < 6: # Sleep
            base_hr = 55
            base_br = 12
            base_spo2 = 98
            noise_hr, noise_br = 2, 1
        elif 7 <= hour < 9 or 17 <= hour < 19: # Potential Exercise/Commute
            base_hr = 100
            base_br = 25
            base_spo2 = 95
            noise_hr, noise_br = 15, 5
        else: # Normal activity
            base_hr = 75
            base_br = 16
            base_spo2 = 97
            noise_hr, noise_br = 5, 2
            
        # Add random noise for authenticity
        hr = base_hr + np.random.normal(0, noise_hr)
        br = base_br + np.random.normal(0, noise_br)
        spo2 = base_spo2 + np.random.normal(0, 0.5)
        
        # Constraints
        hr = max(40, min(180, hr))
        br = max(8, min(50, br))
        spo2 = max(85, min(100, spo2))
        
        data.append({
            'timestamp': ts,
            'heart_rate_bpm': round(hr, 1),
            'breathing_rate_lpm': round(br, 1),
            'spo2_percent': round(spo2, 1)
        })
        
    df = pd.DataFrame(data)
    
    output_path = os.path.join(os.path.dirname(__file__), "raw_physio_data.csv")
    df.to_csv(output_path, index=False)
    
    print(f"🎉 Success! Synthetic authentic data saved to: {output_path}")
    print(df.head())
    return df

if __name__ == "__main__":
    generate_authentic_physio_data()
