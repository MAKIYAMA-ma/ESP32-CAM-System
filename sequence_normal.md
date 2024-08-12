@startuml Take photo and analyze sequence
    participant ESP32_Cam_Controller as app
    participant ESP32_Cam_FW         as board
    participant MQTT_broker          as broker
    participant ESP32_Cam_AnalysisServer          as svr
    participant Mail_Server          as mailsvr

    activate broker
    activate app
    activate svr
    activate board
    activate mailsvr

    app -> broker : subscribe (esp32-cam/img/analyzed)
    board -> broker : subscribe (esp32-cam/board/#)
    svr -> broker : subscribe(esp32-cam/img/raw)
    svr -> broker : subscribe(esp32-cam/server/#)

    app -> broker : publish (esp32-cam/board/control, shot : true)
    broker -> board : publish (esp32-cam/board/control, shot : true)
    board -> board : capture image
    board -> broker : publish (esp32-cam/img/raw, captured image)
    broker -> svr : publish (esp32-cam/img/raw, captured image)
    svr -> svr : face analysis
    alt face is detected
        svr -> svr : create processed image data (add red circle on each face)
    end

    alt face is detected
        svr -> svr : analyzed image = processed image
    else
        svr -> svr : analyzed image = raw image
    end
    svr -> broker : publish (esp32-cam/img/analyzed, analyzed image)
    broker -> app : publish (esp32-cam/img/analyzed, analyzed image)
    app -> app : show subscribed image

    alt "warning mail" function is enabled
        svr -> mailsvr : send e-mail with processed image data
    end
@enduml
