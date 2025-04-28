from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, avg, count, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, ArrayType
import logging
from cassandra.cluster import Cluster, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy
import config

logger = logging.getLogger(__name__)

def create_cassandra_tables():
    """Create required Cassandra tables if they do not exist."""
    try:
        logger.info("Creating Cassandra tables if they do not exist")
        cluster = Cluster(
            ['cassandra.finstream.svc.cluster.local'],
            port=9042)
        session = cluster.connect()
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS fintech 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        session.set_keyspace("fintech")
        session.execute("""
            CREATE TABLE IF NOT EXISTS fintech.trades (
                id text PRIMARY KEY,
                symbol text,
                price double,
                volume double,
                trade_timestamp bigint,
                ingestion_time timestamp
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS fintech.trade_aggregations (
                window_start timestamp,
                window_end timestamp,
                symbol text,
                avg_price double,
                trade_count bigint,
                PRIMARY KEY (window_start, symbol)
            )
        """)
        logger.info("Cassandra tables created successfully")
    except Exception as e:
        logger.exception(f"Error creating Cassandra tables: {e}")
    finally:
        cluster.shutdown()

def consumer():
    spark = None
    try:
        logger.info('Starting the consumer')
        spark = SparkSession.builder \
            .appName("FinStreamProcessing") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,com.github.jnr:jnr-posix:3.1.15") \
            .config("spark.cassandra.connection.host", "cassandra.finstream.svc.cluster.local") \
            .config("spark.cassandra.connection.port", "9042") \
            .getOrCreate()
        logger.info('Spark session created successfully')

        create_cassandra_tables()

        schema = StructType([
            StructField("data", ArrayType(StructType([
                StructField("c", StringType(), True),
                StructField("p", DoubleType(), True),
                StructField("s", StringType(), True),
                StructField("t", LongType(), True),
                StructField("v", DoubleType(), True)
            ])), True),
            StructField("type", StringType(), True)
        ])

        df = spark.readStream \
            .format('kafka') \
            .option("kafka.bootstrap.servers", 'kafka:9092') \
            .option("subscribe", 'finnhub_trades') \
            .option("startingOffsets", "earliest") \
            .option("group.id", "finstream-group") \
            .load()

        df = df.select(from_json(col("value").cast("string"), schema).alias("data")) \
               .selectExpr("explode(data.data) as trade") \
               .select(
                   col("trade.s").alias("symbol"),
                   col("trade.p").alias("price"),
                   col("trade.v").alias("volume"),
                   (col("trade.t") / 1000).cast("timestamp").alias("timestamp")
               )

        raw_df = df.select(
            col("symbol").alias("symbol"),
            col("price").alias("price"),
            col("volume").alias("volume"),
            (col("timestamp").cast("long") * 1000).alias("trade_timestamp"),
            current_timestamp().alias("ingestion_time"),
            col("timestamp").cast("string").alias("id")
        )

        raw_query = raw_df.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", "fintech") \
            .option("table", "trades") \
            .option("checkpointLocation", "/tmp/checkpoint/raw") \
            .outputMode("append") \
            .start()
        logger.info('Raw data streaming query started')

        aggregated_df = df.withWatermark("timestamp", "10 seconds") \
            .groupBy(
                window(col("timestamp"), "5 seconds"),
                col("symbol")
            ).agg(
                avg("price").alias("avg_price"),
                count("*").alias("trade_count")
            ).select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol").alias("symbol"),
                col("avg_price").alias("avg_price"),
                col("trade_count").alias("trade_count")
            )

        agg_query = aggregated_df.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", "fintech") \
            .option("table", "trade_aggregations") \
            .option("checkpointLocation", "/tmp/checkpoint/agg") \
            .outputMode("append") \
            .start()
        logger.info('Aggregated data streaming query started')

        spark.streams.awaitAnyTermination()

    except Exception as e:
        logger.exception(f'Consumer error: {e}')
    finally:
        if spark:
            spark.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    consumer()