import pandas as pd
import os

def sync_and_clean_data():
    """
    Synchronizes the environmental and physiological datasets.
    Aligns them on the same timeline for ML training.
    """
    print("🧹 Starting Data Synchronization...")
    
    # Define paths
    env_path = os.path.join(os.path.dirname(__file__), "raw_env_data.csv")
    phys_path = os.path.join(os.path.dirname(__file__), "raw_physio_data.csv")
    
    if not os.path.exists(env_path) or not os.path.exists(phys_path):
        print("❌ Error: One or both raw data files are missing.")
        return
        
    # Load data
    df_env = pd.read_csv(env_path)
    df_phys = pd.read_csv(phys_path)
    
    # Convert timestamps
    df_env['timestamp'] = pd.to_datetime(df_env['timestamp'])
    df_phys['timestamp'] = pd.to_datetime(df_phys['timestamp'])
    
    # Get the minimum length to avoid index errors
    min_len = min(len(df_env), len(df_phys))
    print(f"📏 Using {min_len} samples for synchronization.")
    
    # Take the last N samples from both
    df_env_sync = df_env.tail(min_len).copy().reset_index(drop=True)
    df_phys_sync = df_phys.tail(min_len).copy().reset_index(drop=True)
    
    # Overwrite env timestamps with phys timestamps to force alignment
    df_env_sync['timestamp'] = df_phys_sync['timestamp']
    
    # Merge the datasets on timestamp
    print("🔗 Merging datasets...")
    final_df = pd.merge(df_phys_sync, df_env_sync, on='timestamp')
    
    # Handle missing values (Interpolate)
    final_df = final_df.interpolate(method='linear').ffill().bfill()
    
    # Save the cleaned dataset
    output_path = os.path.join(os.path.dirname(__file__), "cleaned_training_data.csv")
    final_df.to_csv(output_path, index=False)
    
    print(f"🎉 Success! Cleaned training data saved to: {output_path}")
    print(f"📊 Total integrated samples: {len(final_df)}")
    print(final_df.head())
    
    return final_df

if __name__ == "__main__":
    sync_and_clean_data()
