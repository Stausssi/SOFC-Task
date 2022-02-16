import argparse

from Bridge import Bridge
from util import parseMappings, MQTTParams, CANParams


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Connect MQTT and CAN-FD")
    parser.add_argument("-host", type=str, help="hostname of the MQTT broker. Defaults to 'localhost'")
    parser.add_argument("-port", type=int, help="port of the MQTT broker. Defaults to '1883'")
    parser.add_argument("-user", type=int, help="username for the MQTT broker. Defaults to 'user'")
    parser.add_argument("-password", type=int, help="password for the MQTT broker. Defaults to 'admin'")
    parser.add_argument("-mappings", type=str, help="Path to the JSON mapping file. Defaults to 'mapping.json'")

    args = parser.parse_args()

    mappings = parseMappings(args.mappings)

    # Start the Bridge
    Bridge(
        MQTTParams(
            args.host,
            args.port,
            args.user,
            args.password
        ),
        CANParams(),
        mappings
    )


if __name__ == '__main__':
    main()
