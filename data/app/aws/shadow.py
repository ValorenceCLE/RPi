import asyncio
from awsiot import iotshadow, mqtt
from utils.logging_setup import local_logger as logger
from utils.config import settings
from aws.client import _get_client_instance

aws_client = _get_client_instance().client

class ShadowManager:
    def __init__(self):
        self.shadow_client = iotshadow.IotShadowClient(aws_client)
        self.thing_name = settings.AWS_CLIENT_ID

    async def get_shadow(self):
        """
        Retrieve the device shadow from AWS IoT.
        """
        request = iotshadow.GetShadowRequest(thing_name=self.thing_name)
        future = self.shadow_client.publish_get_shadow(request, qos=mqtt.QoS.AT_MOST_ONCE)
        response = await asyncio.wrap_future(future)  # Ensure it's awaitable
        logger.info(f"Get shadow response: {response}")
        return response

    async def update_shadow(self, desired_state):
        """
        Update the device shadow with the desired state.
        """
        state = iotshadow.ShadowState(desired=desired_state)
        request = iotshadow.UpdateShadowRequest(thing_name=self.thing_name, state=state)
        future = self.shadow_client.publish_update_shadow(request, qos=mqtt.QoS.AT_MOST_ONCE)
        response = await asyncio.wrap_future(future)  # Ensure it's awaitable
        logger.info(f"Update shadow response: {response}")
        return response

    async def delete_shadow(self):
        """
        Delete the device shadow from AWS IoT.
        """
        request = iotshadow.DeleteShadowRequest(thing_name=self.thing_name)
        future = self.shadow_client.publish_delete_shadow(request, qos=mqtt.QoS.AT_MOST_ONCE)
        response = await asyncio.wrap_future(future)  # Ensure it's awaitable
        logger.info(f"Delete shadow response: {response}")
        return response
