import cv2
import numpy as np

from Sequencer import Sequencer

print(cv2.__version__)

DICE_SIZE = 18
BLUR_FACTOR = 5
RED_LOW_THRESHOLD = 209
MIN_PIP_AREA = 10

seq = Sequencer(120)
sequenceTable = []


def resizeRect(rect, sizeFactor):
    return rect[0], (rect[1][0] + sizeFactor, rect[1][1] + sizeFactor), rect[2]


def setTempo(tempo):
    seq.setTempo(tempo)


cap = cv2.VideoCapture(1)
windowname = 'DiceRecognizer'
cv2.namedWindow(windowname, cv2.WINDOW_AUTOSIZE)
cv2.createTrackbar('Tempo', windowname, 40, 300, setTempo)
# cv2.createTrackbar('Dice Size Threshold', windowname, 5, 20, fun)
# cv2.createTrackbar('Dice Size Threshold', windowname, 5, 20, fun)
# threshold_value = cv2.getTrackbarPos('Dice Size Threshold', windowname)

i = 0
while i < 10:
    backgroundRet, backgroundFrame = cap.read()
    i += 1
# Change backgroundFrame to grayscale
backgroundFrame = cv2.cvtColor(backgroundFrame, cv2.COLOR_BGR2GRAY)



while True:
    # Capture video frame-by-frame
    ret, originalFrame = cap.read()
    originalFrame = cv2.rotate(originalFrame, cv2.ROTATE_180)
    # Change originalFrame to RGBa
    img = cv2.cvtColor(originalFrame, cv2.COLOR_BGR2BGRA)


    height, width, layers = img.shape
    steps = seq.steps
    notes = seq.notes
    notesPx = height / notes
    stepsPx = width / notes

    # Layer Separation
    blurred = cv2.medianBlur(img, BLUR_FACTOR)
    blue = cv2.split(blurred)[0]
    green = cv2.split(blurred)[1]
    red = cv2.split(blurred)[2]

    # Fetch the dice contours using red threshold. invert.
    diceblocks = cv2.threshold(red, RED_LOW_THRESHOLD, 255, 1)  # 185 --> 235
    invdiceblocks = 255 - diceblocks[1]
    # cv2.imshow("diceblocks",invdiceblocks)

    # do a distance transform and normalize that so we can visualize and threshold it
    pyramids = cv2.distanceTransform(invdiceblocks, 2, 3)
    # cv2.normalize(pyramids, pyramids, 0, 1.2, cv2.NORM_MINMAX)

    # obtain markers for the watershed algorithm by thresholding
    markers = cv2.threshold(pyramids, 0.5, 1, 0)[1]
    cv2.imshow("markers", markers)

    # dilate the dice markers with a DICE_SIZE px element to capture all pips in the contours
    # newImg = cv2.dilate(markers, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(DICE_SIZE, DICE_SIZE)))

    # convert the numpy matrix from float [0..1] to int [0..255]
    bwImg = cv2.convertScaleAbs(markers * 255)

    # capture those contours!
    pyramids, hierarchy = cv2.findContours(bwImg.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print(str(len(pyramids)) + " dice.")

    # fit a rotated rectangle on the distance transformed pyramid
    for pyramid in pyramids:
        rect = cv2.minAreaRect(pyramid)
        # resize it to a certain dice size
        rect = resizeRect(rect, DICE_SIZE)

        floatBox = cv2.boxPoints(rect)
        intBox = np.int0(floatBox)
        bwImg = cv2.drawContours(bwImg, [intBox], 0, (255, 0, 0), -1)

        pts1 = floatBox
        a, b, c, d = cv2.boundingRect(intBox)
        pts2 = np.float32([[a, b], [a + c, b], [a, b + d], [a + c, b + d]])

        M = cv2.getPerspectiveTransform(pts1, pts2)
        dst = cv2.warpPerspective(bwImg, M, pts2.shape)

    # capture those large contours!
    contours, hierarchy = cv2.findContours(bwImg.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # filter out the pips, and then cut out those using the contour areas
    pips = 255 - cv2.threshold(cv2.cvtColor(blurred, cv2.COLOR_RGB2GRAY), 200, 255, 1)[1]
    onlypips = cv2.bitwise_and(bwImg, pips)
    # cv2.imshow("onlypips", onlypips)

    dice = cv2.cvtColor(onlypips, cv2.COLOR_GRAY2RGB)
    dice_results = [0, 0, 0, 0, 0, 0]
    wrongdice = 0

    notesTrig = []
    # look at each dice face and determine number of pips
    for contour in contours:
        pips = 0

        # get the coordinates to cut out the dice face from the image
        # with only the pips
        rect = cv2.minAreaRect(contour)
        floatBox = cv2.boxPoints(rect)
        intBox = np.int0(floatBox)
        a, b, c, d = cv2.boundingRect(intBox)

        # cut out the dice face
        subimage = onlypips[b:b + d, a:a + c]


        # count the number of contours
        pip_contours, subhierarchy = cv2.findContours(subimage.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for pip in pip_contours:
            # count pips only if they are of a certain size
            if cv2.contourArea(pip) >= MIN_PIP_AREA:
                M = cv2.moments(contour)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.circle(img, (cX, cY), 3, (255, 0, 0), 5)
                if [np.floor(cX / stepsPx), np.floor(cY / notesPx)] not in notesTrig:
                    notesTrig.append([np.floor(cX / stepsPx), np.floor(cY / notesPx)])

                pips = pips + 1

        # log erroneous dice
        if pips > 6 or pips == 0:
            wrongdice = wrongdice + 1
            # print(pips)
        else:
            dice_results[pips - 1] = dice_results[pips - 1] + 1
            cv2.putText(img, str(pips), (a, b - 5), 0, 1, (0, 0, 255))

    # print out the results
    # print(dice_results)
    # print(str(wrongdice) + " erroneous objects found.")

    cv2.drawContours(img, contours, -1, (255, 255, 0), 4)

    # Overlay Drawings

    blk = np.zeros(img.shape, np.uint8)

    # horizontal lines
    for i in range(1, int(height / notesPx)):
        cv2.line(blk, (0, int(notesPx * i)), (width, int(notesPx * i)), (0, 0, 255), 2)

    # Vertical lines
    for i in range(1, int(width / stepsPx)):
        cv2.line(blk, (int(stepsPx * i), 0), (int(stepsPx * i), height), (0, 0, 255), 2)

    currStep = seq.getCurrentStep()
    cv2.rectangle(blk, (int(stepsPx * currStep), 0), (int(stepsPx * currStep + stepsPx), height), (255, 0, 0),
                  cv2.FILLED)
    print(notesTrig)
    seq.setSequenceTable(notesTrig)
    seq.updateSequence()
    # seq.setSequenceTable(notesTrig)
    # Generate result by blending both images (opacity of rectangle image is 0.25 = 25 %)
    img = cv2.addWeighted(img, 1.0, blk, 0.7, 1)

    # cv2.imshow('Dice', dice)
    cv2.imshow(windowname, img)


    # cv2.imshow('Original', img)

    # cv2.cvtColor(blurred, cv2.COLOR_RGB2GRAY))

    def doCallbackTest(value):
        # newImg = cv2.adaptiveThreshold(newImg,255,1,0,13,value)
        tmpImg = red.copy()
        newImg = 255 - cv2.threshold(tmpImg, value, 255, 1)[1]  # cv2.threshold(src, thresh, maxval, type
        # cv2.drawContours(tmpImg,contours,-1,(0,255,0),1)
        cv2.imshow('Dice', newImg)


    # cv2.imshow('Original',tmpImg)
    lowThreshold = 1
    max_lowThreshold = 255
    # cv2.namedWindow("Dice", 0)
    # cv2.createTrackbar('Value','Dice',lowThreshold, max_lowThreshold, doCallbackTest)
    # doCallback(lowThreshold)
    # cv2.imshow(windowname, originalFrame)


    # Keypress interrupt exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera resource
cap.release()
cv2.waitKey(0)
cv2.destroyAllWindows()
