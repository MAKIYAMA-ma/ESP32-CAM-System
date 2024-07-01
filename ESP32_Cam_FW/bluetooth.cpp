#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
String buffer;

void bt_init()
{
    SerialBT.begin("ESP32_Cam"); //Bluetooth device name
}

String bt_receive()
{
    if (SerialBT.available()) {
        return SerialBT.readStringUntil(':');
    } else {
        return "";
    }
}
