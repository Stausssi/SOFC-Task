# SOFC-Task
 Dev task for application at SOFC.

This application was developed and tested in **Python 3.10**!

## Usage
1. Install the given requirements in ```requirements.txt``` with `python -m pip install -r requirements.txt`
2. Run the program with `python main.py`. The possible parameters and their explanation can be seen by running `python main.py -h`.
3. The programm should perform a connectivity test by default

## Parameters
Please note that **all Parameters are optional!**

Running `python main.py -h` prompts you this message:
```commandline
usage: main.py [-h] [-host HOST] [-port PORT] [-user USER] [-password PASSWORD] [-mappings MAPPINGS]
               [-channel CHANNEL] [-interface INTERFACE] [-bustype BUSTYPE] [-bitrate BITRATE]

Connect MQTT and CAN-FD

options:
  -h, --help            show this help message and exit
  -host HOST            hostname of the MQTT broker. Defaults to 'localhost'
  -port PORT            port of the MQTT broker. Defaults to '1883'
  -user USER            username for the MQTT broker. Defaults to 'user'
  -password PASSWORD    password for the MQTT broker. Defaults to 'admin'
  -channel CHANNEL      channel of the CAN Bus. Defaults to 'Virtual CAN Bus'
  -interface INTERFACE  interface of the CAN Bus. Defaults to 'virtual'
  -bustype BUSTYPE      interface of the CAN Bus. Defaults to 'virtual'
  -bitrate BITRATE      bitrate of the CAN Bus. Defaults to '500000'
  -mappings MAPPINGS    Path to the JSON mapping file. Defaults to 'mapping.json'
```
The following data types are desired:

| Parameter   | Datatype  |
|-------------|-----------|
| `host`      | _String_  |
| `port`      | _Integer_ |
| `user`      | _String_  |
| `password`  | _String_  |
| `channel`   | _String_  |
| `interface` | _String_  |
| `bustype`   | _String_  |
| `bitrate`   | _Integer_ |
| `mappings`  | _String_  |

## Mappings
The mappings should follow the format given in `mappings.json`:
```json
{
  "mappings": [
    {
      "CAN-ID": 1,
      "MQTT-Topic": "CAN-1"
    },
    {
      "CAN-ID": "0xA",
      "MQTT-Topic": "CAN-10"
    }
  ]
}
```
Every item of the `mappings` list should contain a valid mapping with the fields `CAN-ID` and `MQTT-Topic`.
The field `CAN-ID` can be both an integer and a hex-string. The field `MQTT-Topic` should be a string.