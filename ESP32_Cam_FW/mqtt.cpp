#include <WiFi.h>
#include <PubSubClient.h>
#include "wifi_setting.h"
#include "command_receiver.h"
#include <string.h>
#include <stdlib.h>
#include "config.h"

// #define MQTT_MAX_PACKET_SIZE 8192

static void callback(char *topic, byte *payload, unsigned int length);

// MQTTブローカー
/* const char *mqtt_broker = "test.mosquitto.org"; */
const char *mqtt_broker = "192.168.0.8";
const char *pub_image_topic = "esp32-cam/img/raw";
const char *pub_setting_topic = "esp32-cam/controller/setting";
const char *sub_topic = "esp32-cam/board/#";
const char *control_topic = "esp32-cam/board/control";
const char *setting_topic = "esp32-cam/board/setting";
const char *image_topic = "esp32-cam/img/analyzed_scale";
const char *mqtt_username = "testuser";
const char *mqtt_password = "testpass";
const int mqtt_port = 1883;
const int payload_max_size = 10240;

CommandFIFO fifo(8);

#if (SHOW_RESULT == SHOW_IMG)
#define TIMESTAMP_LEN 14
uint8_t *img_data = NULL;
size_t  img_data_size;
#elif (SHOW_RESULT == SHOW_IMG_SCALE)
uint8_t *img_data = NULL;
size_t  img_data_size;
#endif


WiFiClient espClient;
PubSubClient client(espClient);

void mqtt_init()
{
    int count = 0;
    // WiFiネットワークへの接続
    WiFi.begin(ssid_Router, password_Router);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.println("Connecting to WiFi");
    }
    Serial.println("Success to connect WiFi");
    Serial.print("Local IP:");
    Serial.println(WiFi.localIP());
    // MQTTブローカーへの接続
    client.setServer(mqtt_broker, mqtt_port);
    client.setCallback(callback);
    client.setBufferSize(payload_max_size);
    while (!client.connected()) {
        String client_id = "esp32-client-";
        client_id += String(WiFi.macAddress());
        Serial.printf("Clienet %s is tring to connect MQTT Broker\n", client_id.c_str());
        //if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
        if (client.connect(client_id.c_str())) {
            Serial.println("Succes to connect MQTT Broker");
        } else {
            Serial.print("Fail to connect MQTT Broker:");
            Serial.println(client.state());
            //-4 : MQTT_CONNECTION_TIMEOUT - the server didn't respond within the keepalive time
            //-3 : MQTT_CONNECTION_LOST - the network connection was broken
            //-2 : MQTT_CONNECT_FAILED - the network connection failed
            //-1 : MQTT_DISCONNECTED - the client is disconnected cleanly
            //0 : MQTT_CONNECTED - the client is connected
            //1 : MQTT_CONNECT_BAD_PROTOCOL - the server doesn't support the requested version of MQTT
            //2 : MQTT_CONNECT_BAD_CLIENT_ID - the server rejected the client identifier
            //3 : MQTT_CONNECT_UNAVAILABLE - the server was unable to accept the connection
            //4 : MQTT_CONNECT_BAD_CREDENTIALS - the username/password were rejected
            //5 : MQTT_CONNECT_UNAUTHORIZED - the client was not authorized to connect
            delay(2000);
        }

        if(count++ >= 10) {
            break;
        }
    }

    // test
    // client.publish(topic, "Hello world from ESP32");
    client.subscribe(sub_topic);
    client.subscribe(image_topic);
}

static void callback(char *topic, byte *payload, unsigned int length)
{
    Serial.print("Message is received:");
    Serial.println(topic);

    if(!strcmp(image_topic, topic)) {
#if (SHOW_RESULT == SHOW_IMG)
        if (length > TIMESTAMP_LEN) {
            img_data_size = length - TIMESTAMP_LEN;
            if (img_data != NULL) {
                free(img_data);
            }
            img_data = (uint8_t *)malloc(img_data_size);
            if (img_data != NULL) {
                memcpy(img_data, payload + TIMESTAMP_LEN, img_data_size);
            } else {
                Serial.println("Memory allocation failed!");
            }
        } else {
            Serial.println("Payload length is too short.");
        }
#elif (SHOW_RESULT == SHOW_IMG_SCALE)
        img_data_size = length;
        if (img_data != NULL) {
            free(img_data);
        }
        img_data = (uint8_t *)malloc(img_data_size);
        if (img_data != NULL) {
            memcpy(img_data, payload, img_data_size);
        } else {
            Serial.println("Memory allocation failed!");
        }
#endif
    } else {
        Serial.print("Payload:");
        for (int i = 0; i < length; i++) {
            Serial.print((char)payload[i]);
        }
        std::string result((char *)payload, (int)length);
        // TODO topicによる切り分けとかどうしようか
        fifo.enqueue(result);
        Serial.println();
        Serial.println("-----------------------");
    }
}

std::string mqtt_get_command()
{
    return fifo.dequeue();
}

uint8_t *mqtt_get_img()
{
    return img_data;
}

size_t mqtt_get_img_size()
{
    return img_data_size;
}

void mqtt_del_img()
{
    free(img_data);
    img_data = NULL;
    img_data_size = 0;
}

void pub_image(const byte *image_data, unsigned int length)
{
    Serial.print("len:");
    Serial.println(length);
    boolean result = client.publish(pub_image_topic, image_data, length);
    if(result) {
        Serial.println("pub success");
    } else {
        Serial.println("pub fail");
    }
}

void pub_setting(bool interval_shot, int64_t interval, bool human_sensor)
{
    String payload = "{ \"interval_shot\": ";
    payload += interval_shot ? "true" : "false";
    payload += ", \"interval\": ";
    payload += String(interval);
    payload += ", \"human_sensor\": ";
    payload += human_sensor ? "true" : "false";
    payload += " }";

    Serial.println("payload: " + payload);
    boolean result = client.publish(pub_setting_topic, payload.c_str());
    if(result) {
        Serial.println("pub success");
    } else {
        Serial.println("pub fail");
    }
}

void mqtt_task(void)
{
    if (client.connected()) {
        client.loop();
    } else {
        String client_id = "esp32-client-";
        client_id += String(WiFi.macAddress());
        Serial.printf("Clienet %s is tring to connect MQTT Broker\n", client_id.c_str());
        //if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
        if (client.connect(client_id.c_str())) {
            Serial.println("Succes to connect MQTT Broker");
            client.subscribe(sub_topic);
            client.subscribe(image_topic);
            client.loop();
        } else {
            Serial.print("Fail to connect MQTT Broker:");
            Serial.println(client.state());
            //-4 : MQTT_CONNECTION_TIMEOUT - the server didn't respond within the keepalive time
            //-3 : MQTT_CONNECTION_LOST - the network connection was broken
            //-2 : MQTT_CONNECT_FAILED - the network connection failed
            //-1 : MQTT_DISCONNECTED - the client is disconnected cleanly
            //0 : MQTT_CONNECTED - the client is connected
            //1 : MQTT_CONNECT_BAD_PROTOCOL - the server doesn't support the requested version of MQTT
            //2 : MQTT_CONNECT_BAD_CLIENT_ID - the server rejected the client identifier
            //3 : MQTT_CONNECT_UNAVAILABLE - the server was unable to accept the connection
            //4 : MQTT_CONNECT_BAD_CREDENTIALS - the username/password were rejected
            //5 : MQTT_CONNECT_UNAUTHORIZED - the client was not authorized to connect
            delay(2000);
        }
    }
}
