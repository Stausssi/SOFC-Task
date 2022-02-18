import random
import time
from threading import Thread

from can import Message
from can.interface import Bus

from CANHandler import CANHandler
from MQTTHandler import MQTTHandler
from util import MQTTParams, CANParams, Mapping


def _logConsole(message: str):
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

        _logConsole("Initializing Bridge...")

        # Create the MQTTHandler
        self._mqttHandler = MQTTHandler(
            self._sendMessageToCAN,
            mqttParams.hostname, mqttParams.port, mqttParams.username, mqttParams.password,
            mappings
        )

        # Create the CANHandler
        self._canHandler = CANHandler(
            self._sendMessageToMQTT,
            canParams.channel, canParams.interface, canParams.bustype, canParams.bitrate,
            mappings
        )

        if self._mqttHandler.connect() and not self._canHandler.abort:
            # Start a thread for the loop of the MQTTHandler
            self.__mqttThread = Thread(target=self._mqttHandler.client.loop_forever)
            self.__mqttThread.start()

            # Wait for the MQTT Handler to connect
            while not self._mqttHandler.connected:
                time.sleep(0.1)

                if self._mqttHandler.abort:
                    self.stop()

            self._mqttHandler.initHandler()

            _logConsole("Bridge initialized!")

            # Test whether the connections are working
            self.testConnectivity()
        else:
            self.stop()

    def stop(self):
        """
        Stops the Bridge and both handlers.

        :return: Nothing
        """

        # Stop the MQTTHandler
        self._mqttHandler.stop()
        try:
            self.__mqttThread.join()
        except AttributeError:
            pass

        # Stop the CANHandler
        self._canHandler.stop()

        _logConsole("Stopped!")

        exit(0)

    def _sendMessageToCAN(self, canID: int, payload):
        """
        Common ground to send a message from MQTT to CAN.

        :param canID: The CAN-ID the message should be sent on
        :param payload: The payload of the message
        :type payload: bytearray[int] | list[int]
        :return: Nothing
        """

        _logConsole("Forwarding from MQTT to CAN.")

        self._canHandler.sendMessage(canID, payload)

    def _sendMessageToMQTT(self, topic: str, payload):
        """
        Common ground to send a message from the CAN to MQTT.

        :param topic: The MQTT Topic
        :param payload: The payload of the message
        :return: Nothing
        """

        _logConsole("Forwarding from CAN to MQTT.")

        self._mqttHandler.publishMessage(topic, payload)

    def testConnectivity(self):
        """
        Creates a new CANHandler to send demo messages to the other CAN. These message should then be forwarded to the
        MQTT Broker.
        Afterwards, the MQTTHandler send messages to itself, which should be forwarded to the CAN Bus.

        :return: Nothing
        """

        print()
        print("-"*25)
        _logConsole("Testing Connectivity...")
        print("-" * 10)
        _logConsole("Starting with messages on the virtual CAN...")

        # noinspection PyTypeChecker
        demoCAN = Bus("Virtual CAN Bus", bustype="virtual", interface="virtual")

        # Send random messages
        demoCAN.send(Message(
            arbitration_id=1,
            data=random.randbytes(random.randint(1, 8))
        ))
        demoCAN.send(Message(
            arbitration_id=10,
            data=random.randbytes(random.randint(1, 8))
        ))

        demoCAN.shutdown()

        time.sleep(1)

        _logConsole("CAN Test done!")
        print("-" * 10)
        _logConsole("Now MQTT...")

        # Enable the MQTTHandler to receive own messages
        self._mqttHandler.receiveOwnMessages = True

        self._mqttHandler.publishMessage("CAN-1", random.randrange(0, 2 ** 32))
        self._mqttHandler.publishMessage("CAN-10", random.randrange(0, 2 ** 32))

        time.sleep(1)

        self._mqttHandler.receiveOwnMessages = False

        print("-" * 10)
        _logConsole("Connectivity test done!")
        print("-" * 25)
        print()
