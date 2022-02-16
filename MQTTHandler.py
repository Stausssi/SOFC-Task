from paho.mqtt.client import Client, MQTTMessage

from util import Mapping


def logConsole(message: str):
    """
    Prints a message with a "[MQTT]: " prefix

    :param message: The message to print
    :return: Nothing
    """

    print(f"[MQTT]: {message}")


class MQTTHandler:
    """Handles the communication with the MQTT broker"""

    def __init__(self, sendToCan, host: str = "localhost", port: int = 1883, username: str = "user",
                 password: str = "admin", mappings: list[Mapping] = None):
        """
        Creates an MQTT handler.

        :param sendToCan: The function which will be called to send a message to the can
        :param host: The hostname or IP-address of the MQTT Broker
        :param port: The port of the MQTT Broker
        :param username: The name of the user to login as
        :param password: The password of the given user
        :param mappings: A list of topics to subscribe to
        """

        if mappings is None:
            mappings = []

        if host is None:
            host = "localhost"

        if port is None:
            port = 1883

        if username is None:
            username = "user"

        if password is None:
            password = "admin"

        self.mappings = mappings
        self.sendToCan = sendToCan
        self.hostname = host
        self.port = port

        self.connected = False

        logConsole(f"Trying to connect to MQTT Broker at '{host}:{port}' as '{username}'...")

        self.client = Client("Python_MQTT_Client", clean_session=True)
        self.client.username_pw_set(username, password)

        self.client.on_connect_fail = self.__onConnectFail
        self.client.on_connect = self.__onConnect
        self.client.on_disconnect = lambda _, __, reason: logConsole(f"Disconnected with reason '{reason}'!")

    def connect(self):
        """
        Connect to the MQTT Broker.

        :return: True, if the broker can be reached.
        """

        try:
            self.client.connect(self.hostname, self.port)
            return True
        except ConnectionRefusedError:
            logConsole("Broker refused the connection. Check if it's running!")
            return False

    @staticmethod
    def __onConnectFail(_, __):
        """
        Callback for a connection failure. Exits with 1.

        :param _: The MQTT client. Ignored.
        :param __: The MQTT user data. Ignored.
        :return: Nothing
        """

        logConsole("Failed to connect to broker!")
        exit(1)

    def initHandler(self):
        """
        Initializes the handler by subscribing to the given topics.

        :return: Nothing
        """

        for mapping in self.mappings:
            self.client.subscribe(mapping.mqttTopic)
            logConsole(f"Subscribed to topic '{mapping.mqttTopic}'")

        self.client.on_message = self.messageReceived

    def __onConnect(self, _, __, ___, resultCode: int):
        """
        This method is called once the connection to the MQTT Broker is established.

        :param _: The MQTT client. Ignored.
        :param __: The MQTT user data. Ignored.
        :param ___: The flags. Ignored.
        :param resultCode: The result code of the connection. Determines whether the connection was successful.
        :return: Nothing
        """

        match resultCode:
            case 0:
                logConsole(f"Successfully connected!")
                self.connected = True
            case 5:
                logConsole("Invalid authentication!")
                exit(1)
            case _:
                logConsole(f"Connected with result code '{resultCode}'")

    def stop(self):
        """
        Disconnects from the Broker and stops the MQTT client loop.

        :return: Nothing.
        """

        self.client.disconnect()
        self.client.loop_stop()
        logConsole("Stopped!")

    def messageReceived(self, client: Client, userdata, message: MQTTMessage):
        """
        This method is called every time a message was sent to one of the topics this MQTT client is subscribed to.

        :param client: The MQTT client which sent the message
        :param userdata: ?
        :param message: The message
        :return: Nothing
        """

        # Only forward message if it was sent by a different client
        otherClientID = client.client_id.decode('utf-8')
        if otherClientID != self.client.client_id.decode('utf-8'):
            topic = message.topic
            payload = message.payload.decode("utf-8")

            logConsole(f"Client '{otherClientID}' (userdata: {userdata}) sent a message:")
            print(f"{' ' * 8}- Topic: {topic}")
            print(f"{' ' * 8}- Payload: {payload}")
            try:
                canID = [mapping.canID for mapping in self.mappings if mapping.mqttTopic == topic][0]
                logConsole(
                    f"This message will be forwarded to CAN-ID '{canID}'!"
                )

                self.sendToCan(canID, payload)
            except IndexError:
                logConsole(f"No CAN-ID for MQTT-Topic '{topic}' found!")

    def publishMessage(self, topic: str, payload):
        """
        This method publishes a given message to the MQTT broker.

        :param topic: The topic the message should be published to
        :param payload: The payload of the message
        :return: True, if the message was sent successfully
        """

        try:
            logConsole(
                f"Publishing message with payload '{payload}' from CAN-ID "
                f"'{[mapping.canID for mapping in self.mappings if mapping.mqttTopic == topic][0]}' "
                f"to MQTT-Topic '{topic}'"
            )

            result = self.client.publish(topic, payload)

            return result[0] == 0
        except IndexError:
            logConsole(f"No CAN-ID for MQTT-Topic '{topic}' found!")
