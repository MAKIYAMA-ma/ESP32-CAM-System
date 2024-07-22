# ESP32-CAM-System
toy with ESP32-WROVER Board

## Outline
### System connection diagram
<img src="./connection_image.png" width="80%">

### Requirements
#### ESP32_Cam_Controller
The app is intended for Android with API34 or later.

#### Server_Side
This script is developed using following libraries.
- Cython                        3.0.10
- numpy                         1.26.1
- onnx                          1.16.1
- onnxruntime                   1.18.0
- insightface                   0.7.3

#### ESP32_Cam_FW
You have to make "wifi_setting.h" in the same directory with mqtt.cpp.
The SSID and password of the WiFi router to be used must be defined in this file like following.
```
const char *ssid_Router = "hoge";
const char *password_Router = "fuga";
```

## Sequence Outline
### Take photo and analyze it
@startuml Take photo and analyze sequence
    participant ESP32_Cam_Controller as app
    participant ESP32_Cam_FW         as board
    participant MQTT_broker          as broker
    participant Server_Side          as svr

    activate broker
    activate app
    activate svr
    activate board

    app -> broker : subscribe (esp32-cam/img/#)
    board -> broker : subscribe (esp32-cam/board/#)
    svr -> broker : subscribe(esp32-cam/#)

    app -> broker : publish (esp32-cam/board/control, shot : true)
    broker -> board : publish (esp32-cam/board/control, shot : true)
    board -> board : capture image
    board -> broker : publish (esp32-cam/img/raw, captured image)
    broker -> app : publish (esp32-cam/img/raw, captured image)
    alt app is showing raw image mode
        app -> app : show subscribed image
    end
    broker -> svr : publish (esp32-cam/img/raw, captured image)
    svr -> svr : face analysis
    svr -> svr : create processed image data

    alt send with e-mail
        svr -> svr : send e-mail with processed image data
    else send with mqtt
        svr -> broker : (esp32-cam/img/raw, captured image)
        broker -> app : (esp32-cam/img/raw, captured image)
        alt app is showing processed image mode
            app -> app : show subscribed image
        end
    end
@enduml

### Setting
TODO Sequence Diaglam


## MQTT
### MQTT Setting
TODO setting about MQTT

### MQTT Messages
| topic                    | payload                    | from   | to          | note                        |
|--------------------------|----------------------------|--------|-------------|-----------------------------|
| esp32-cam/img/raw        | captured image data        | Board  | Server, App |                             |
| esp32-cam/img/processed  | analyzed image data        | Server | App         | used if set to send         |
| esp32-cam/board/setting  | change setting of board    | App    | Board       |                             |
| esp32-cam/board/control  | control message for board  | App    | Board       |                             |
| esp32-cam/server/setting | change setting of server   | App    | Server      |                             |
| esp32-cam/server/control | control message for server | App    | Server      | it is not used but reserved |

#### esp32-cam/board/setting

| key           | value       | note                                             |
|---------------|-------------|--------------------------------------------------|
| interval_shot | true/false  | enable/disable interval shot                     |
| interval      | number (>0) | interval time [msec] for executing interval shot |

#### esp32-cam/board/control

| key  | value | note                 |
|------|-------|----------------------|
| shot | true  | take onetime capture |

#### esp32-cam/server/setting

| key        | value          | note                                           |
|------------|----------------|------------------------------------------------|
| send_image | mail/mqtt/none | send image with e-mail/MQTT, or not to send    |
| image_type | raw/processed  | send raw-data/processed-data of detected image |
