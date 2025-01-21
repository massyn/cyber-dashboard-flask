# Continuous Assurance - Dashboard

The Continuous Assurance Dashboard is a stand-alone, Python Flask-based application that is capable of running pre-defined security reporting.  What's missing though, is your data, and your metrics.

Once you have your data, a simple API call to the app will result in the data getting indexed, trended over time, and served straight away.

## Getting started

The app is built on Python 3.13.  Make sure you are running at least 3.x.  Some older versions may also work.

**Clone the repo**

* `git clone https://github.com/massyn/cyber-dashboard-flask`
* `cd cyber-dashboard-flask`

**Install Python requirements**

* `pip install -r requirements.txt`

**Run the app**

* `python app.py`

**Open the app**

* http://localhost:8080

Logon with the default credentials (`user` / `password123`)

At this point, the dashboard would appear, but it will be completely empty.  Let's add a metric to it.

**Add a metric to the dashboard**

We will add some data.  We use a simple vulnerability management metric that indicates if a server is compliant (1) or not (0) against some arbitrary criteria that was set.  A server also belongs to a particular business unit, so we prepare the following data.

| metric_id | resource | compliance | business_unit |
|-----------|----------|------------|---------------|
| vm-99     | ServerA  | 1          | Sales         |
| vm-99     | ServerB  | 0          | Sales         |
| vm-99     | ServerC  | 1          | Sales         |
| vm-99     | ServerD  | 1          | Sales         |
| vm-99     | ServerE  | 0          | Marketing     |
| vm-99     | ServerF  | 0          | Marketing     |
| vm-99     | ServerG  | 1          | Marketing     |
| vm-99     | ServerH  | 0          | Marketing     |
| vm-99     | ServerI  | 1          | Marketing     |
| vm-99     | ServerJ  | 1          | Marketing     |

Prepare a `csv` data blob of the data you'd like to ingest.  The following `curl` command can be used to simulate the loading of this data via API.

```bash
    curl -X POST http://localhost:8080/api \
    -H "Authorization: Bearer 6002920168C3253430A653E16AD36EE88F6E3C7D917A5F245F735D96ABDA67FE" \
    -H "Content-Type: text/csv" \
    --data-binary $'metric_id,resource,compliance,business_unit\nvm-99,ServerA,1,Sales\nvm-99,ServerB,0,Sales\nvm-99,ServerC,1,Sales\nvm-99,ServerD,1,Sales\nvm-99,ServerE,0,Marketing\nvm-99,ServerF,0,Marketing\nvm-99,ServerG,1,Marketing\nvm-99,ServerH,0,Marketing\nvm-99,ServerI,1,Marketing\nvm-99,ServerJ,1,Marketing\n'
```

On success, you should see a message like this:

```json
{"message":"Uploaded 10 records","result":[{"metric_id":"vm-99","score":0.6,"total":10,"totalok":6}],"success":true}
```

What we're seeing here, is that 10 records got uploaded, it was successful, and the system calculated the percentage compliance for us, and it came in at 60%.

