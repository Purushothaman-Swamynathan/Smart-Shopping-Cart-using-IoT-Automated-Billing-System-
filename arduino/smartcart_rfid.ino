#include <SPI.h>
#include <MFRC522.h>

// Arduino UNO + RC522 wiring:
// SDA/SS -> D10, RST -> D9, MOSI -> D11, MISO -> D12, SCK -> D13
#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  Serial.println("SMARTCART_RFID_READY");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  Serial.println(uid); // Python serial listener can consume this UID

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(800); // basic duplicate-scan debounce
}
