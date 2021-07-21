from matplotlib import cm
import numpy as np
import math
	
# animation!!
# Pacakge Imports
from utils import *
import importlib
import utils
importlib.reload(utils)
import os.path
from os import path
import pandas as pd
import mplcursors
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as patches
from datetime import datetime
import animation_utils
import cv2
import os

def getCarColor(speed, maxSpeed, carID) :
    if(carID == 316120) : return 'black'
    elif(carID == 344120) : return 'red'
    elif(carID == 399120) : return 'white'
    else :
        coolwarm = cm.get_cmap('coolwarm_r')
    
        if speed > 34 :
            return coolwarm(0.999)
        else :
            normVal = speed / 34.0
            return coolwarm(normVal)

def restructCoord(frameSnap) :
    for i in range(len(frameSnap)) :
        if frameSnap[i,9] == 1 :  # If car is going left to right
            # Transform the coordinates so that bbr_x and so on are in sync
            # with cars going from right to left
            
            temp = frameSnap[i,0]
            frameSnap[i,0] = frameSnap[i,4]
            frameSnap[i,4] = temp
            
            temp = frameSnap[i,1]
            frameSnap[i,1] = frameSnap[i,5]
            frameSnap[i,5] = temp
            
            temp = frameSnap[i,2]
            frameSnap[i,2] = frameSnap[i,6]
            frameSnap[i,6] = temp
            
            temp = frameSnap[i,3]
            frameSnap[i,3] = frameSnap[i,7]
            frameSnap[i,7] = temp
            
        # Loop to change to feet
        for j in range(0,8) :
            frameSnap[i,j] *= 3.28084
            
        if math.isnan(frameSnap[i,11]) : frameSnap[i,11] = 0
            
def fillBetweenX(xs) :
    # Minor misalignments between the coordinates causes the fill function
    # to fill color in random spaces. Fixing the numbers to be exact.
    temp = list(xs)
    temp[1] = temp[2]
    temp[3] = temp[0]
    newxs = tuple(temp)
    
    return newxs

def fillBetweenY(ys) :
    temp = list(ys)
    temp[1] = temp[0]
    temp[2] = temp[3]
    newys = tuple(temp)
    
    return newys
	
	


def generate_frames(df, xmin, xmax, ymax, skip_frame, image_folder):
	# xmin, xmax, ymin, ymax = utils.get_xy_minmax(df)

	# Divide all the data into frame numbers(1 ~ 2000). Then save each frame snapshot as a .jpg file
	# within a separate folder to later create an animation.
	img = plt.imread("highway_p1c3.jpg")
	maxFrameNum = int(max(df['Frame #']))    # Find the maximum number of frame
	maxFrameNum = 600
	# if maxFrameNum > 2100:
		# maxFrameNum = 2100
	minFrameNum = int(min(df['Frame #']))    # Find the maximum number of frame
	if 'speed' not in df:
		df['speed'] = 30
	maxSpeed = np.amax(np.array(df[['speed']]))        # Find the maximum speed of cars
	print('Frame: ', minFrameNum, maxFrameNum)
	for i in range(minFrameNum,maxFrameNum):
		if (i%skip_frame==0):
			# Plot dimension setup
			fig, ax = plt.subplots(figsize=(9,6))
			ax.imshow(img, extent=[xmin,xmax,0,ymax])
			plt.xlim(xmin, xmax)
			plt.ylim(0, ymax)
			plt.xlabel('feet')
			plt.ylabel('feet')
			# extract the ID & road coordinates of the bottom 4 points of all vehicles at frame # i
			frameSnap = df.loc[(df['Frame #'] == i)]
			frame_time = frameSnap.Timestamp.iloc[0]
			frameSnap = np.array(frameSnap[['bbr_x','bbr_y','fbr_x','fbr_y','fbl_x','fbl_y','bbl_x','bbl_y',
											'ID','direction','Timestamp', 'speed']])
			animation_utils.restructCoord(frameSnap)
			# Looping thru every car in the frame
			for j in range(len(frameSnap)):
				carID = frameSnap[j,8]
				carSpeed = frameSnap[j,11]
				coord = frameSnap[j,0:8]     # Road Coordinates of the Car
				coord = np.reshape(coord,(-1,2)).tolist()
				coord.append(coord[0])
				xs, ys = zip(*coord)
				xcoord = frameSnap[j,2]
				ycoord = frameSnap[j,3]
				# Displaying information above the car
				if xcoord < xmax and xcoord > xmin and ycoord < ymax :
					plt.text(xcoord, ycoord, str(int(carID)), fontsize=8)
	#                 plt.text(xcoord, ycoord, str(int(carSpeed * 2.2369)) + ' mph', fontsize=8)    
				# Setting up car color
				oneCarColor = animation_utils.getCarColor(carSpeed, maxSpeed, carID)
				# Plotting the car
				newxs = animation_utils.fillBetweenX(xs)
				newys = animation_utils.fillBetweenY(ys)
				ax.plot(newxs, newys, c = oneCarColor)
				ax.fill(newxs, newys, color = oneCarColor)

			plt.title(datetime.fromtimestamp(frame_time).strftime("%H:%M:%S"), pad=20)
			fig.savefig(image_folder + '/' + format(i,"04d") + '.jpg', dpi=80)
			plt.close(fig)
	return
	
def write_video(image_folder, video_name, fps):
	images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
	images.sort()
	frame = cv2.imread(os.path.join(image_folder, images[1]))
	height, width, layers = frame.shape
	video = cv2.VideoWriter(video_name, 0, fps, (width,height))
	for image in images:
		video.write(cv2.imread(os.path.join(image_folder, image)))
	cv2.destroyAllWindows()
	video.release()
	return
	
	