import json
from kafka import KafkaConsumer, KafkaProducer
import random
import string
import time
from datetime import datetime as dt
from datetime import timedelta as td

DEFAULT_KAFKA_TOPIC_BQ_SINK = 'vt.fleet.geotab-gateway.logrecord.demux'
DEFAULT_KAFKA_BROKER = 'localhost:9092'


def get_random_string(n: int, charset: str = 'ud') -> str:
    chars = ''
    if 'l' in charset:
        chars += string.ascii_lowercase
    if 'u' in charset:
        chars += string.ascii_uppercase
    if 'd' in charset:
        chars += string.digits

    return ''.join(random.choices(chars, k=n))


def gen_message():
    now = dt.utcnow()
    active_from = now - td(days=random.randint(1, 100), seconds=random.randint(1, 86400))

    return {
        'key': 'GEOTAB:telefonica_europcar_sp:b' + str(random.randint(1000, 1200)),
        'value': {
            'latitude': 39 + random.random(),
            'dateTime': now.isoformat(),
            'receivedOn': now.isoformat(),
            'longitude': 3 + random.random(),
            'id': 'b' + get_random_string(8, 'ud'),
            'device': {
                #'database': 'telefonica_europcar_sp',
                #'serialNumber': get_random_string(12, 'ud'),
                #'name': get_random_string(7, 'ud'),
                #'vehicleIdentificationNumber': get_random_string(17, 'ud'),
                #'deviceType': 'GO7',
                #'activeFrom': active_from.isoformat(),
                'id': 'b' + get_random_string(4, 'ud'),
                #'timeZoneId': 'America/New_York',
                #'owner': '',
                #'engineVehicleIdentificationNumber': 'TMBZZZ' + get_random_string(11, 'ud'),
            },
            'speed': random.random() * 60
        }
    }


def publish_message(producer, topic, key, value):
    try:
        producer.send(topic, key=key.encode('utf8'), value=value.encode('utf8'))
        producer.flush()
    #         print('Message published successfully.')
    except Exception as ex:
        print('Exception in publishing to topic {}'.format(topic))
        print(str(ex))


# ------------------------------------------------
# Main execution part

def parse_args():
    """ Parse command line arguments if run interactively.

    Returns
    -------
    arg_parse.Namespace
        Parsed arguments as returned by ArgumentParser.
    """

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-n',
                        type=int, default=-1, metavar='n',
                        help='messages to produce')

    parser.add_argument('-b', '--broker',
                        type=str, default=DEFAULT_KAFKA_BROKER, metavar='broker',
                        help='kafka broker address [default: {}]'.format(DEFAULT_KAFKA_BROKER))


    parser.add_argument('-t', '--topic',
                        type=str, default=DEFAULT_KAFKA_TOPIC_BQ_SINK, metavar='topic',
                        help='topic to write to [default: {}]'.format(DEFAULT_KAFKA_TOPIC_BQ_SINK))

    parser.add_argument('-p', '--pause',
                        type=int, default=0, metavar='pause',
                        help='ms to pause between messages')

    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False, dest='verbose',
                        help='Write the messages to STDOUT')

    return parser, parser.parse_args()


if __name__ == '__main__':
    parser, opts = parse_args()

    if opts.n < 0:
        parser.print_help()

    producer = KafkaProducer(bootstrap_servers=[opts.broker], api_version=(0, 10))

    for i in range(opts.n):
        msg = gen_message()
        if msg is not None:
            publish_message(
                producer=producer,
                topic=opts.topic,
                key=msg.get('key'),
                value=json.dumps(msg.get('value')))

        if opts.pause > 0:
            time.sleep(opts.pause)
