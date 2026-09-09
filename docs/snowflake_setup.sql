-- One-time Snowflake setup. Run in a Snowsight worksheet before the first
-- ingestion. Select all statements and run them together, not one at a time.

-- XSMALL is the cheapest compute size and is plenty for this data volume.
-- AUTO_SUSPEND = 60 matters most on a credit-metered trial: the warehouse
-- shuts off after a minute idle instead of billing while nothing is running.
CREATE WAREHOUSE IF NOT EXISTS nfl_wh
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

CREATE DATABASE IF NOT EXISTS nfl_analytics;

-- raw     = source data exactly as published, never transformed
-- staging = typed and cleaned dbt views
-- marts   = the aggregated tables the dashboard reads
CREATE SCHEMA IF NOT EXISTS nfl_analytics.raw;
CREATE SCHEMA IF NOT EXISTS nfl_analytics.staging;
CREATE SCHEMA IF NOT EXISTS nfl_analytics.marts;

USE WAREHOUSE nfl_wh;
USE DATABASE nfl_analytics;
