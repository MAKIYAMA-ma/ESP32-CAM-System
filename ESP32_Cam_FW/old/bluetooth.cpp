#include "BluetoothSerial.h"
#include "command_receiver.h"

BluetoothSerial SerialBT;

CommandFIFO fifo(8);

const char CR = '\r';
const char LF = '\n';

void bt_init()
{
    SerialBT.begin("ESP32_Cam"); //Bluetooth device name
}

char readbuf[16 + 1];
int idx = 0;
void bt_chk_command()
{
    int count = 0;

    while (SerialBT.available() > 0 && count < 16) {
        char c = (char)SerialBT.read();
        if(c == CR) {
            // ignore CR
            continue;
        } else if(c == LF) {
            // finish at LF
            std::string result(readbuf, idx);
            idx = 0;
            fifo.enqueue(result);
        } else {
            readbuf[idx++] = c;
            count++;
        }
    }
}

std::string bt_get_command()
{
    return fifo.dequeue();
}
