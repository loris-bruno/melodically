import cv2
import numpy as np
import imutils
import time
from threading import Thread
import pygame

# from: https://raspberrypi.stackexchange.com/a/22089
pygame.mixer.init(48000,-16,1,1024)

sounds = 'piano'


# text style
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
color = (200, 200, 200)
thickness = 2

"""
Note class representing a note in the image
"""
class Note: 
    name = ''
    centerX = 0
    centerY = 0
    radius = 0
    contour = []
    def __init__(self, name, centerX, centerY, radius, contour):
        self.name = name
        self.centerX = centerX
        self.centerY = centerY
        self.radius = radius
        self.contour = contour
 
"""
Note color class representing the color assigned to a note
"""
class NoteColor:
    name = '' # name of the note
    color = '' # name of the color
    lower1 = [] # first range lower bound
    upper1 = [] # first range upper bound
    lower2 = [] # second range lower bound
    upper2 = [] # second range upper bound
    
    def __init__(self, name, color, lower1, upper1, lower2 = [], upper2 = []):
        self.name = name
        self.color = color
        self.lower1 = np.array(lower1, dtype="uint8")
        self.upper1 = np.array(upper1, dtype="uint8")
        self.lower2 = np.array(lower2, dtype="uint8")
        self.upper2 = np.array(upper2, dtype="uint8")
    
    """ Compute the color mask
    @param image: the image of which we want to get the color mask
    """
    def get_mask(self, image):
        mask = cv2.inRange(image, self.lower1, self.upper1)
        mask1 = 0
        if self.lower2.size != 0: 
            mask1 = cv2.inRange(image, self.lower2, self.upper2)
        maskTot = mask + mask1
        return maskTot

# for each color to detect, define its spectrum in OpenCV HSV space [0...179]
noteColors = []
noteColors.append(NoteColor('do', 'red', [0, 100, 20], [10, 255, 255], [160,100,20], [179, 255, 255]))
noteColors.append(NoteColor('re', 'orange', [11, 100, 100], [20, 255, 255]))
noteColors.append(NoteColor('mi', 'yellow', [21, 100, 100], [40, 255, 255]))
noteColors.append(NoteColor('fa', 'green', [60, 100, 20], [80, 255, 255]))
noteColors.append(NoteColor('sol', 'cyan', [78, 100, 100], [100, 255, 255]))
noteColors.append(NoteColor('la', 'blue', [100, 100, 10], [120, 255, 255]))
noteColors.append(NoteColor('si', 'pink', [120, 10, 100], [170, 255, 255]))
 
""" Experience main program, process image nad play song
@param image: the image to process
@param sounds: the sounds folder where the note sounds are stored
"""
def make_song(imageName):
    global sounds
    # read image.
    image = cv2.imread(imageName)
    original = image.copy()
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
    notes = []
    colorThreads= []
    
    # start color threads
    for noteColor in noteColors:
        newThread = colorThread(noteColor, imageHSV)
        colorThreads.append(newThread)
        newThread.start()
    
    # wait for all colors to end
    for ct in colorThreads:
        ct.join()
        notes += ct.notes
        
    #cv2.imwrite("result.jpg", original)

    # assign notes to lines
    lineNotes = []
    for note in notes:
        inLine = False
        for line in lineNotes:
            if(line[0].centerY-100 <= note.centerY <= line[0].centerY+100):
                line.append(note)
                inLine = True
        if(not inLine):
            lineNotes.append([])
            lineNotes[len(lineNotes)-1].append(note)

    # sort lines by vertical axis
    lineNotes.sort(key=lambda line:line[0].centerY)

    print('\n --- RESULT ---')
    result = []
    for idx, line in enumerate(lineNotes):
        # sort notes by horizontal axis
        line.sort(key=lambda note:note.centerX)
        print('line: '+str(idx))
        prevCoords = 0
        resultLine = []
        for idxNote, note in enumerate(line):
            resultLine.append(note.name)
            
            if idxNote == 0:
                delay = 1
            else: 
                # compute delay
                delay = (note.centerX - prevCoords) / (2*note.radius) - 1
                if delay < 0:
                    delay = 0
            
            print("delay: "+str(delay))
            # wait and play sound
            time.sleep(delay)
            
            sound = pygame.mixer.Sound('sounds/'+sounds+'/'+note.name+'.wav')
            
            
            sound.play(fade_ms=1000)
            
            
            print('\t'+note.name+': ', '(', note.centerX,',',note.centerY,')')
            
            # draw detected note on the image
            org = (note.centerX-20, note.centerY+10)
            cv2.circle(original, (note.centerX, note.centerY), 7, (255, 255, 255), -1)
            original = cv2.putText(original, note.name, org, font, fontScale, color, thickness, cv2.LINE_AA)
            cv2.drawContours(original, [note.contour], -1, (36, 255, 12), 5)
            
            prevCoords = note.centerX
        result.append(resultLine)
    cv2.imwrite("result.jpg", original)
    return result
    
""" 
Thread class to process color to detect notes 
"""
class colorThread(Thread):
    """ constructor
    @param noteColor: the notecolor to process
    @param imageHSV: original image in HSV space
    """
    def __init__(self, noteColor, imageHSV):
        Thread.__init__(self)
        self.value = None
        self.noteColor = noteColor
        self.imageHSV = imageHSV
        
    def run(self):        
        # get the color mask from the original image
        mask = self.noteColor.get_mask(self.imageHSV)
        
        # filter out some noise
        # source: https://stackoverflow.com/a/42812226
        nb_blobs, im_with_separated_blobs, stats, _ = cv2.connectedComponentsWithStats(mask)
        sizes = stats[:, -1]
        sizes = sizes[1:]
        nb_blobs -= 1
        min_size = 100
        mask_result = np.zeros_like(im_with_separated_blobs)
        
        # for every component in the image, keep it only if it's above min_size
        for blob in range(nb_blobs):
            if sizes[blob] >= min_size:
                mask_result[im_with_separated_blobs == blob + 1] = 255
        
        mask_result = mask_result.astype(np.uint8)
        
        '''if(self.noteColor.name == 'si'):
            maskS=cv2.resize(mask_result, (960,540))
            cv2.imshow('blue mask', maskS)
            cv2.waitKey(0)'''
    
        # Find contours
        cnts = cv2.findContours(mask_result, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cnts = imutils.grab_contours(cnts)
        
        circles = 0 # number of detected circles
        
        # Using cv2.putText() method
        self.notes = []
        for c in cnts:
            perimeter = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * perimeter, True)
            if len(approx) > 5:
                # filter by radius size
                (cx, cy), radius = cv2.minEnclosingCircle(c)
                if radius < 50:
                    continue
                # compute the center of the contour
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    newNote = Note(self.noteColor.name, cX, cY, radius, c)
                    self.notes.append(newNote)
                    print("\t center: (", cX,',',cY,'), radius: ',radius)
                    org = (cX-20, cY+10)
                    
                    circles += 1
        print("\n\t n of ",self.noteColor.name+"("+self.noteColor.color+"): ", circles)

""" Set sounds location
@param newSounds: folder string
"""
def setSounds(newSounds):
    global sounds
    sounds = newSounds
    
