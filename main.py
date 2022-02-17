import argparse

from Bridge import Bridge
from util import parseMappings, MQTTParams, CANParams


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Connect MQTT and CAN-FD")

    parser.add_argument("-host", type=str, help="hostname of the MQTT broker. Defaults to 'localhost'")
    parser.add_argument("-port", type=int, help="port of the MQTT broker. Defaults to '1883'")
    parser.add_argument("-user", type=str, help="username for the MQTT broker. Defaults to 'user'")
    parser.add_argument("-password", type=str, help="password for the MQTT broker. Defaults to 'admin'")
    parser.add_argument("-mappings", type=str, help="Path to the JSON mapping file. Defaults to 'mapping.json'")

    parser.add_argument("-channel", type=str, help="channel of the CAN Bus. Defaults to 'Virtual CAN Bus'")
    parser.add_argument("-interface", type=str, help="interface of the CAN Bus. Defaults to 'virtual'")
    parser.add_argument("-bustype", type=str, help="interface of the CAN Bus. Defaults to 'virtual'")
    parser.add_argument("-bitrate", type=int, help="bitrate of the CAN Bus. Defaults to '500000'")

    args = parser.parse_args()

    # Read the mappings from the file
    mappings = parseMappings(args.mappings)

    # Start the Bridge
    Bridge(
        MQTTParams(
            args.host,
            args.port,
            args.user,
            args.password
        ),
        CANParams(
            args.channel,
            args.interface,
            args.bustype,
            args.bitrate
        ),
        mappings
    )


if __name__ == '__main__':
    main()
