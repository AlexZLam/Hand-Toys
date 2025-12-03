import cv2
import mediapipe as mp
import time
import numpy as np 



class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.75, trackCon=0.3):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        blank = np.zeros_like(img)
        blankScreen = False

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    if(blankScreen):
                        self.mpDraw.draw_landmarks(blank, handLms, self.mpHands.HAND_CONNECTIONS)
                    else:
                        self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        if(blankScreen):
            return blank   # <-- return blank instead of original
        else:
            return img
    
    def findPositions(self, img, draw=True):   
        handsLmLists = []
        if self.results.multi_hand_landmarks:
            for handLms, handType in zip(self.results.multi_hand_landmarks,
                                        self.results.multi_handedness):
                lmList = []
                h, w, c = img.shape
                for id, lm in enumerate(handLms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                    if draw and id == 4:  # thumb tip highlight
                        cv2.circle(img, (cx, cy), 7, (250, 255, 0), cv2.FILLED)

                handsLmLists.append({
                    'lmList': lmList,
                    'type': handType.classification[0].label  # 'Left' or 'Right'
                })
        return handsLmLists



def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)  
        lmList = detector.findPosition(img)      
        img = cv2.flip(img, 1)
        
        
        if len(lmList) != 0: 
            print(lmList[4])

        cTime = time.time()
        fps = 1/(cTime-pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10,70), 
            cv2.FONT_HERSHEY_COMPLEX, 3, (0,0,255), 3)

        cv2.imshow('Image', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    main()
