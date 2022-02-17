from threading import Thread, Timer

from CANHandler import CANHandler
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

        # Create the CANHandler
        self.canHandler = CANHandler(
            self.sendMessageToMQTT,
            canParams.channel, canParams.interface, canParams.bustype, canParams.bitrate, canParams.receiveOwnMessages,
            mappings
        )

        # TODO: Remove this. Just a debugging thing.
        Timer(5, lambda: self.stop()).start()

        if self.mqttHandler.connect():
            self.mqttHandler.initHandler()

            # Start a thread for the loop of the MQTTHandler
            self.mqttThread = Thread(target=self.mqttHandler.client.loop_forever)
            self.mqttThread.start()

            for i in range(10):
                Timer(1, lambda: self.canHandler.sendMessage(2**20, [255, 1, 2, 3])).start()

            logConsole("Bridge initialized")

    def stop(self):
        """
        Stops the Bridge and both handlers.

        :return: Nothing
        """

        # Stop the MQTTHandler
        self.mqttHandler.stop()
        self.mqttThread.join()

        # Stop the CANHandler
        self.canHandler.stop()

        logConsole("Stopped!")

    def sendMessageToCAN(self, canID: int, payload):
        """
        Common ground to send a message from MQTT to CAN.

        :param canID: The CAN-ID the message should be sent on
        :param payload: The payload of the message
        :type payload: bytearray[int] | list[int]
        :return: Nothing
        """

        logConsole("Forwarding from MQTT to CAN.")

        self.canHandler.sendMessage(canID, payload)

    def sendMessageToMQTT(self, topic: str, payload):
        """
        Common ground to send a message from the CAN to MQTT.

        :param topic: The MQTT Topic
        :param payload: The payload of the message
        :return: Nothing
        """

        logConsole("Forwarding from CAN to MQTT.")

        self.mqttHandler.publishMessage(topic, payload)
