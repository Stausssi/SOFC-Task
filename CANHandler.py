from can import Message, Listener, Notifier
from can.interface import Bus

from util import Mapping, MAX_EXTENDED_CAN_ID, MAX_CAN_ID, BYTE_ORDER


def beautifyBytearray(array: bytearray):
    """
    Converts a given bytearray into a more readable string representation

    :param array: The bytearray to convert to a string
    :return: [byte, byte, byte, ...] where byte is a hex
    number 0x00 - 0xff
    """

    return f"[{', '.join([str(hex(item)) for item in array])}]"


def _logConsole(message: str):
    """
    Prints a message with a "[CAN]: " prefix

    :param message: The message to print
    :return: Nothing
    """

    print(f"[CAN]: {message}")


class CANHandler:
    """Handles the communication with a (virtual) CAN Bus"""

    def __init__(self, sendToMQTT, channel="Virtual CAN Bus", interface="virtual", bustype="virtual",
                 bitrate=500000, mappings: list[Mapping] = None):
        """
        Creates a CANHandler instance.

        :param sendToMQTT: The function which will be called to send a message to MQTT.
        :param channel: The channel of the CAN Bus. 'Virtual CAN Bus' for a virtual CAN Bus.
        :param interface: The interface of the CAN. 'virtual' for a virtual CAN Bus.
        :param bustype: The bustype. 'virtual' for a virtual CAN Bus.
        :param bitrate: The bitrate of the CAN Bus. Not needed for a virtual CAN.
        :param mappings: A list of CAN-IDs to react to.
        """

        if channel is None:
            channel = "Virtual CAN Bus"

        if interface is None:
            interface = "virtual"

        if bustype is None:
            bustype = "virtual"

        if bitrate is None:
            bitrate = 500000

        if mappings is None:
            mappings = []

        self._sendToMQTT = sendToMQTT
        self.mappings = mappings

        self.abort = False

        _logConsole("Opening CAN Bus...")

        if bustype == "virtual" or interface == "virtual" or channel == "Virtual CAN Bus":
            # noinspection PyTypeChecker
            self._canBus = Bus("Virtual CAN Bus", bustype="virtual", interface="virtual")
        else:
            # noinspection PyTypeChecker
            self._canBus = Bus(interface=interface, bustype=bustype, channel=channel, bitrate=bitrate)

        _logConsole(f"CAN Bus created: '{self._canBus.channel_info}'")

        # Try to send and receive a message from the CAN
        _logConsole("Checking whether message can be sent and received...")
        self._canBus.receive_own_messages = True

        testMessage = Message(arbitration_id=MAX_EXTENDED_CAN_ID, data=[0xff] * 8)
        self._canBus.send(testMessage, 5)

        receivedMessage = self._canBus.recv(5)
        if receivedMessage.arbitration_id == testMessage.arbitration_id and receivedMessage.data == testMessage.data:
            _logConsole("Check successful!")

            # Reset
            self._canBus.receive_own_messages = False

            _logConsole("Initializing Listener and Notifier!")

            # Create a listener for incoming messages
            listener = Listener()
            listener.on_message_received = self.__messageReceived

            self.__notifier = Notifier(self._canBus, [listener], 0)

            _logConsole("CANHandler initialized!")
        else:
            _logConsole("Check failed!")
            self.abort = True

    def stop(self):
        """
        Shuts the virtual CAN Bus down.

        :return: Nothing.
        """

        try:
            self.__notifier.stop()
        except AttributeError:
            pass

        self._canBus.shutdown()

        _logConsole("Stopped!")

    def __messageReceived(self, canMessage: Message):
        """
        This method is called every time a message was sent to the CAN Bus.

        :param canMessage: The message
        :return: Nothing
        """

        canID = canMessage.arbitration_id

        # Extend data to 8 bytes
        canMessage.data.extend([0 for _ in range(0, 8 - canMessage.dlc)])

        # Convert to int
        payload = int.from_bytes(canMessage.data, byteorder=BYTE_ORDER)

        _logConsole(f"Received CAN message with ID '{hex(canID)}' and data '{beautifyBytearray(canMessage.data)}'!")

        try:
            # Get corresponding MQTT topic
            topic = [mapping.mqttTopic for mapping in self.mappings if canID == mapping.canID][0]

            _logConsole(f"This message will be forwarded to MQTT-Topic '{topic}' (payload: '{payload}')!")

            self._sendToMQTT(topic, payload)
        except IndexError:
            _logConsole(f"No MQTT-Topic for CAN-ID '{hex(canID)}' found!")

    def sendMessage(self, canID: int, payload, timeout: float = 1.0):
        """
        Send a message to the CAN Bus.

        :param canID: The CAN-ID of the message
        :param payload: The payload of the message. Can be both a bytearray or a list.
            Maximum of 8 items with 32 bit each allowed!
        :type payload: bytearray[int] | list[int]
        :param timeout: The duration (in s) which will be waited for in order for the message to be delivered.
        :return: Nothing
        :raises ValueError: if any of the given data bytes in the payload exceed the range (0, 256)
        :raises ValueError: if the CAN-ID is invalid. Maximum allowed ID is 2^29 - 1
        """

        if isinstance(payload, list):
            if any([number > 0xff for number in payload]):
                raise ValueError(
                    "Invalid integer in payload! Please ensure that each data byte is in the range (0, 256)!"
                )

            payload = bytearray(payload)

        if not isinstance(canID, int) or canID > MAX_EXTENDED_CAN_ID:
            raise ValueError(f"Invalid CAN-ID! The maximum allowed ID is {hex(MAX_EXTENDED_CAN_ID)}")

        _logConsole(f"Sending message with payload '{beautifyBytearray(payload)}' to CAN-ID '{hex(canID)}'.")

        self._canBus.send(Message(arbitration_id=canID, data=payload, extended_id=canID > MAX_CAN_ID), timeout)
