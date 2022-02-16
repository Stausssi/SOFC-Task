import json


def parseMappings(mappingFile: str = "mapping.json"):
    """
    Parses the mappings of a given JSON file.

    :param mappingFile: The path to the mapping file
    :return: A list of Mappings.
    """

    if mappingFile is None:
        mappingFile = "mapping.json"

    try:
        with open(mappingFile) as file:
            return [
                Mapping(mapping["CAN-ID"], mapping["MQTT-Topic"]) for mapping in json.load(file)["mappings"]
            ]
    except FileNotFoundError as e:
        print(f"The given mapping file '{mappingFile}' doesn't exist! {e}")


class Mapping:
    """Represents a static data class containing information about a CAN to MQTT mapping"""

    def __init__(self, canID: str, mqttTopic: str):
        """
        Creates a static data class.

        :param canID: The ID of the message on the CAN-Bus
        :param mqttTopic: The name of the corresponding MQTT topic
        """

        self.canID = canID
        self.mqttTopic = mqttTopic


class MQTTParams:
    """Param container for the MQTTHandler class"""

    def __init__(self, host: str = "localhost", port: int = 1883, username: str = "user", password: str = "admin"):
        """
        Creates a static data class.

        :param host: The hostname or IP-address of the MQTT Broker
        :param port: The port of the MQTT Broker
        :param username: The name of the user to login as
        :param password: The password of the user to login as
        """

        if host is None:
            host = "localhost"

        if port is None:
            port = 1883

        if username is None:
            username = "user"

        if password is None:
            password = "admin"

        self.hostname = host
        self.port = port
        self.username = username
        self.password = password


class CANParams:
    """Param container for the CANHandler class"""

    def __init__(self):
        pass
