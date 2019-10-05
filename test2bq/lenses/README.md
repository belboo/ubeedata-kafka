# Using Lenses instead of KSQL

Compose and also build the connect docker image with kcbq wihle we're at it:

```sql
INSERT INTO `test.topic.avro`

SELECT
    foo,
    bar,
    lat,
    lon,
    boo.id AS boo_id,
    datetime

FROM
    `test.topic`
```

```
name=test2bq
connector.class=com.wepay.kafka.connect.bigquery.BigQuerySinkConnector
tasks.max=1
key.converter=
value.converter=
header.converter=
transforms=
topics=["test.topic.avro"]
topics.regex=
enableBatchLoad=
batchLoadIntervalSec=120
gcsBucketName=
gcsFolderName=
topicsToTables=
project="phoenix-164312"
datasets=".*=testdataset"
schemaRetriever=
keyfile=
sanitizeTopics=true
includeKafkaData=false
avroDataCacheSize=100
allBQFieldsNullable=false
convertDoubleSpecialValues=false
autoCreateTables=true
```
