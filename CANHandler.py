from can import Message, Listener, Notifier
from can.interface import Bus

from util import Mapping, MAX_EXTENDED_CAN_ID, MAX_CAN_ID, BYTE_ORDER


def logConsole(message: str):
    """
    Prints a message with a "[CAN]: " prefix

    :param message: The message to print
    :return: Nothing
    """

    print(f"[CAN]: {message}")


class CANHandler:
    """Handles the communication with a (virtual) CAN Bus"""

    def __init__(self, sendToMQTT, channel="", interface="", bustype="virtual",
                 bitrate=500000, receiveOwnMessages=True, mappings: list[Mapping] = None):
        """
        Creates a CANHandler instance.

        :param sendToMQTT: The function which will be called to send a message to MQTT
        :param channel: The channel of the CAN Bus. Not needed for a virtual CAN.
        :param interface: The interface of the CAN. Not needed for a virtual CAN.
        :param bustype: The bustype. 'virtual' for a virtual CAN Bus.
        :param bitrate: The bitrate of the CAN Bus. Not needed for a virtual CAN.
        :param receiveOwnMessages: Whether the Bus should receive messages sent by himself.
        :param mappings: A list of CAN-IDs to react to.
        """

        if channel is None:
            channel = ""

        if interface is None:
            interface = ""

        if bustype is None:
            bustype = "virtual"

        if bitrate is None:
            bitrate = 500000

        if receiveOwnMessages is None:
            receiveOwnMessages = True

        if mappings is None:
            mappings = []

        self.sendToMQTT = sendToMQTT
        self.mappings = mappings

        logConsole("Opening CAN Bus...")

        if bustype == "virtual":
            # noinspection PyTypeChecker
            self.canBus = Bus("Virtual CAN Bus", bustype="virtual", receive_own_messages=True)
        else:
            # noinspection PyTypeChecker
            self.canBus = Bus(interface=interface, bustype=bustype, channel=channel, bitrate=bitrate,
                              receive_own_messages=receiveOwnMessages)

        logConsole(f"CAN Bus created: '{self.canBus.channel_info}'")

        # Try to send and receive a message from the CAN
        logConsole("Trying whether message can be sent and received...")
        self.canBus.receive_own_messages = True

        testMessage = Message(arbitration_id=1, data=[0xff] * 8)
        self.sendMessage(testMessage.arbitration_id, testMessage.data)

        receivedMessage = self.canBus.recv(5)
        if receivedMessage.arbitration_id == testMessage.arbitration_id and receivedMessage.data == testMessage.data:
            logConsole("Check successful!")

            # Reset to original value
            self.canBus.receive_own_messages = receiveOwnMessages

            logConsole("Initializing Listener and Notifier!")

            # Create a listener for incoming messages
            listener = Listener()
            listener.on_message_received = self.messageReceived

            self.notifier = Notifier(self.canBus, [listener], 0)

            logConsole("CANHandler initialized!")
        else:
            logConsole("Check failed!")
            self.stop()
            exit(1)

    def stop(self):
        """
        Shuts the virtual CAN Bus down.

        :return: Nothing.
        """

        try:
            self.notifier.stop()
        except AttributeError:
            pass

        self.canBus.shutdown()

        logConsole("Stopped!")

    def messageReceived(self, canMessage: Message):
        """
        This method is called every time a message was sent to the CAN Bus.

        :param canMessage: The message
        :return: Nothing
        """

        canID = canMessage.arbitration_id

        # Convert to int
        payload = int.from_bytes(canMessage.data, byteorder=BYTE_ORDER)

        logConsole(f"Received CAN message with ID '{canID}' and data '{payload}' ({list(canMessage.data)})!")

        try:
            # Get corresponding MQTT topic
            topic = [mapping.mqttTopic for mapping in self.mappings if canID == mapping.canID][0]

            logConsole(f"This message will be forwarded to MQTT-Topic '{topic}' (payload: {payload})!")

            self.sendToMQTT(topic, payload)
        except IndexError:
            logConsole(f"No MQTT-Topic for CAN-ID '{canMessage.arbitration_id}' found!")

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
        """

        if isinstance(payload, list):
            if any([number > 0xff for number in payload]):
                raise ValueError(
                    "Invalid integer in payload! Please ensure that each data byte has to be in the range (0, 256)!"
                )

            payload = bytearray(payload)

        if not isinstance(canID, int) or canID > MAX_EXTENDED_CAN_ID:
            raise ValueError(f"Invalid CAN-ID! The maximum allowed ID is {MAX_EXTENDED_CAN_ID}")

        self.canBus.send(Message(arbitration_id=canID, data=payload, extended_id=canID > MAX_CAN_ID), timeout)
