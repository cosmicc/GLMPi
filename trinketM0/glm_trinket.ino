/*  Galaxy Lighting Module 
 *  Trinket M0 Arduino code
 */
 
#include "IRLibAll.h"
#include <IRLib_P01_NEC.h>    
#include <IRLib_P02_Sony.h>
#include <IRLib_P03_RC5.h>
#include <IRLib_P04_RC6.h>
#include <IRLib_P05_Panasonic_Old.h>
#include <IRLib_P07_NECx.h>   
#include <IRLibCombo.h> 

IRsend mySender;
IRrecvPCI myReceiver(2); //create receiver and pass pin number
IRdecode myDecoder;   //create decoder

int inputPin = A0;

String inputString = "";         // a String to hold incoming data
bool stringComplete = false;
const int numReadings = 20;
int readings[numReadings];      // the readings from the analog input
int readIndex = 0;              // the index of the current reading
int total = 0;                  // the running total
int average = 0;                // the average

long lastlightcheck = 0;
long lastlightsend = 0;

void serialcheck() {
  if (Serial1.available() > 0) {
    // get the new byte:
    char inChar = (char)Serial1.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void sendit(String ctype, String bits, String icode) {
  myReceiver.disableIRIn();
  switch(ctype.toInt()) {
  case 1:
    mySender.send(NEC,icode.toInt(),0);
    break;
  case 2:
    mySender.send(SONY,icode.toInt(),0);
    break;
  case 3:
    mySender.send(RC5,icode.toInt(),0); 
    break;
  case 4:
    mySender.send(RC6,icode.toInt(),0);
  break;
  }
  myReceiver.enableIRIn();
}

void setup() {
  Serial1.begin(9600);
  //Serial.begin(9600);  // DEBUG
  inputString.reserve(200);
  delay(.5); while (!Serial1);
  myReceiver.enableIRIn(); // Start the receiver
  //Serial1.println(F("Ready to receive IR signals"));
  for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    readings[thisReading] = 0;
  }
  lastlightcheck = millis();
  lastlightsend = millis();
}

void loop() {
    if (myReceiver.getResults()) {
    myDecoder.decode();           //Decode it
    if (myDecoder.value != 0 && myDecoder.value != 4294967295) {
      //Serial1.print("#");
      Serial1.print(myDecoder.protocolNum);
      Serial1.print(":");
      Serial1.print(myDecoder.bits); 
      Serial1.print(":");
      Serial1.println(myDecoder.value);
    }
    myReceiver.enableIRIn();      //Restart receiver
  }
  serialcheck();
  if (stringComplete) {
    //Serial.println(inputString);  // DEBUG
    String ctype = getValue(inputString, ':', 0);
    String icode = getValue(inputString, ':', 2);
    String bits = getValue(inputString, ':', 1);
    sendit(ctype, bits, icode);
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
  if (millis() - lastlightcheck >= 5) {
    total = total - readings[readIndex];
    readings[readIndex] = analogRead(inputPin);
    total = total + readings[readIndex];
    readIndex = readIndex + 1;
    if (readIndex >= numReadings) {
      readIndex = 0;
    }
    average = total / numReadings;
    //Serial.println(average);  // DEBUG
    lastlightcheck = millis();
  }
  if (millis() - lastlightsend > 1000) {
    Serial1.print("+");
    Serial1.println(average);
    lastlightsend = millis();
  }
}
