from threading import Thread, Timer

from MQTTHandler import MQTTHandler
from util import MQTTParams, CANParams, Mapping


def logConsole(message: str):
    """
    Prints a message with a "[Bridge]: " prefix

    :param message: The message to print
    :return: Nothing
    """

    print(f"[Bridge]: {message}")


class Bridge:
    """The Bridge between CAN and MQTT"""

    def __init__(self, mqttParams: MQTTParams, canParams: CANParams, mappings: list[Mapping]):
        """
        Create a Bridge instance with the given params for both handlers and the mappings.

        :param mqttParams: The params needed for the MQTTHandler
        :param canParams: The params needed for the CANHandler
        :param mappings: A list of mappings between CAN-ID and MQTT-Topic
        """

        logConsole("Initializing Bridge...")

        # Create the MQTTHandler
        self.mqttHandler = MQTTHandler(
            self.sendMessageToCAN,
            mqttParams.hostname, mqttParams.port, mqttParams.username, mqttParams.password,
            mappings
        )

        # TODO: Create the CANHandler

        # TODO: Remove this. Just a debugging thing.
        Timer(5, lambda: self.stop()).start()

        if self.mqttHandler.connect():
            # TODO: connect the CANHandler

            self.mqttHandler.initHandler()

            # TODO: Init the CANHandler (if needed)

            logConsole("Bridge initialized")

            # Start a thread for the loop of the MQTTHandler
            self.mqttThread = Thread(target=self.mqttHandler.client.loop_forever)
            self.mqttThread.start()

            # TODO: Start a thread for the CANHandler

    def stop(self):
        """
        Stops the Bridge and both handlers.

        :return: Nothing
        """

        # Wait for the MQTTHandler
        self.mqttHandler.stop()
        self.mqttThread.join()

        # TODO: Wait for the CANHandler
        logConsole("Stopped!")

    def sendMessageToCAN(self, canID, payload):
        """
        Common ground to send a message from MQTT to CAN. NOT YET IMPLEMENTED1

        :param canID: The CAN-ID the message should be sent on
        :param payload: The payload of the message
        :return: Nothing
        """

        logConsole(f"Send to CAN '{canID}' with payload '{payload}'!")
        raise NotImplementedError("Not yet at least")

    def sendMessageToMQTT(self, topic: str, payload):
        """
        Common ground to send a message from the CAN to MQTT.

        :param topic: The MQTT Topic
        :param payload: The payload of the message
        :return: Nothing
        """

        self.mqttHandler.publishMessage(topic, payload)
