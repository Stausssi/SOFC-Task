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

        if len(mappings) <= 0:
            _logConsole("Running this with no mapping is useless! Check the mapping file contents!")
            return

        _logConsole("Initializing Bridge...")

        self.mappings = mappings

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

            # Init the abort listener thread
            self.__listenForAbort = True
            self.__abortListenerThread = Thread(target=self.__abortListener)
            self.__abortListenerThread.start()

            _logConsole("Bridge initialized!")

            # Test whether the connections are working
            self.testConnectivity()
        else:
            self.stop()

    def __abortListener(self):
        """
        Checks if any of the handlers set the abort flag and stop the bridge. The loop can be interrupted by setting
        __listenForAbort to False.

        :return: Nothing
        """

        while self.__listenForAbort:
            if any([handler.abort for handler in [self._canHandler, self._mqttHandler]]):
                _logConsole(f"{'MQTT' if self._mqttHandler.abort else 'CAN'} requested abort!")
                self.stop()

    def stop(self):
        """
        Stops the Bridge and the handlers as well as the abort listener.

        :return: Nothing
        """

        # Stop the abort listener
        self.__listenForAbort = False
        try:
            self.__abortListenerThread.join()
        except (AttributeError, RuntimeError):
            pass

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

        # Send random messages to all canIDs
        for canID in [mapping.canID for mapping in self.mappings]:
            demoCAN.send(Message(
                arbitration_id=canID,
                data=random.randbytes(random.randint(1, 8))
            ))

        demoCAN.shutdown()

        time.sleep(1)

        _logConsole("CAN Test done!")
        print("-" * 10)
        _logConsole("Now MQTT...")

        # Enable the MQTTHandler to receive own messages
        self._mqttHandler.receiveOwnMessages = True

        # Send random messages to all topics
        for topic in [mapping.mqttTopic for mapping in self.mappings]:
            self._mqttHandler.publishMessage(topic, random.randrange(0, 2 ** 32))

        # Wait for the messages to be received
        time.sleep(1)

        self._mqttHandler.receiveOwnMessages = False

        print("-" * 10)
        _logConsole("Connectivity test done!")
        print("-" * 25)
        print()
