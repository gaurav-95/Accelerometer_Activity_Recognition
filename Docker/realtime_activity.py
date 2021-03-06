# -*- coding: utf-8 -*-
"""Analysis_data_from_sw.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SKPJAy2thrTZZYbSJcvMgf4sfomIFADx
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"    
from datetime import datetime
from dateutil.tz import gettz
from datetime import timedelta
import requests
import pandas as pd
import numpy as np
from tensorflow import keras
from numpy import argmax
from apscheduler.scheduler import Scheduler


sched = Scheduler()
sched.start()

def flatten(List_2D):
    List_flat=[]
    for i in range(len(List_2D)): #Traversing through the main list
        for j in range (len(List_2D[i])): #Traversing through each sublist
            List_flat.append(List_2D[i][j])
    return List_flat

def get_frames(df, frame_size, hop_size):

    N_FEATURES = 3
    
    frames = []
    for i in range(0, len(df) - frame_size, hop_size):
        x = df['x'].values[i: i + frame_size]
        y = df['y'].values[i: i + frame_size]
        z = df['z'].values[i: i + frame_size]
        
        frames.append([x, y, z])
  
    # Bring the segments into a better shape
    frames = np.asarray(frames).reshape(-1, frame_size, N_FEATURES)

    return frames

model_h5  = 'activity_detectv9.h5'
model = keras.models.load_model(model_h5)

secret_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJkZWJhbmphbiIsImlhdCI6MTYxNjY0NjA3OH0.Tfyog7lHPADpickUc1itaxdC_fs4_eAxLQDY3G9C5Z4"
frame_size = 120
hop_size = frame_size*1

user_url = "https://apiserverparentprotect.herokuapp.com/get-active-users"

def main():
    now = datetime.now(tz=gettz('Asia/Kolkata'))
    prev = now - timedelta(seconds=5)
    timestamp = prev.strftime("%d/%m/%Y %H:%M:%S")
    
    #print(now)
    #print(prev)
    
    print(timestamp)
    user_list = {"secret_token": secret_token, "timestamp": timestamp}
    response = requests.post(user_url, json=user_list)
    
    #print(response)
    user = response.json()['data']['users']
    
    #print(user)
    #user = ['607c1911676b1700046ae8ea']

    from_time = prev.strftime("%d/%m/%Y") + "%20" + prev.strftime("%H:%M:%S")
    #print(from_time)

    to_time = now.strftime("%d/%m/%Y")+ "%20" + now.strftime("%H:%M:%S")
    #print(to_time)
    
    states=[]
    
    for i in user:
        user_data = requests.get("https://apiserverparentprotect.herokuapp.com/accelerometer-data?secret_token="+secret_token+"&type=accelerometer&dateFrom="+from_time+"&dateTo="+to_time+"&userID="+i)
        useracc = user_data.json()['data']
        
        tot=len(useracc["accelerometer_data_array"])
        #print(tot)
        
        for j in range(0,tot):
            useracc['accelerometer_data_array'][j].pop(0)
        
        a=flatten(useracc['accelerometer_data_array'])
        
        v = np.array(a[0::2], float)
        v = v*0.0078125 ##(1/128)
        
        x = v[0::3]
        y = v[1::3]
        z = v[2::3]
        #print(x,y,z)
        
        xyz = pd.DataFrame(list(zip(x, y, z)), columns =['x', 'y', 'z'])
        
        X = get_frames(xyz, frame_size, hop_size)#, timestamps
        #print(X.shape)
      
        #reshaping
        a=X.shape
        a = a + (1,)
        X = X.reshape(a)
        #print(X.shape)

        prediction = (model.predict(X) > 0.5).astype("int32")
        summed = np.sum(prediction, axis=0)
        label_val = argmax(summed)

        if label_val == 0:
            state="running"
        elif label_val == 1:
            state="sitting"
        elif label_val == 2:
            state="walking"
        else:
            state="unknown"
            
        user_data={"state": state, "timestamp": timestamp, "user_id": i}
        states.append(user_data.copy())
                  
    data = {"secret_token" : secret_token , "states" : states}
    #print(data)
    url = "https://apiserverparentprotect.herokuapp.com/record-state"
    requests.post(url, json=data)
    #print(response)
    print(states)

sched.add_interval_job(main, seconds = 6)
#sched.modify(max_instances=10)
