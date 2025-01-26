import yaml
import pandas as pd
import argparse

def load_summary():
    config = read_config()
    return pd.read_parquet(config['data']['summary'])

def load_detail():
    config = read_config()
    return pd.read_parquet(config['data']['detail'])

def read_config():
    parser = argparse.ArgumentParser(description='Cyber Dashboard - Flask')
    parser.add_argument('-config',help='Path to the config.yml file',default="config.yml")
    parser.add_argument('-load',help='Path to a csv file to be loaded by the api call',default=None)

    args = parser.parse_args()
 
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    config['cli'] = {
        'load' : args.load
    }

    return config

def data_last_12_items(df):
    # Filter the DataFrame for the last 12 months
    df['datestamp'] = pd.to_datetime(df['datestamp'])

    twelve_months_ago = pd.Timestamp.now() - pd.DateOffset(months=12)
    df_filtered = df[df['datestamp'] >= twelve_months_ago]
    
    # Sort the DataFrame by datestamp
    df_filtered = df_filtered.sort_values(by='datestamp')

    # Determine the number of rows and the interval for spacing
    num_records = len(df_filtered)
    if num_records < 12:
        # If there are fewer than 12 records, just use them all
        selected_datestamps = df_filtered
    else:
        # Always include the first and last items
        selected_datestamps = df_filtered.iloc[[0, -1]]

        # Calculate the interval for the remaining items
        interval = (num_records - 2) // 10  # 10 remaining items to select

        # Select the remaining evenly spaced datestamps
        if interval > 0:
            selected_datestamps = pd.concat([selected_datestamps, df_filtered.iloc[1:-1:interval][:10]])

    # Filter the DataFrame to only include the selected datestamps
    df_filtered = df_filtered[df_filtered['datestamp'].isin(selected_datestamps['datestamp'])]
    df_filtered['datestamp'] = pd.to_datetime(df_filtered['datestamp']).dt.strftime('%Y-%m-%d')
    return df_filtered