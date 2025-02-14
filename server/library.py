import yaml
import pandas as pd
import sys
import boto3
from botocore.exceptions import ClientError
import os

def load_summary():
    config = read_config()

    # == get the files from the storage account, but don't overwrite it if they already exist
    if not cloud_storage_read(config['summary'],False):
        if not os.path.exists(config['summary']):
            initial_data = pd.DataFrame({
                "datestamp": pd.Series(dtype="datetime64[ns]"),
                "metric_id": pd.Series(dtype="str"),
                "total": pd.Series(dtype="float64"),
                "totalok": pd.Series(dtype="float64"),
                "slo": pd.Series(dtype="float64"),
                "slo_min": pd.Series(dtype="float64"),
                "weight": pd.Series(dtype="float64"),
                "title": pd.Series(dtype="str"),
                "category": pd.Series(dtype="str")
            })
            for d in config['dimensions']:
                initial_data[d] = pd.Series(dtype="str")

            initial_data.to_parquet(config['summary'], index=False)

    return pd.read_parquet(config['summary'])

def load_detail():
    config = read_config()

    # == read the cloud storage
    if not cloud_storage_read(config['detail'],False):
        # Initialize dataset and save it to disk if it doesn't exist
        if not os.path.exists(config['detail']):
            initial_data = pd.DataFrame({
                "datestamp" : pd.Series(dtype="datetime64[ns]"),
                "metric_id" : pd.Series(dtype="str"),
                "resource"  : pd.Series(dtype="str"),
                "compliance": pd.Series(dtype="float64"),
                "count"     : pd.Series(dtype="float64"),
                "detail"    : pd.Series(dtype="str"),
                "slo"       : pd.Series(dtype="float64"),
                "slo_min"   : pd.Series(dtype="float64"),
                "weight"    : pd.Series(dtype="float64"),
                "title"     : pd.Series(dtype="str"),
                "category"  : pd.Series(dtype="str")
            })
            new_columns = [key for key in config['dimensions'].keys() if key not in list(initial_data.columns)]
            for d in new_columns:
                initial_data[d] = pd.Series(dtype="str")
                print("adding {d}")

            initial_data.to_parquet(config['detail'], index=False)

    return pd.read_parquet(config['detail'])

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

    # Start experimenting with the idea of overwriting some config parameters from the environment variables
    for v in ['title','detail','summary','privacy']:
        ev = f"DASHBOARD_{v.upper()}"
        if ev in os.environ:
            config[v] = os.environ[ev]

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

def cloud_storage_write(local_file):
    if 'AWS_S3_BUCKET' in os.environ and os.environ['AWS_S3_BUCKET'].startswith('s3://'):
        target_key = f"{os.environ['AWS_S3_BUCKET']}/{os.path.basename(local_file)}"
        if not os.path.exists(local_file):
            print(f"WARNING - Not uploading to S3 because {local_file} does not exist")
            return False
        
        print(f"Uploading {local_file} to {target_key}...")

        bucket = target_key.split('/')[2]
        key = '/'.join(target_key.split('/')[3:])
        
        s3_client = boto3.client('s3')
        try:
            s3_client.upload_file(local_file, bucket, key, ExtraArgs={'ACL': 'bucket-owner-full-control'})
            print("AWS S3 Upload complete.")
        except ClientError as e:
            print(f"AWS S3 Upload ERROR : {e}")
            return False
        return True

def cloud_storage_read(local_file,overwrite=False):
    if 'AWS_S3_BUCKET' in os.environ and os.environ['AWS_S3_BUCKET'].startswith('s3://'):
        target_key = f"{os.environ['AWS_S3_BUCKET']}/{os.path.basename(local_file)}"
        if os.path.exists(local_file) and not overwrite:
            print(f"WARNING - Not downloading to S3 because {local_file} already exists")
            return False
        
        print(f"Downloading {target_key} to {local_file}...")

        bucket = target_key.split('/')[2]
        key = '/'.join(target_key.split('/')[3:])
        
        s3_client = boto3.client('s3')
        try:
            s3_client.download_file(bucket, key, local_file)
            print("AWS S3 Download complete.")
            return True
        except ClientError as e:
            print(f"AWS S3 Download ERROR : {e}")
            return False