# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 20:55:27 2021

@author: Gaurav
"""

from datetime import datetime
from dateutil.tz import gettz
from datetime import timedelta
import requests
import time
import pandas as pd
import numpy as np
from tensorflow import keras
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from numpy import argmax

#def flatten(List_2D):
#    List_flat=[]
#    for i in range(len(List_2D)): #Traversing through the main list
#        for j in range (len(List_2D[i])): #Traversing through each sublist
#            List_flat.append(List_2D[i][j])
#    return List_flat

def prepare(data):
    data=data[["x","y","z"]]

    data = data.dropna()
  
    scaler1 = StandardScaler()
    X = scaler1.fit_transform(data)

    scaler = MinMaxScaler()
    X = scaler.fit_transform(data)
  
    scaled_X = pd.DataFrame(data = X, columns = ['x', 'y', 'z'])
  
    return scaled_X

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

model_h5  = 'fall_detect_v2.h5'
model = keras.models.load_model(model_h5)

secret_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJkZWJhbmphbiIsImlhdCI6MTYxNjY0NjA3OH0.Tfyog7lHPADpickUc1itaxdC_fs4_eAxLQDY3G9C5Z4"
frame_size = 16
hop_size = frame_size*1



def main():
    tot_falls=0
    while True:
    
        now = datetime.now(tz=gettz('Asia/Kolkata'))
        prev = now - timedelta(seconds=2)
        timestamp = prev.strftime("%d/%m/%Y %H:%M:%S")
        #print(now)
        #print(prev)
        print(timestamp)

        user_list = {"secret_token": secret_token, "timestamp": timestamp}
        user_url = "https://apiserverparentprotect.herokuapp.com/get-active-users"
        response = requests.post(user_url, user_list)
        #print(response)
        user = response.json()["data"]['users']
        #print(user)

        from_time = prev.strftime("%d/%m/%Y") + "%20" + prev.strftime("%H:%M:%S")
        #print(from_time)

        to_time = now.strftime("%d/%m/%Y")+ "%20" + now.strftime("%H:%M:%S")
        #print(to_time)
    
        time.sleep(5)
    
        for i in user:
            user_data = requests.get("https://apiserverparentprotect.herokuapp.com/accelerometer-data?secret_token="+secret_token+"&type=accelerometer&dateFrom="+from_time+"&dateTo="+to_time+"&userID="+i)
            useracc = user_data.json()['data']

            x = useracc['acc_data'][0::3]
            y = useracc['acc_data'][1::3]
            z = useracc['acc_data'][2::3]
            #print(x,y,z)

            xyz = pd.DataFrame(list(zip(x, y, z)), columns =['x', 'y', 'z'])
            scaled_X = prepare(xyz)

            X = get_frames(scaled_X, frame_size, hop_size)#, timestamps
            #print(X.shape)
      
            #reshaping
            a=X.shape
            a = a + (1,)
            X = X.reshape(a)
            #print(X.shape)

            prediction = model.predict_classes(X)
            
            label_val = argmax(prediction)
            print(label_val)
            
            if label_val == 0:
                state="nofall"
            else:
                state="fall"
                tot_falls += 1
            
            print(i, state, tot_falls)
            data = {"secret_token" : secret_token , "state" : state+str(tot_falls) , "timestamp" : timestamp , "user_id" : i}
            #print(data)
            url = "https://apiserverparentprotect.herokuapp.com/record-state"
            response = requests.post(url, data)
      
            #print(response)
    time.sleep(5)
      
main()