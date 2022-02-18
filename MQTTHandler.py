from paho.mqtt.client import Client, MQTTMessage, error_string

from util import Mapping, BYTE_ORDER


def _logConsole(message: str):
    """
    Prints a message with a "[MQTT]: " prefix

    :param message: The message to print
    :return: Nothing
    """

    print(f"[MQTT]: {message}")


class MQTTHandler:
    """Handles the communication with the MQTT broker"""

    def __init__(self, sendToCAN, host: str = "localhost", port: int = 1883, username: str = "user",
                 password: str = "admin", mappings: list[Mapping] = None):
        """
        Creates an MQTT handler.

        :param sendToCAN: The function which will be called to send a message to the can
        :param host: The hostname or IP-address of the MQTT Broker
        :param port: The port of the MQTT Broker
        :param username: The name of the user to login as
        :param password: The password of the given user
        :param mappings: A list of topics to subscribe to
        """

        if host is None:
            host = "localhost"

        if port is None:
            port = 1883

        if username is None:
            username = "user"

        if password is None:
            password = "admin"

        if mappings is None:
            mappings = []

        self._sendToCan = sendToCAN
        self.mappings = mappings

        self.__hostname = host
        self.__port = port

        self.connected = False
        self.abort = False
        self.receiveOwnMessages = False

        _logConsole(f"Trying to connect to MQTT Broker at '{host}:{port}' as '{username}'...")

        # Create the client
        self.client = Client("Python_MQTT_Client", clean_session=True)
        self.client.username_pw_set(username, password)

        # Add callbacks
        self.client.on_connect_fail = self.__onConnectFail
        self.client.on_connect = self.__onConnect
        self.client.on_disconnect = lambda _, __, reason: _logConsole(
            f"Disconnected with reason '{reason}': {error_string(reason)}"
        )

    def connect(self):
        """
        Connect to the MQTT Broker.

        :return: True, if the broker can be reached.
        """

        try:
            self.client.connect(self.__hostname, self.__port)
            return True
        except (ConnectionRefusedError, TimeoutError):
            _logConsole("Broker refused the connection. Check if it's running!")
            return False

    @staticmethod
    def __onConnectFail(_, __):
        """
        Callback for a connection failure. Exits with 1.

        :param _: The MQTT client. Ignored.
        :param __: The MQTT user data. Ignored.
        :return: Nothing
        """

        _logConsole("Failed to connect to broker!")
        exit(1)

    def initHandler(self):
        """
        Initializes the handler by subscribing to the given topics.

        :return: Nothing
        """

        # Subscribe to every topic
        for mapping in self.mappings:
            self.client.subscribe(mapping.mqttTopic)
            _logConsole(f"Subscribed to topic '{mapping.mqttTopic}'")

        self.client.on_message = self.__messageReceived

    def __onConnect(self, _, __, ___, resultCode: int):
        """
        This method is called once the connection to the MQTT Broker is established.

        :param _: The MQTT client. Ignored.
        :param __: The MQTT user data. Ignored.
        :param ___: The flags. Ignored.
        :param resultCode: The result code of the connection. Determines whether the connection was successful.
        :return: Nothing
        """

        # Act according to the result code
        match resultCode:
            case 0:
                _logConsole(f"Successfully connected!")
                self.connected = True
            case 5 | 7:
                _logConsole(f"Connection failed: {error_string(resultCode)}")
                self.abort = True
            case _:
                _logConsole(f"Connected with result code '{resultCode}'")

    def stop(self):
        """
        Disconnects from the Broker and stops the MQTT client loop.

        :return: Nothing.
        """

        # Stop the loop and disconnect
        self.client.loop_stop()
        self.client.disconnect()

        _logConsole("Stopped!")

    def __messageReceived(self, client: Client, _, message: MQTTMessage):
        """
        This method is called every time a message was sent to one of the topics this MQTT client is subscribed to.

        :param client: The MQTT client which sent the message
        :param _: The userdata. Ignored for now.
        :param message: The message
        :return: Nothing
        """

        # Only forward message if it was sent by a different client
        try:
            otherClientID = client.client_id.decode('utf-8')
            if otherClientID != self.client.client_id.decode('utf-8') or self.receiveOwnMessages:
                topic = message.topic
                payload = message.payload.decode("utf-8")

                _logConsole(f"Client '{otherClientID}' sent a message:")
                print(f"{' ' * 8}- Topic: {topic}")
                print(f"{' ' * 8}- Payload: {payload}")

                try:
                    # Get the corresponding canID
                    canID = [mapping.canID for mapping in self.mappings if mapping.mqttTopic == topic][0]

                    try:
                        # Convert the payload
                        payload = int(payload).to_bytes(8, byteorder=BYTE_ORDER)

                        _logConsole(f"This message will be forwarded to CAN-ID '{canID}'!")
                        self._sendToCan(canID, payload)
                    except (OverflowError, ValueError) as e:
                        _logConsole(f"Something went wrong while converting the payload into a byte-array: {e}")
                except IndexError:
                    _logConsole(f"No CAN-ID for MQTT-Topic '{topic}' found!")
        except UnicodeDecodeError as e:
            _logConsole(f"Encountered an error while trying to convert the message data: {e}")

    def publishMessage(self, topic: str, payload: int):
        """
        This method publishes a given message to the MQTT broker.

        :param topic: The topic the message should be published to
        :param payload: The payload of the message
        :return: True, if the message was sent successfully
        """

        try:
            _logConsole(f"Publishing message with payload '{payload}' to MQTT-Topic '{topic}'.")

            result = self.client.publish(topic, payload)

            return result[0] == 0
        except IndexError:
            _logConsole(f"No CAN-ID for MQTT-Topic '{topic}' found!")
