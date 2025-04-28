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






kubectl delete -f finstream-zookeeper.yaml
kubectl apply -f finstream-zookeeper.yaml
kubectl apply -f finstream-cassandra.yaml
kubectl logs -n finstream cassandra-665b4cb8cf-n8z5v
kubectl get pods -n finstream
kubectl get deploy -n finstream
kubectl get services -n finstream



-Verify Cassandra Connectivity:
 kubectl exec -it cassandra-665b4cb8cf-n8z5v -n finstream -- nodetool status
 kubectl exec -it cassandra-665b4cb8cf-n8z5v -n finstream -- cqlsh 10.244.0.125 9042
 kubectl exec -it cassandra-665b4cb8cf-s7grs -n finstream -- cqlsh cassandra.finstream.svc.cluster.local 9042



streamlit:
  kubectl create configmap streamlit-app --from-file=app.py -n finstream
  kubectl cp app.py finstream/streamlit-59cb9d7897-jsr6b:/app/app.py
  kubectl port-forward svc/streamlit 8501:8501 -n finstream


🔹 `kubectl create configmap`: you're creating a **ConfigMap** (a way to store non-sensitive files/configs in Kubernetes)  
🔹 `project-files`: the **name** of the ConfigMap  
🔹 `--from-file=consumer.py`: you're including the file `consumer.py` into the ConfigMap  
🔹 `-n finstream`: you're putting the ConfigMap in the **namespace `finstream`**

👉 This lets you **mount `consumer.py` into a Pod** later without baking it into an image.



-Test Kafka:
  Create a test pod to interact with Kafka:  kubectl run kafka-client --restart=Never --image=bitnami/kafka:3.5.1 --namespace=finstream --command -- sleep infinity
  Access the pod: kubectl exec -it kafka-client -n finstream -- bash
  Create a topic:  /opt/bitnami/kafka/bin/kafka-topics.sh --create --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1 --topic test
  Produce a message:  /opt/bitnami/kafka/bin/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic test
  Consume the message:  /opt/bitnami/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic test --from-beginning
  Clean up:  kubectl delete pod kafka-client -n finstream



kubectl create configmap project-files \
  --from-file=producer.py \
  --from-file=consumer.py \
  --from-file=.env \
  --from-file=config/config.py \
  --from-file=config/config.yml \
  -n finstream --dry-run=client -o yaml | kubectl apply -f -



kubectl describe configmap project-files -n finstream


ConfigMapis read-only in Kubernetes



we just need to restart producer to connect to stable kafka 




kubectl exec -it <new-master-pod> -n finstream -- bash
/opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/tmp/ivy2 \
  --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 \
  /project/consumer.py



  /opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/tmp/ivy2 \
  --conf hadoop.security.authentication=simple \
  --conf spark.driver.memory=1g \
  --conf spark.executor.memory=1g \
  --conf spark.log.level=DEBUG \
  --packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0 \
  /project/consumer.py





  kubectl get configmap project-files -n finstream -o yaml > current-configmap.yaml


  kubectl create configmap project-files \
  --from-file=producer.py=/home/ali/Desktop/FinStream/producer.py \
  --from-file=consumer.py=/home/ali/Desktop/FinStream/consumer.py \
  --from-file=.env=/home/ali/Desktop/FinStream/.env \
  --from-file=__init__.py=/home/ali/Desktop/FinStream/config/__init__.py \
  --from-file=config.py=/home/ali/Desktop/FinStream/config/config.py \
  --from-file=config.yml=/home/ali/Desktop/FinStream/config/config.yml \
  -n finstream --dry-run=client -o yaml | kubectl apply -f -



kubectl exec -it spark-worker-85bcbf7fff-lkfjl  -n finstream -- /opt/bitnami/python/bin/pip3 install cassandra-driver




1- configmap (remember there s  two  )
2- remember pods have container and also you need to enter the container and run the script for consumer


kubectl exec -it -n finstream kafka-5cf94b6fc6-8dnf2 -- kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic finnhub_trades
kubectl exec -it -n finstream kafka-5cf94b6fc6-8dnf2 -- kafka-topics.sh --bootstrap-server kafka:9092 --create --topic finnhub_trades --partitions 1 --replication-factor 1
kubectl exec -it -n finstream spark-master-7f5784f74-htp48 -- rm -rf /tmp/checkpoint/agg
kubectl exec -it -n finstream spark-master-7f5784f74-htp48 -- rm -rf /tmp/checkpoint/raw





kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- /opt/bitnami/spark/bin/spark-submit     --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,com.github.jnr:jnr-posix:3.1.15     --executor-memory 2g     --executor-cores 4     /project/consumer.py


kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- pkill -f spark-submit
kubectl exec -it spark-master-7f5784f74-htp48 -n finstream -- rm -rf /tmp/checkpoint



- **Event Time**: The timestamp in the data when the event occurred (e.g., `trade.t`, like `2025-04-27 19:41:09`).
- **Ingestion Time**: The time Spark processes the data (e.g., `2025-04-27 23:34:54`).
- **Watermark Difference**: Watermark (e.g., 10 seconds) sets the max gap between event time and the latest event time processed. If event time is too old (e.g., >10 seconds behind), it’s ignored.
- **Key Issue**: Event time must be close to the latest event time, not ingestion time, to avoid being dropped by the watermark.





kubectl apply -f configmaps.yaml -n finstream