Go back and open the [dashboard](http://localhost:8080) again.  What just happened?  The first data you just loaded got rendered on the dashboard.  The filters got added, you have the ability to switch from one business unit to another, and see their respective scores.

## Deeper dive - what happened in the background?

The `/api` call serves one purpose only - to load data into the dashboard.  It only accepts csv data.  The csv format has a number of fields.

### csv format

| Field        | Type   | Mandatory | Description                                                | Default     |
|--------------|--------|-----------|------------------------------------------------------------|-------------|
| `datestamp`  | string | No        | Date of the record using format `YYYY-MM-DD`               | Today       |
| `metric_id`  | string | Yes       | Unique identifier for the metric                           |             |
| `title`      | string | No        | Title of the metric                                        | metric_id   |
| `category`   | string | No        | Category (or security domain) of the metric                | `undefined` |
| `slo`        | float  | No        | Service level objective percentage between 0 and 1         | 0.95        |
| `slo_min`    | float  | No        | Minimum service level objective percentage between 0 and 1 | 0.90        |
| `weight`     | float  | No        | Weight of the metric                                       | 0.90        |
| `resource`   | string | Yes       | Unique identifier for the resource being                   |             |
| `compliance` | float  | No        | Compliance value between 0 and 1                           | 0           |
| `detail`     | string | No        | Additional information to help with remediation            | **blank**   |
| *            | string | No        | Additional dimensions to be used if required               | `undefined` |

### Sanisation

The sanisation function will read the provided csv data, fill in the gaps with default values, and fail the upload where mandatory data is either not provided, or not meeting the required formats.

### Store the detail

Data is stored in the parquet format.  When saving the detail, only the latest load per metric is retained.  The store function will delete the metric id being provided by the api call, and will replace it with the sanitised data.  That way the detail will always contain a copy of the latest detail.

### Summarise the data

Summarising the data is performed by counting the number of resources in the metric, as well as summing the values of compliance.  Like a pivot table, the dimensions are populated with these values.

In addition to summarising the values, the data is also stored as a time series.  The table will be used to calculate trends over time.

| Field        | Type   | Description                                                |
|--------------|--------|------------------------------------------------------------|
| `datestamp`  | string | Date of the record using format `YYYY-MM-DD`               |
| `metric_id`  | string | Unique identifier for the metric                           |
| `title`      | string | Title of the metric                                        |
| `category`   | string | Category (or security domain) of the metric                |
| `slo`        | float  | Service level objective percentage between 0 and 1         |
| `slo_min`    | float  | Minimum service level objective percentage between 0 and 1 |
| `weight`     | float  | Weight of the metric                                       |
| `totalok`    | float  | Sum of compliance                                          |
| `total`      | float  | Count of compliance                                        |
| *            | string | Additional dimensions to be used if required               |

## About the dashboard

### Aggregation

Aggregation is the process of merging metrics together, to allow for a consolidated view.  Think of it as a way to average the metrics together, as to see what the overall impact is.  Aggregation is useful for scenarios where the actual metric is not of importance, but rather the net result of some of the them grouped together.

The dashboard does two types of aggregation.  The first is on the first dimension (as specified in the `config.yml` file), showing a breakdown of the latest metric data load aggregated by that dimension.  The second is an aggregation by the `category` column (as specified during the data load process).

Aggregation is based off a weighted-average approach.  Rather than just simply doing an average of all metrics, you have the ability to adjust the weight of each metric during data load.  If one metric is more important than another, you have the ability to adjust the weight for that metric which will result in that metric's score having a bigger influence over the the resulting score.

### Attribution

Attribution is the process of assigning resources to a dimension, like a business unit, team or location.  It allows the dashboard to filter the metrics by that particular dimension to provide better insights in where a particular issue may exist.

Dimensions can be customised.  Update the `config.yml` file with any additional dimensions you'd like to introduce in the schema.  Be sure to update your API calls to the dashboard to include the dimensions in your data load.

### config.yml

TODO

## Write a metric

### What is important?

When defining a metric, we start by figuring out what we are trying to measure.  The dashboard metrics are always a percentage, with 100% being good, so when defining metrics, you need to write them in such a way to reflect this consistent view.  The reason we do it this way is to allow for data aggregation to occur.  

TODO

## Additional tops for success

* The `compliance` field is a float, a percentage of compliance if you will.  That means that when you decide compliance for a particular resource, you could infact define _partial_ compliance.
* To backup and restore, simply grab the `data` folder, and store that safely.  Upon recovery, install a fresh copy of the application, and restore the `data` folder.  Any customisation you may have made to the `config.yml` file also needs to be restored.
* You can start the dashboard with a custom `config.yml` file by starting the `app.py` with the path to the new config, for example:

```bash
python app.py my_other_config.yml
```

### AWS EC2 Instance

You can run the code on an AWS EC2 instance.  Deploy an `Amazon Linux 2023` instance.  Using the following UserData code will spawn a fresh server.

```bash
#!/bin/sh
sudo yum install -y git python3-pip
git clone https://github.com/massyn/cyber-dashboard-flask
cd cyber-dashboard-flask
pip install -r requirements.txt
cd server
gunicorn -w 4 -b 0.0.0.0:8080 app:server &
```

