# Adding connect service to kafka in k8s - step by step...

## Configuration

- `kafka.yaml` - tune to set proper kafka deployment addresses and ports.
  In final deployment all variables shall be in Helm values
- `bq_auth.json` - unless you are somehow managing scopes in k8s,
  if you need the connector to be able to write to BigQuery/GCS,
  supply valid credentials file

## Build plugin image and push to gcr

The plugins are copied into the respective folder by the init containers.
Let's build a container which shall do that for the Kafka Connect BigQuery:

```bash
cd kcbq-plugin-docker
docker build -t cp-kafka-connect-kcbq:0.1 .
```

Tag:

```bash
docker tag cp-kafka-connect-kcbq:0.1 eu.gcr.io/REPOSITORY_NAME/cp-kafka-connect-kcbq:0.1
```

Push to the repo you can access from k8s:

```bash
docker push eu.gcr.io/REPOSITORY_NAME/cp-kafka-connect-kcbq
```

## Create secret with credentials for BQ/GCS

Create a secret from the gcloud auth file:

```bash
kubectl create secret generic -n production cp-kafka-connect-kcbq-credentials --from-file=./bq_auth.json
```

## Upgrade the release

Depending on your orchestration method, upgrade the deployment.
Here we rerun use Helm:

```bash
helm upgrade confluent .
```

See the status of the deployment:

```bash
helm status confluent .
```

See if the init containers have done their job:

```bash
kdpon system confluent-kafka-connect-
```

## Lenses Connect Config

You can also do the same via Kafka's REST, but since we have Lenses,
let's us use that one to set up stream redirection to BigQuery.

Respective config:

```json
lenses.connect.clusters=[{
    "name": "kafkaconnect",
    "statuses": "connect-status",
    "configs": "connect-configs",
    "offsets": "connect-offsets",
    "urls":[
      {"url":"http://KAFKA_CONNECT_ADDRESS:8083", "metrics": {
          "url":"KAFKA_CONNECT_ADDRESS:39999",
          "type": "JMX",
          "ssl": false,
        }}
    ]
  }
]
```

## KSQL

KCBQ requires an AVRO encoded topic to be able to manage BQ tables
and their schema evolution automatically. We had a protobuf serialised
into JSON, so we needed do some magic and cast the topic into AVRO.

Streams

```sql
CREATE STREAM cast_stream
(
    foo VARCHAR,
    bar VARCHAR,
    datetime VARCHAR
    boo STRUCT<
        id VARCHAR>
)
WITH
(
    KAFKA_TOPIC = 'input_topic',
    VALUE_FORMAT = 'JSON'
);

CREATE STREAM output_topic
WITH
(
    VALUE_FORMAT = 'AVRO'
)
AS SELECT
    foo AS `foo`,
    bar AS `bar`,
    datetime AS `datetime`,
    ROUND(STRINGTOTIMESTAMP(dateTime, 'yyyy-MM-dd''T''HH:mm:ss.nnnnnn') * 0.001) AS `datetime_utc`,
    boo->id AS `boo_id`
FROM
    `cast_stream`;

SET 'ksql.streams.retention.ms' = '3600000';
```

## Lenses SQL

Once lenses introduces encoding casting, it shall be possible to do that in LSQL.

```sql
INSERT INTO `data.sink.vt.fleet.geotab-gateway.logrecord.demux`

SELECT STREAM
	foo,
    bar,
    boo.id AS boo_id,
	datetime

FROM
	`input_topic`
```

Lenses SQL Processor Config:

```json
[
    {
        "name": "intermediate-stream",
        "sql": "INSERT INTO `intermediate.stream`\n\nSELECT STREAM\n\tfoo,\n\tbar,\n  \tboo.id AS boo_id,\n\tdatetime \t\nFROM \n\t`input_topic`",
        "runners": 1,
        "clusterName": "incluster"
    }
]
```

## Connector

```yaml
connector.class=com.wepay.kafka.connect.bigquery.BigQuerySinkConnector
sanitizeTopics=true
autoCreateTables=true
allBQFieldsNullable=true
errorsLogEnable=true
tasks.max=1
topics=output_topic
includeKafkaData=false
schemaRegistryLocation=http://SCHEMA_REGISTRY_ADDRESS:8081
topicsToTables=vt_(.*)_avro=$1
project=GCP_NAME
datasets=.*=DATESET_NAME
errorsLogIncludeMessages=true
keyfile=/var/lib/kafka-connect/credentials/bq_auth.json
name=streamtobq
schemaRetriever=com.wepay.kafka.connect.bigquery.schemaregistry.schemaretriever.SchemaRegistrySchemaRetriever
convertDoubleSpecialValues=false
key.converter=org.apache.kafka.connect.storage.StringConverter
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=http://confluent-schema-registry.system.svc.cluster.local:8081
```
