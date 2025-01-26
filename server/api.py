from flask import Blueprint, jsonify, request
import pandas as pd
import os
from io import StringIO
import datetime
from library import read_config
import sys

config = read_config()

api_blueprint = Blueprint('api', __name__)

# Initialize dataset and save it to disk if it doesn't exist
if not os.path.exists(config['data']['detail']):
    initial_data = pd.DataFrame({
        "datestamp": pd.Series(dtype="datetime64[ns]"),
        "metric_id": pd.Series(dtype="str"),
        "resource": pd.Series(dtype="str"),
        "compliance": pd.Series(dtype="float64"),
        "slo": pd.Series(dtype="float64"),
        "slo_min": pd.Series(dtype="float64"),
        "weight": pd.Series(dtype="float64"),
        "title": pd.Series(dtype="str"),
        "category": pd.Series(dtype="str")
    })
    for d in config['dimensions']:
        initial_data[d] = pd.Series(dtype="str")

    initial_data.to_parquet(config['data']['detail'], index=False)

def retention_summary(df):
    print("starting retention")
    # Rule 1: Remove entries older than 13 months
    thirteen_months_ago = pd.Timestamp.now() - pd.DateOffset(months=13)
    df = df[df['datestamp'] >= thirteen_months_ago]

    # Rule 2: Retain only the last datestamp per month for entries older than 40 days
    forty_days_ago = pd.Timestamp.now() - pd.Timedelta(days=40)

    # Split the DataFrame into two parts
    recent_entries = df[df['datestamp'] >= forty_days_ago]
    older_entries = df[df['datestamp'] < forty_days_ago]

    # For older entries, retain only the last datestamp per month
    older_entries['year_month'] = older_entries['datestamp'].dt.to_period('M')  # Extract year-month
    older_entries = (
        older_entries.sort_values('datestamp')
        .groupby('year_month', group_keys=False)
        .tail(1)  # Keep the last entry per group
    )

    # Combine the DataFrames back
    df_retained = pd.concat([recent_entries, older_entries], ignore_index=True)

    # Optional: Drop the helper column 'year_month'
    df_retained.drop(columns=['year_month'], inplace=True, errors='ignore')

    print("retained")
    print(df_retained)
    return df_retained

def data_sanitise_detail(new_data):
    # Sanitize the data received.
    if 'datestamp' not in new_data.columns:
        new_data['datestamp'] = pd.Timestamp.now()
    new_data['datestamp'] = pd.to_datetime(new_data['datestamp']) #, errors='coerce') #.dt.strftime('%Y-%m-%d')
    
    if 'metric_id' not in new_data.columns:
        return jsonify({"success": False, "message": f"Missing mandatory column : metric_id"}), 400

    if 'resource' not in new_data.columns:
        return jsonify({"success": False, "message": f"Missing mandatory column : resource"}), 400
    
    if 'category' not in new_data.columns:
        new_data['category'] = 'undefined'

    if 'compliance' not in new_data.columns:
        new_data['compliance'] = 0

    if 'title' not in new_data.columns:
        new_data['title'] = new_data['metric_id']
    
    if 'slo' not in new_data.columns:
        new_data['slo'] = 0.95
    
    if 'slo_min' not in new_data.columns:
        new_data['slo_min'] = 0.90
    
    if 'weight' not in new_data.columns:
        new_data['weight'] = 0.5
    
    # Check if the float values are between 0 and 1
    for f in ['slo','slo_min','weight','compliance']:
        if not new_data[f].between(0, 1).all():
            return jsonify({"success": False, "message": f"Values in '{f}' column must be between 0 and 1"}), 400
    
    if (new_data['slo'] < new_data['slo_min']).all():
        return jsonify({"success": False, "message": f"slo must be greater than slo_min"}), 400
    
    # == check the dimensions
    for d in config['dimensions']:
        if d not in new_data.columns:
            new_data[d] = 'undefined'
    
    # == let's clean up any columns that should not be there
    for c in new_data.columns:
        if c not in config['dimensions'] and c not in ['metric_id','resource','compliance','slo','slo_min','weight','title','category','datestamp']:
            del new_data[c]

    return new_data

