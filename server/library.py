import yaml
import pandas as pd
import sys

def load_summary():
    config = read_config()
    return pd.read_parquet(config['data']['summary'])

def load_detail():
    config = read_config()
    return pd.read_parquet(config['data']['detail'])

def read_config():
    config_path = "config.yml"
    load_path = None

    # Only parse args if running as a script (not under Gunicorn)
    if hasattr(sys, "argv") and len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description='Cyber Dashboard - Flask')
        parser.add_argument('-config', help='Path to the config.yml file', default="config.yml")
        parser.add_argument('-load', help='Path to a CSV file to be loaded by the API call', default=None)
        args, _ = parser.parse_known_args()
        config_path = args.config
        load_path = args.load

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    config['cli'] = {'load': load_path}

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