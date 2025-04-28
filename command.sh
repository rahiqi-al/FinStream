docker exec -it producer bash
docker exec -it producer pip install confluent_kafka websocket-client python-dotenv pyyaml


docker exec -it --user root spark-master bash
/opt/bitnami/python/bin/pip3 install python-dotenv PyYAML cassandra-driver

docker exec -it spark-master spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 /project/consumer.py


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


-------------------------------------------------------------------------------------------------------------------------------------------
Cassandra:

 kubectl exec -it cassandra-665b4cb8cf-s7grs -n finstream -- cqlsh cassandra.finstream.svc.cluster.local 9042
  DESCRIBE KEYSPACE fintech;
  SELECT * FROM fintech.trades LIMIT 10;
  SELECT * FROM fintech.trade_aggregations LIMIT 10;


-------------------------------------------------------------------------------------------------------------------------------------------
streamlit:

  kubectl port-forward svc/streamlit 8501:8501 -n finstream

-------------------------------------------------------------------------------------------------------------------------------------------
Kafka:

  Create_a_test_pod_to_interact_with_Kafka:  kubectl run kafka-client --restart=Never --image=bitnami/kafka:3.5.1 --namespace=finstream --command -- sleep infinity
  Access_the_pod: kubectl exec -it kafka-client -n finstream -- bash
  Create_a_topic:  /opt/bitnami/kafka/bin/kafka-topics.sh --create --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1 --topic test
  Produce_a_message:  /opt/bitnami/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic test
  Consume_the_message:  /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic finnhub_trades --from-beginning
  Clean_up:  kubectl delete pod kafka-client -n finstream




  kubectl exec -it -n finstream kafka-5cf94b6fc6-8dnf2 -- kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic finnhub_trades
  kubectl exec -it -n finstream kafka-5cf94b6fc6-8dnf2 -- kafka-topics.sh --bootstrap-server kafka:9092 --create --topic finnhub_trades --partitions 1 --replication-factor 1


-------------------------------------------------------------------------------------------------------------------------------------------
spark:

kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- /opt/bitnami/spark/bin/spark-submit     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,com.github.jnr:jnr-posix:3.1.15     --executor-memory 2g     --executor-cores 4     /project/consumer.py

kubectl exec -it <new-master-pod> -n finstream -- bash
  /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/tmp/ivy2 \
  --conf hadoop.security.authentication=simple \
  --conf spark.driver.memory=1g \
  --conf spark.executor.memory=1g \
  --conf spark.log.level=DEBUG \
  --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0 \
  /project/consumer.py


  kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- pkill -f spark-submit
  kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- rm -rf /tmp/checkpoint

-------------------------------------------------------------------------------------------------------------------------------------------
configmap:

kubectl create configmap project-files \
  --from-file=producer.py=/home/ali/Desktop/FinStream/producer.py \
  --from-file=consumer.py=/home/ali/Desktop/FinStream/consumer.py \
  --from-file=.env=/home/ali/Desktop/FinStream/.env \
  --from-file=__init__.py=/home/ali/Desktop/FinStream/config/__init__.py \
  --from-file=config.py=/home/ali/Desktop/FinStream/config/config.py \
  --from-file=config.yml=/home/ali/Desktop/FinStream/config/config.yml \
  -n finstream --dry-run=client -o yaml > project-files-configmap.yaml

kubectl create configmap streamlit-app \
  --from-file=app.py=/home/ali/Desktop/FinStream/app.py \
  -n finstream --dry-run=client -o yaml > streamlit-app-configmap.yaml



kubectl describe configmap project-files -n finstream
