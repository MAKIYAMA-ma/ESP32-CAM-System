#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
String buffer;

void bt_init()
{
    SerialBT.begin("ESP32_Cam"); //Bluetooth device name
}

String bt_read_string()
{
    String result = "";
    int count = 0;

    while (SerialBT.available() > 0 && count < 16) {
        char c = (char)SerialBT.read();
        result += c;
        count++;
    }

    return result;
}