# Function to save the dataset
def save_data(df):
    if os.path.exists(config['data']['detail']):
        orig_df = pd.read_parquet(config['data']['detail'])
        # == delete the old metric - this dataframe should only contain the latest
        for metric_id in df['metric_id'].unique():
            try:
                orig_df = orig_df[orig_df['metric_id'] != metric_id]
            except:
                pass
        # == merge the new metric
        df = pd.concat([df,orig_df], ignore_index=True)

    # == apply the retention policy to detail data - keep only the last 2 days

    df = df[df['datestamp'] >= pd.to_datetime(pd.Timestamp.now() - pd.DateOffset(days=2))]

    df['datestamp'] = pd.to_datetime(df['datestamp'], errors='coerce').dt.strftime('%Y-%m-%d')

    df.to_parquet(config['data']['detail'], index=False)

    # == pivot the summary
    df_summary = df.groupby(['datestamp','metric_id','title','category','slo','slo_min','weight'] + list(config['dimensions'].keys())).agg({'compliance' : ['sum','count']}).reset_index()
    df_summary.columns = ['datestamp','metric_id','title','category','slo','slo_min','weight'] + list(config['dimensions'].keys()) + ['totalok', 'total']

    if os.path.exists(config['data']['summary']):
        orig_summary_df = pd.read_parquet(config['data']['summary'])

        # Ensure the columns exist in both DataFrames
        if 'metric_id' in orig_summary_df.columns and 'datestamp' in orig_summary_df.columns:
            # Get a set of metric_id and datestamp pairs to remove
            to_remove = set(zip(df_summary['metric_id'], df_summary['datestamp']))

            # Filter the original DataFrame to exclude rows matching any of the pairs
            orig_summary_df = orig_summary_df[
                ~orig_summary_df[['metric_id', 'datestamp']].apply(tuple, axis=1).isin(to_remove)
            ]

        # Concatenate the updated original DataFrame with the new summary
        df_summary = pd.concat([df_summary, orig_summary_df], ignore_index=True)

    #df = retention_summary(df_summary)  # apply data retention policy to keep the summary data small
    df_summary.to_parquet(config['data']['summary'], index=False)
    
# Function to check if the token is valid (in the list of valid tokens)
def check_token(token):
    return token in config['tokens']

@api_blueprint.route('/api', methods=['POST'])
def update_data():
    """API to update data using CSV content."""    
    # Get the Bearer token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "message": "Bearer token is missing or invalid"}), 401
    
    token = auth_header.split(" ")[1]  # Extract the token
    if not check_token(token):
        return jsonify({"success": False, "message": "Invalid token"}), 403

    # Read the CSV data from the request
    if request.data:
        try:
            # Read CSV data directly from request body
            csv_data = StringIO(request.data.decode('utf-8'))
            new_data = pd.read_csv(csv_data)
            
            new_data = data_sanitise_detail(new_data)
            # == check if new_data is a dataframe.  If it is, save it.  If not, return the error message
            if not isinstance(new_data, pd.DataFrame):
                return new_data
            
            save_data(new_data)
            
            # == Cosmetic - let's just show the number back to the API for added value
            score = new_data.groupby(['metric_id']).agg(totalok=('compliance', 'sum'), total=('compliance', 'count')).reset_index()
            score['score'] = score['totalok'] / score['total']
            
            return jsonify({"success": True, "message": f"Uploaded {len(new_data)} records", "result" : score.to_dict(orient='records')}), 200
        except Exception as e:
            return jsonify({"success": False, "message": f"Failed to process CSV data: {str(e)}"}), 400
    
    return jsonify({"success": False, "message": "No CSV data provided"}), 400

if __name__ == '__main__':
    # When running api as is, it takes the second command line option as a file name, and inserts that file to the dataframes
    if len(sys.argv) > 2:
        new_data = data_sanitise_detail(pd.read_csv(sys.argv[2]))
        save_data(new_data)
