import requests
import pandas as pd
import os

def download_env_data_from_github():
    """
    Downloads historical air quality data from a reliable GitHub repository.
    Source: Indian Cities Daily Pollution (2015-2020)
    """
    url = "https://raw.githubusercontent.com/learning-monk/datasets/master/Indian_cities_daily_pollution_2015-2020.csv"
    
    print(f"🚀 Downloading real-world data from GitHub...")
    try:
        # Load directly into pandas
        df = pd.read_csv(url)
        
        # Filter for Delhi
        print("🔍 Filtering data for Delhi...")
        delhi_df = df[df['City'] == 'Delhi'].copy()
        
        if delhi_df.empty:
            print("⚠️ No data found for Delhi in this dataset.")
            return None
            
        # Select and rename relevant columns to match our engine's needs
        # Columns in dataset: City, Date, PM2.5, PM10, NO, NO2, NH3, CO, SO2, O3, Benzene, Toluene, Xylene, AQI, AQI_Bucket
        delhi_df = delhi_df[['Date', 'PM2.5', 'PM10', 'O3', 'NO2']]
        delhi_df = delhi_df.rename(columns={
            'Date': 'timestamp',
            'PM2.5': 'pm2.5_ug_m3',
            'PM10': 'pm10_ug_m3',
            'O3': 'ozone_ppb',
            'NO2': 'no2_ppb'
        })
        
        # Sort by date
        delhi_df['timestamp'] = pd.to_datetime(delhi_df['timestamp'])
        delhi_df = delhi_df.sort_values('timestamp')
        
        # Save to CSV
        output_path = os.path.join(os.path.dirname(__file__), "raw_env_data.csv")
        delhi_df.to_csv(output_path, index=False)
        
        print(f"🎉 Success! Real-world data saved to: {output_path}")
        print(f"📊 Total records found: {len(delhi_df)}")
        print(delhi_df.head())
        
        return delhi_df
        
    except Exception as e:
        print(f"❌ Error during download: {e}")
        return None

if __name__ == "__main__":
    download_env_data_from_github()
