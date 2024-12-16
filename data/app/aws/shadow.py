import asyncio
from awsiot import iotshadow, mqtt5
from utils.logging_setup import local_logger as logger
from utils.config import settings
from aws.client import _get_client_instance

class ShadowManager:
    def __init__(self, mqtt_client):
        if not isinstance(mqtt_client, mqtt5.Client):
            raise TypeError("ShadowManager requires an mqtt5.Client instance")
        self.mqtt_connection = mqtt_client
        self.shadow_client = iotshadow.IotShadowClient(self.mqtt_connection)
        self.thing_name = settings.AWS_CLIENT_ID

        # Initialize subscriptions
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Subscribe to necessary shadow topics."""
        try:
            # Subscribe to accepted/rejected topics for shadow operations
            self.shadow_client.subscribe_to_get_shadow_accepted(
                request=iotshadow.GetShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_get_shadow_accepted
            )
            self.shadow_client.subscribe_to_get_shadow_rejected(
                request=iotshadow.GetShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_get_shadow_rejected
            )
            self.shadow_client.subscribe_to_update_shadow_accepted(
                request=iotshadow.UpdateShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_update_shadow_accepted
            )
            self.shadow_client.subscribe_to_update_shadow_rejected(
                request=iotshadow.UpdateShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_update_shadow_rejected
            )
            self.shadow_client.subscribe_to_delete_shadow_accepted(
                request=iotshadow.DeleteShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_delete_shadow_accepted
            )
            self.shadow_client.subscribe_to_delete_shadow_rejected(
                request=iotshadow.DeleteShadowSubscriptionRequest(thing_name=self.thing_name),
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_delete_shadow_rejected
            )

            logger.info("Successfully subscribed to shadow topics.")
        except Exception as e:
            logger.error(f"Failed to subscribe to shadow topics: {e}")

    async def get_shadow(self):
        """Retrieve the shadow asynchronously."""
        request = iotshadow.GetShadowRequest(thing_name=self.thing_name)
        try:
            response = await self._publish_async(
                self.shadow_client.publish_get_shadow, request, qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            logger.info(f"Get shadow response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to get shadow: {e}")

    async def update_shadow(self, desired_state):
        """Update the shadow asynchronously."""
        state = iotshadow.ShadowState(desired=desired_state)
        request = iotshadow.UpdateShadowRequest(thing_name=self.thing_name, state=state)
        try:
            response = await self._publish_async(
                self.shadow_client.publish_update_shadow, request, qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            logger.info(f"Shadow updated successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to update shadow: {e}")

    async def delete_shadow(self):
        """Delete the shadow asynchronously."""
        request = iotshadow.DeleteShadowRequest(thing_name=self.thing_name)
        try:
            response = await self._publish_async(
                self.shadow_client.publish_delete_shadow, request, qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            logger.info(f"Shadow deleted successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to delete shadow: {e}")

    async def _publish_async(self, publish_method, request, qos):
        """Wrapper for publishing to shadow topics."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: publish_method(request, qos).result())

    # Callbacks for shadow responses
    def _on_get_shadow_accepted(self, response):
        logger.info(f"GetShadow accepted: {response}")

    def _on_get_shadow_rejected(self, error):
        logger.error(f"GetShadow rejected: {error}")

    def _on_update_shadow_accepted(self, response):
        logger.info(f"UpdateShadow accepted: {response}")

    def _on_update_shadow_rejected(self, error):
        logger.error(f"UpdateShadow rejected: {error}")

    def _on_delete_shadow_accepted(self, response):
        logger.info(f"DeleteShadow accepted: {response}")

    def _on_delete_shadow_rejected(self, error):
        logger.error(f"DeleteShadow rejected: {error}")
