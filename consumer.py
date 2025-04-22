from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, avg, count, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType , ArrayType
import logging
from cassandra.cluster import Cluster, NoHostAvailable
import uuid
from config.config import config

logger = logging.getLogger(__name__)

def store_cassandra_raw(batch_df, batch_id):
    cluster = None
    try:
        logger.info(f'Storing raw batch {batch_id} in Cassandra')
        cluster = Cluster(['cassandra'], port=9042)
        session = cluster.connect()

        session.execute("CREATE KEYSPACE IF NOT EXISTS fintech WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
        session.set_keyspace("fintech")
        
        session.execute("""CREATE TABLE IF NOT EXISTS fintech.trades (
            id uuid PRIMARY KEY,
            symbol text,
            price double,
            volume double,
            trade_timestamp bigint,
            ingestion_time timestamp
        )""")

        df = batch_df.select(
            col("symbol").alias("symbol"),
            col("price").alias("price"),
            col("volume").alias("volume"),
            col("timestamp").alias("trade_timestamp"),
            current_timestamp().alias("ingestion_time")
        )

        logger.info(f'Starting to insert raw data for batch {batch_id}')
        rows = df.collect()
        for row in rows:
            session.execute(
                """INSERT INTO fintech.trades (id, symbol, price, volume, trade_timestamp, ingestion_time)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (uuid.uuid4(), row["symbol"], row["price"], row["volume"], row["trade_timestamp"], row["ingestion_time"])
            )
        logger.info(f'Inserted {len(rows)} raw rows into Cassandra for batch {batch_id}')

    except NoHostAvailable as e:
        logger.exception(f'Cassandra connection failed for raw batch {batch_id}: {e}')
    except Exception as e:
        logger.exception(f'Cassandra raw processing error for batch {batch_id}: {e}')
    finally:
        if cluster:
            cluster.shutdown()

def store_cassandra_aggregated(batch_df, batch_id):
    cluster = None
    try:
        logger.info(f'Storing aggregated batch {batch_id} in Cassandra, row count: {batch_df.count()}')
        if batch_df.count() == 0:
            logger.info(f'No data in aggregated batch {batch_id}')
            return

        cluster = Cluster(['cassandra'], port=9042)
        session = cluster.connect()
        session.set_keyspace("fintech")

        session.execute("""CREATE TABLE IF NOT EXISTS fintech.trade_aggregations (
            window_start timestamp,
            window_end timestamp,
            symbol text,
            avg_price double,
            trade_count bigint,
            PRIMARY KEY (window_start, symbol)
        )""")

        df = batch_df.select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("symbol").alias("symbol"),
            col("avg_price").alias("avg_price"),
            col("trade_count").alias("trade_count")
        )

        logger.info(f'Starting to insert aggregated data for batch {batch_id}')
        rows = df.collect()
        for row in rows:
            session.execute(
                """INSERT INTO fintech.trade_aggregations (window_start, window_end, symbol, avg_price, trade_count)
                VALUES (%s, %s, %s, %s, %s)""",
                (row["window_start"], row["window_end"], row["symbol"], row["avg_price"], row["trade_count"])
            )
        logger.info(f'Inserted {len(rows)} aggregated rows into Cassandra for batch {batch_id}')

    except NoHostAvailable as e:
        logger.exception(f'Cassandra connection failed for aggregated batch {batch_id}: {e}')
    except Exception as e:
        logger.exception(f'Cassandra aggregated processing error for batch {batch_id}: {e}')
    finally:
        if cluster:
            cluster.shutdown()

def consumer():
    spark = None
    try:
        logger.info('Starting the consumer')
        spark = SparkSession.builder \
            .appName("FinStreamProcessing") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
            .config("spark.hadoop.fs.defaultFS", "file:///") \
            .getOrCreate()
        logger.info('Spark session created successfully')

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
            .option("kafka.bootstrap.servers", config.server) \
            .option("subscribe", config.topic_name) \
            .option("startingOffsets", "earliest") \
            .option("group.id", "finstream-group") \
            .load()

        df = df.select(from_json(col("value").cast("string"), schema).alias("data")) \
               .selectExpr("explode(data.data) as trade") \
               .select(
                   col("trade.s").alias("symbol"),
                   col("trade.p").alias("price"),
                   col("trade.v").alias("volume"),
                   col("trade.t").alias("timestamp")
               )

        # First Query: Write raw data to Cassandra
        raw_query = df.writeStream \
            .foreachBatch(store_cassandra_raw) \
            .outputMode('append') \
            .start()
        logger.info('Raw data streaming query started')

        # Second Query: Aggregations every 5 seconds
        aggregated_df = df.groupBy(
            window((col("timestamp") / 1000).cast("timestamp"), "5 seconds"),
            col("symbol")
        ).agg(
            avg("price").alias("avg_price"),
            count("*").alias("trade_count")
        )

        agg_query = aggregated_df.writeStream \
            .foreachBatch(store_cassandra_aggregated) \
            .outputMode('update') \
            .start()
        logger.info('Aggregated data streaming query started')

        spark.streams.awaitAnyTermination()

    except Exception as e:
        logger.exception(f'Consumer error: {e}')
    finally:
        if spark:
            spark.stop()

if __name__ == "__main__":
    consumer()