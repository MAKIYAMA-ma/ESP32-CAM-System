#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
String buffer;

const char CR = '\r';
const char LF = '\n';

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
        if(c == CR) {
            // ignore CR
            continue;
        } else if(c == LF) {
            // finish at LF
            break;
        } else {
            result += c;
            count++;
        }
    }

    return result;
}
