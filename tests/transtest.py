import time
from rpi_ws281x import Color
from threads.ledstrip import ledStrip

ledstrip = ledStrip()

def transition(currentColor, targetColor, duration, fps):
    distance = colorDistance(currentColor, targetColor)
    increment = calculateIncrement(distance, fps, duration)
    for i in range(0, int(fps)):
        transitionStep(currentColor, targetColor, increment)
        time.sleep(duration/fps)

def colorDistance(currentColor, targetColor):
    distance = [0, 0, 0]
    for i in range(len(currentColor)):
        distance[i] = abs(currentColor[i] - targetColor[i])
    return distance

def calculateIncrement(distance, fps, duration):
    increment = [0, 0, 0]
    for i in range(len(distance)):
        inc = abs(distance[i] / fps)
        increment[i] = inc
    return increment

def transitionStep(currentColor, targetColor, increment):
    for i in range(len(currentColor)):
        if currentColor[i] > targetColor[i]:
            currentColor[i] -= increment[i]
            if currentColor[i] <= targetColor[i]:
                increment[i] = 0
        else:
            currentColor[i] += increment[i]
            if currentColor[i] >= targetColor[i]:
                increment[i] = 0
    setColor(currentColor)

def setColor(color):
    #print(f'r:{int(color[0])} g:{int(color[1])} b:{int(color[2])}')
    ncolor = Color(int(color[0]), int(color[1]), int(color[2]))
    ledstrip.colorchange(ncolor, sticky=False, savestate=False)

def hexPercent(color):
    percent = (color / float(0xFF)) * 100
    return percent

if __name__ == '__main__':
    try:
        waittime = 0
        duration = 0
        fps = 30
        currentColor = [50, 100, 200]
        nextColor = [20, 10, 0]

        stime = time.time()
        transition(currentColor, nextColor, duration, fps)
        print(time.time()-stime)

        time.sleep(5)

        currentColor = [20, 10, 0]
        nextColor = [255, 255, 255]

        stime = time.time()
        transition(currentColor, nextColor, duration, fps)
        print(time.time()-stime)

        time.sleep(5)

        currentColor = [255, 255, 255]
        nextColor  = [20, 10, 0]

        stime = time.time()
        transition(currentColor, nextColor, duration, fps)
        print(time.time()-stime)

    except KeyboardInterrupt:
        print("Intrerrupted by user")
        pass
    finally:
        print("Program stopped")
