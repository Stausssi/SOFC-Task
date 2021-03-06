import json

MAX_CAN_ID = 2 ** 11 - 1
MAX_EXTENDED_CAN_ID = 2 ** 29 - 1
BYTE_ORDER = "little"


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
                Mapping(
                    int(mapping["CAN-ID"], base=0) if isinstance(mapping["CAN-ID"], str) else mapping["CAN-ID"],
                    mapping["MQTT-Topic"]
                )
                for mapping in json.load(file)["mappings"]
            ]
    except FileNotFoundError as e:
        print(f"The given mapping file '{mappingFile}' doesn't exist! {e}")
    except Exception as e:
        print(f"An exception occurred while parsing the mapping file: {e}")

    exit(1)


class Mapping:
    """Represents a static data class containing information about a CAN to MQTT mapping"""

    def __init__(self, canID: int, mqttTopic: str):
        """
        Creates a static data class.

        :param canID: The ID of the message on the CAN-Bus
        :param mqttTopic: The name of the corresponding MQTT topic
        """

        if canID > MAX_EXTENDED_CAN_ID:
            raise ValueError(f"The given CAN-ID is greater than the maximum of '{MAX_EXTENDED_CAN_ID}'!")

        self.canID = canID
        self.mqttTopic = mqttTopic


class MQTTParams:
    """Param container for the MQTTHandler class"""

    def __init__(self, host: str = "localhost", port: int = 1883, username: str = "user", password: str = "admin"):
        """
        Creates a static data class.

        :param host: The __hostname or IP-address of the MQTT Broker
        :param port: The __port of the MQTT Broker
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

    def __init__(self, channel="Virtual CAN Bus", interface="virtual", bustype="virtual", bitrate=500000):
        """
        Creates a static data class.

        :param channel: The channel of the CAN Bus. 'Virtual CAN Bus' for a virtual CAN Bus.
        :param interface: The interface of the CAN. 'virtual' for a virtual CAN Bus.
        :param bustype: The bustype. 'virtual' for a virtual CAN Bus.
        :param bitrate: The bitrate of the CAN Bus. Not needed for a virtual CAN.
        """

        if channel is None:
            channel = ""

        if interface is None:
            interface = "virtual"

        if bustype is None:
            bustype = "virtual"

        if bitrate is None:
            bitrate = 500000

        self.channel = channel
        self.interface = interface
        self.bustype = bustype
        self.bitrate = bitrate
