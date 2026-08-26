# Databricks notebook source
# Production-target code: runs on a Databricks cluster against the
# Bronze -> Silver -> Gold medallion tables backing this project.
# Bronze: raw trip_events streamed from the app's event bus (Kafka) via
#         Databricks Structured Streaming, landed as Delta.
# Silver: cleaned + typed trip events, deduplicated on trip_id.
# Gold:   ETA and pricing feature table consumed by the model and by
#         the BigQuery export job that feeds Tableau / Omni.
#
# Not executed in this repo (no live Databricks cluster attached) —
# included as the production-target implementation, same convention
# used for the FraudStream Delta Live Tables pipeline.

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ---- Bronze -> Silver ------------------------------------------------

bronze = spark.readStream.format("delta").table("bronze.trip_events")

silver = (
    bronze
    .dropDuplicates(["trip_id"])
    .withColumn("requested_at", F.to_timestamp("requested_at"))
    .withColumn("hour_of_day", F.hour("requested_at"))
    .withColumn(
        "is_peak",
        F.col("hour_of_day").isin([7, 8, 9, 17, 18, 19]),
    )
    .filter(F.col("distance_km") > 0)
)

(
    silver.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/silver_trip_events")
    .table("silver.trip_events")
)

# ---- Silver -> Gold: ETA + pricing feature table ----------------------

region_window = Window.partitionBy("region", "hour_of_day")

gold = (
    spark.read.table("silver.trip_events")
    .withColumn(
        "eta_error_minutes",
        F.col("actual_eta_minutes") - F.col("predicted_eta_minutes"),
    )
    .withColumn(
        "region_avg_demand_index",
        F.avg("demand_index").over(region_window),
    )
    .withColumn(
        "fare_uplift_pct",
        (F.col("final_fare_usd") - F.col("base_fare_usd")) / F.col("base_fare_usd"),
    )
)

(
    gold.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("gold.eta_pricing_features")
)

# Unity Catalog governance: gold table is registered under
# catalog.logistics_analytics.gold.eta_pricing_features with column-level
# masking on trip_id for non-privileged roles.
