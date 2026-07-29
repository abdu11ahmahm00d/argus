#include <Servo.h>
#include <SoftwareSerial.h>
#include <ArduinoJson.h>
#include "protocol.h"

SoftwareSerial btSerial(PIN_HC05_TX, PIN_HC05_RX);
Servo servo1;
Servo servo2;

unsigned long startTime = 0;
bool buzzerActive = false;
unsigned long buzzerEndTime = 0;

void setup() {
  pinMode(PIN_LASER, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_SWITCH, INPUT_PULLUP);

  servo1.attach(PIN_SERVO1);
  servo2.attach(PIN_SERVO2);

  servo1.write(SERVO1_REST);
  servo2.write(SERVO2_REST);
  digitalWrite(PIN_LASER, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_LED_GREEN, LOW);

  btSerial.begin(9600);
  Serial.begin(9600);

  startTime = millis();
  sendAck("SETUP", "OK", "system_ready");
}

void loop() {
  if (buzzerActive && millis() >= buzzerEndTime) {
    digitalWrite(PIN_BUZZER, LOW);
    buzzerActive = false;
  }

  int switchState = digitalRead(PIN_SWITCH);
  if (switchState == LOW) {
    digitalWrite(PIN_LASER, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    delay(100);
    return;
  }

  if (btSerial.available()) {
    String raw = btSerial.readStringUntil('\n');
    raw.trim();
    if (raw.length() == 0) return;

    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, raw);
    if (err) {
      sendAck("PARSE_ERR", "ERR", err.c_str());
      return;
    }

    const char* cmd = doc["cmd"];
    if (!cmd) {
      sendAck("NO_CMD", "ERR", "missing_cmd_field");
      return;
    }

    handleCommand(cmd, doc);
  }
}

void handleCommand(const char* cmd, StaticJsonDocument<128>& doc) {
  if (strcmp(cmd, CMD_BARRIER_DROP) == 0) {
    servo1.write(SERVO1_ACTIVE);
    digitalWrite(PIN_LASER, HIGH);
    sendAck(cmd, "OK", "barrier_dropped");
  }
  else if (strcmp(cmd, CMD_BARRIER_RAISE) == 0) {
    servo1.write(SERVO1_REST);
    digitalWrite(PIN_LASER, LOW);
    sendAck(cmd, "OK", "barrier_raised");
  }
  else if (strcmp(cmd, CMD_FLAG_RAISE) == 0) {
    servo2.write(SERVO2_ACTIVE);
    sendAck(cmd, "OK", "flag_raised");
  }
  else if (strcmp(cmd, CMD_FLAG_LOWER) == 0) {
    servo2.write(SERVO2_REST);
    sendAck(cmd, "OK", "flag_lowered");
  }
  else if (strcmp(cmd, CMD_LASER_ON) == 0) {
    digitalWrite(PIN_LASER, HIGH);
    sendAck(cmd, "OK", "laser_on");
  }
  else if (strcmp(cmd, CMD_LASER_OFF) == 0) {
    digitalWrite(PIN_LASER, LOW);
    sendAck(cmd, "OK", "laser_off");
  }
  else if (strcmp(cmd, CMD_BUZZ) == 0) {
    int duration = doc["duration"] | 1000;
    digitalWrite(PIN_BUZZER, HIGH);
    buzzerActive = true;
    buzzerEndTime = millis() + duration;
    sendAck(cmd, "OK", "buzzer_on");
  }
  else if (strcmp(cmd, CMD_LED_RED) == 0) {
    const char* mode = doc["mode"] | "on";
    if (strcmp(mode, "on") == 0) {
      digitalWrite(PIN_LED_RED, HIGH);
    } else if (strcmp(mode, "off") == 0) {
      digitalWrite(PIN_LED_RED, LOW);
    }
    sendAck(cmd, "OK", "led_red");
  }
  else if (strcmp(cmd, CMD_LED_GREEN) == 0) {
    const char* mode = doc["mode"] | "on";
    if (strcmp(mode, "on") == 0) {
      digitalWrite(PIN_LED_GREEN, HIGH);
    } else if (strcmp(mode, "off") == 0) {
      digitalWrite(PIN_LED_GREEN, LOW);
    }
    sendAck(cmd, "OK", "led_green");
  }
  else if (strcmp(cmd, CMD_LED_OFF) == 0) {
    const char* target = doc["target"] | "all";
    if (strcmp(target, "all") == 0 || strcmp(target, "red") == 0) {
      digitalWrite(PIN_LED_RED, LOW);
    }
    if (strcmp(target, "all") == 0 || strcmp(target, "green") == 0) {
      digitalWrite(PIN_LED_GREEN, LOW);
    }
    sendAck(cmd, "OK", "led_off");
  }
  else if (strcmp(cmd, CMD_PING) == 0) {
    sendAck(cmd, "OK", "pong");
  }
  else if (strcmp(cmd, CMD_RESET) == 0) {
    servo1.write(SERVO1_REST);
    servo2.write(SERVO2_REST);
    digitalWrite(PIN_LASER, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_LED_GREEN, LOW);
    buzzerActive = false;
    sendAck(cmd, "OK", "reset_complete");
  }
  else {
    sendAck(cmd, "ERR", "unknown_command");
  }
}

void sendAck(const char* cmd, const char* status, const char* message) {
  StaticJsonDocument<96> ack;
  ack["ack"] = status;
  ack["cmd"] = cmd;
  ack["msg"] = message;
  ack["uptime"] = (millis() - startTime) / 1000;
  String output;
  serializeJson(ack, output);
  btSerial.println(output);
  Serial.println(output);
}
