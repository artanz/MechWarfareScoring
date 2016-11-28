/*
	MWScore Transponder
	
	XBEE setup:
	ATBD = 5 (38400bps)
	ATID = 6200
	MY   = 6200 + TRANSPONDER_ID
	DL   = 6201
	CH   = c
	
	Scoring Receiver XBEE setup (Send Broadcast message)
  ATBD = 5 (38400bps)
  ATID = 6200
  MY   = 6201
  DL   = FFFF
  DH   = 0
  CH   = c
  
*/ 

#include <TimerOne.h>
#include <PinChangeInt.h>

#define XBEE_BAUDRATE 38400

#define PANELMASK  240
#define PANEL1     112
#define PANEL2     176
#define PANEL3     208
#define PANEL4     224

#define MS_COOLDOWN 1000
#define MS_SIGNAL 50

#define LED_RATE 50
#define LED_PERIOD 300 // LED_RATE * 6

//#define TimerMS 7813                // 128 Hz
//#define TimerMS 15625               //  64 Hz 
//#define TimerMS 31250               //  32 Hz
//#define TimerMS 62500               //  16 Hz
//#define TimerMS 125000              //   8 Hz
#define TimerMS 250000              //   4 Hz
//#define TimerMS 500000              //   2 Hz
//#define TimerMS 1000000             //   1 Hz
//#define TimerMS 2000000             // 0.5 Hz

volatile uint8_t hit = 0;
volatile uint8_t hitpoint = 20;
volatile uint8_t panel = 0;
uint8_t id;

// Arduino Pin Assignments
int hiti = 3;
int hitu = 2;

int tp1 = 4;
int tp2 = 5;
int tp3 = 6;
int tp4 = 7;

// ID Pin Assignments (Analog Pins)
int sw0 = A0;
int sw1 = A1;
int sw2 = A2;
int sw3 = A3;
int sw4 = A4;
int sw5 = A5;
int sw6 = A6;
int sw7 = A7;

void setup() {
  pinMode(hiti, OUTPUT);
  pinMode(hitu, OUTPUT);
  
  pinMode(tp1, INPUT_PULLUP);
  pinMode(tp2, INPUT_PULLUP);
  pinMode(tp3, INPUT_PULLUP);
  pinMode(tp4, INPUT_PULLUP);
  
  PCintPort::attachInterrupt(tp1, hittp1, CHANGE);
  PCintPort::attachInterrupt(tp2, hittp2, CHANGE);
  PCintPort::attachInterrupt(tp3, hittp3, CHANGE);
  PCintPort::attachInterrupt(tp4, hittp4, CHANGE);
  
  pinMode(sw0, INPUT);
  pinMode(sw1, INPUT);
  pinMode(sw2, INPUT);
  pinMode(sw3, INPUT);
  pinMode(sw4, INPUT);
  pinMode(sw5, INPUT);
  pinMode(sw6, INPUT);
  pinMode(sw7, INPUT);
  
  Serial.begin(XBEE_BAUDRATE);

  // set ID intially
  id = 63 - (0x3f & PINC);

  // set up interrupt to send HP status message
  delay(50);
  Timer1.initialize(TimerMS);
  Timer1.attachInterrupt(ISRTimer1);
  delay(50);
}

void loop() {
  uint32_t delayms = 0;
  byte receive[3];

  // update ID when changed
  id = 63 - (0x3f & PINC);

  // Check for HP change
  // Scoring Receiver sends broadcast message to set HP
  // If no message default is 20 HP
  // Receive message 0x55 ID 255-ID HP
  if (Serial.available() > 0) {
    Serial.readBytes(receive,4);
    if(receive[0] == 0x55) {
      if((receive[1] == id) && ((receive[1] + receive[2]) == 255)) {
        hitpoint = (int)receive[3];
      }
    }
  }
  
  if ((hit != 0) && (hitpoint > 0)) {		
    // determine panel that was hit
    if ((hit & PANELMASK) == PANEL1) {
      delayms = MS_SIGNAL * 1;
      panel = 1;
      }
    else if ((hit & PANELMASK) == PANEL2) {
      delayms = MS_SIGNAL * 2;
      panel = 2;
      }
    else if ((hit & PANELMASK) == PANEL3) {
      delayms = MS_SIGNAL * 3;
      panel = 3;
      }
    else if ((hit & PANELMASK) == PANEL4) {
      delayms = MS_SIGNAL * 4;
      panel = 4;
      }
    else {
      delayms = MS_SIGNAL * 5;
      panel = 5;
      }
    
    if(panel != 0) {			
      // hit output high
      hitpoint--;
      digitalWrite(hiti, HIGH);

      // delay and reset hit output
      delay(delayms);
      digitalWrite(hiti, LOW);
			
      // blink LED board 3 times
      for (int x = 0; x < 3; x++)
      {
        digitalWrite(hitu, HIGH);
        delay(LED_RATE);
        digitalWrite(hitu, LOW);
        delay(LED_RATE);
      }
      // delay for the remaining cooldown period
      delay(MS_COOLDOWN - LED_PERIOD - delayms);
    }
    
    // reset variables
    hit = 0;
    delayms = 0;
    panel = 0;
  }

  // leave LED on board when dead
  if (hitpoint == 0) {
    digitalWrite(hitu, HIGH);
    }
  else {
    digitalWrite(hitu, LOW);
  }
  
}

void ISRTimer1(){
  // tx hit packet
  Serial.write((uint8_t) 0x55);
  Serial.write((uint8_t) id);
  Serial.write((uint8_t) (0xff - id));
  Serial.write((uint8_t) panel);
  Serial.write((uint8_t) hitpoint);
}

void hittp1() {
  hit = PANEL1;
}

void hittp2() {
  hit = PANEL2;
}

void hittp3() {
  hit = PANEL3;
}

void hittp4() {
  hit = PANEL4;
}



