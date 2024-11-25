from awsiot import mqtt5_client_builder
from awscrt import mqtt5
from utils.logging_setup import local_logger as logger
from utils.config import settings
from concurrent.futures import Future

TIMEOUT=100
future_stopped = Future()
future_connection_success = Future()

def on_publish_received(publish_packet_data):
    publish_packet = publish_packet_data.publish_packet
    assert isinstance(publish_packet, mqtt5.PublishPacket)
    logger.info("Received message from topic'{}':{}".format(publish_packet.topic, publish_packet.payload))


def on_lifecycle_stopped(lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
    logger.info("MQTT connection stopped")
    global future_stopped
    future_stopped.set_result(lifecycle_stopped_data)

def on_lifecycle_connection_success(lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
    logger.info("Lifecycle Connection Success")
    global future_connection_success
    future_connection_success.set_result(lifecycle_connect_success_data)

def on_lifecycle_connection_failure(lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
    logger.info("Lifecycle Connection Failure")
    logger.info("Connection failed with exception:{}".format(lifecycle_connection_failure.exception))

client=mqtt5_client_builder.mtls_from_path(
    endpoint=settings.AWS_ENDPOINT,
    port=8883,
    cert_filepath=settings.DEVICE_COMBINED_CRT,
    pri_key_filepath=settings.DEVICE_KEY,
    ca_filepath=settings.AWS_ROOT_CA,
    http_proxy_options=None,
    on_publish_received=on_publish_received,
    on_lifecycle_stopped=on_lifecycle_stopped,
    on_lifecycle_connection_success=on_lifecycle_connection_success,
    on_lifecycle_connection_failure=on_lifecycle_connection_failure,
    client_id=settings.AWS_CLIENT_ID
)
client.start()
lifecycle_connection_success_data = future_connection_success.result(TIMEOUT)
connack_packet = lifecycle_connection_success_data.connack_packet
negotiated_settings = lifecycle_connection_success_data.negotiated_settings

def publish(topic, payload):
    publish_future = client.publish(mqtt5.PublishPacket(topic=f"{settings.AWS_CLIENT_ID}/{topic}", payload=payload, qos=mqtt5.QoS.AT_LEAST_ONCE))
    publish_completion_data = publish_future.result(TIMEOUT)
    logger.debug("PubAck received with {}".format(repr(publish_completion_data.puback.reason_code)))

def subscribe(topic):
    subscribe_future = client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[mqtt5.Subscription(
            topic_filter=f"{settings.AWS_CLIENT_ID}/{topic}",
            qos=mqtt5.QoS.AT_LEAST_ONCE
        )]
    ))
    suback = subscribe_future.result(TIMEOUT)
    logger.debug("SubAck received with {}".format(repr(suback.suback_packet.reason_string)))