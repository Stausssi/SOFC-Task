import argparse

from MQTTHandler import MQTTHandler


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Connect MQTT and CAN-FD")
    parser.add_argument("-host", type=str, help="hostname of the MQTT broker")
    parser.add_argument("-port", type=int, help="port of the MQTT broker")
    parser.add_argument("-user", type=int, help="username for the MQTT broker")
    parser.add_argument("-password", type=int, help="password for the MQTT broker")

    args = parser.parse_args()

    # Start the MQTT Handler
    mqtt = MQTTHandler(args.host, args.port, args.user, args.password)


if __name__ == '__main__':
    main()
