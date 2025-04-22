docker exec -it producer bash
docker exec -it producer pip install confluent_kafka websocket-client python-dotenv pyyaml


docker exec -it --user root spark-master bash
/opt/bitnami/python/bin/pip3 install python-dotenv PyYAML cassandra-driver

docker exec -it spark-master spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 /project/consumer.py



grafana : http://localhost:3000
spark : http://localhost:8081



DESCRIBE KEYSPACE fintech;
SELECT * FROM fintech.trades LIMIT 10;
SELECT * FROM fintech.trade_aggregations LIMIT 10;


Cassandra: """docker exec -it cassandra cqlsh
            CREATE KEYSPACE IF NOT EXISTS disaster WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
            USE disaster;
            CREATE TABLE test_table (id int PRIMARY KEY, name text);

            INSERT INTO test_table (id, name) VALUES (1, 'Test');
            SELECT * FROM test_table;"""

kafka :"""create topic:
        docker exec kafka kafka-topics --create --topic test-topic --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1
        producer:
        docker exec -it kafka kafka-console-producer --topic test-topic --bootstrap-server kafka:9092
        consumer:
        docker exec -it kafka kafka-console-consumer --topic test-topic --bootstrap-server kafka:9092 --from-beginning"""




------------------------------------------------------------------------------------
Runs /opt/bitnami/spark/sbin/start-master.sh & to start the master in the background(script starts the Spark master, binding it to port 7077)
------------------------------------------------------------------------------------
The global producer statement in producer() declares the producer variable as global, allowing it to be accessed and modified across functions. It’s used to share the Kafka Producer instance