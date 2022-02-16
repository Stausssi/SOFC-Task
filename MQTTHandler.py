from paho.mqtt.client import Client, MQTTMessage


def logConsole(message: str):
    print(f"[MQTT]: {message}")


class MQTTHandler:
    def __init__(self, host="localhost", port=1883, username="user", password="admin"):
        if host is None:
            host = "localhost"

        if port is None:
            port = 1883

        if username is None:
            username = "user"

        if password is None:
            password = "admin"

        logConsole(f"Trying to connect to MQTT Broker at '{host}:{port}' as '{username}'...")

        self.client = Client("Python_MQTT_Client")
        self.client.username_pw_set(username, password)

        self.client.on_connect_fail = lambda _, __: logConsole("Failed to connect to broker!")
        self.client.on_connect = lambda _, __, ___, ____: logConsole("Connected!")
        self.client.on_disconnect = lambda _, __, reason: logConsole(f"Disconnected with reason: {reason}")

        try:
            self.client.connect(host, port)
        except ConnectionRefusedError:
            logConsole("Broker refused the connection. Check if it's running!")

        self.client.subscribe("CAN-Translation")
        self.client.on_message = self.messageReceived

        self.publishMessage()

        self.client.loop_forever()

    def messageReceived(self, client: Client, userdata, message: MQTTMessage):
        logConsole(
            f"received message {message.payload} from client {client.client_id.decode('utf-8')} with userdata {userdata}")

    def publishMessage(self):
        result = self.client.publish("CAN-Translation", "Test message")
        if result[0] == 0:
            logConsole("message sent")
        else:
            logConsole("message not sent")
