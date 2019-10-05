# Data & Kafka - A match made in heaven...

Kafka related code and snippets - tests and experiments...

For now we have:

- some tests on python API for protobuf (`protobuf` folder)
- a local test of KCBQ with full confluent container deployment [see [README](test2bq/README.md)]
- test of KQBC deployment on k8s [see [README](connect-k8s/README.md)]
- config files for the debezium plugin to tail MySQL binlog to Kafka
