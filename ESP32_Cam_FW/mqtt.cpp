#include <WiFi.h>
#include <PubSubClient.h>
#include "wifi_setting.h"

// #define MQTT_MAX_PACKET_SIZE 8192

static void callback(char *topic, byte *payload, unsigned int length);

// MQTTブローカー
const char *mqtt_broker = "192.168.0.8";
const char *topic = "esp32-cam/img";
const char *mqtt_username = "testuser";
const char *mqtt_password = "testpass";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

void mqtt_init()
{
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
    client.setBufferSize(8192);
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
    }

    // test
    client.publish(topic, "Hello world from ESP32");
    client.subscribe(topic);
}

static void callback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Message is received:");
  Serial.println(topic);
  Serial.print("Payload:");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.println("-----------------------");
}

void pub_image(const byte *image_data, unsigned int length)
{
    Serial.print("len:");
    Serial.println(length);
    // TODO publishのデータ量を上げたい 画像のサイズだと送れない
    boolean result = client.publish(topic, image_data, length);
    //boolean result = client.publish(topic, image_data, 30);
    if(result) {
        Serial.println("pub success");
    } else {
        Serial.println("pub fail");
    }
}

void mqtt_task(void)
{
    client.loop();
}
