'''
This module contains scripts used to load and parse the data for the Touchalytics, BrainRun and HMOG dataset. The HMOG dataset
was not used in the experiments, due to the swipes being collected for a different type of activities, and the model being
unable to generalize to the new data.
'''

from re import U
from pymongo import MongoClient
from tqdm import tqdm
import pandas as pd
from glob import glob
from datetime import datetime

def load_brainrun(NUMBER_OF_USERS, GESTURES, MIN_GESTURES_PER_SESSION, MAX_SESSIONS_PER_USER, MIN_GESTURES, *args):
    client = MongoClient('127.0.0.1')
    db=client.BrainRun

    devices = db['devices']
    gestures = db['gestures']
    users = db['users']

    # Filter devices with multiple users

    res = devices.aggregate([
        {
            '$group': {
                '_id': '$device_id', 
                'count': {
                    '$sum': 1
                }
            }
        }, {
            '$match': {
                'count': {
                    '$gt': 1
                }
            }
        }, {
            '$sort': {
                'count': -1
            }
        }
    ])

    ids = [x['_id'] for x in res]
    not_good = []
    bad_devices = []

    for id in ids:
        res = devices.find({'device_id': id})
        res = set(x['user_id'] for x in res)
        not_good.extend(res)
        bad_devices.append(id)
        if len(res) != 1:
            print(id, res)

    res = users.find({'_id': {'$in': not_good}})

    # Gets users in the form [user_id: {devices: {device list}}]

    users = devices.distinct('user_id')[:NUMBER_OF_USERS]
    all_users = []

    for user in tqdm(users):
        dev = [x for x in devices.find({'user_id': user}) if x['device_id'] not in bad_devices]
        for i,d in enumerate(dev):
            width = d['width'] 
            height = d['height'] 
            sessions = gestures.aggregate(
                [
                    {'$match': {
                        '$and': [
                            {'device_id': d['device_id']},
                            {'type': {'$in': GESTURES}}
                        ]
                    }},
                    {'$group': 
                        {
                            '_id': '$session_id',
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$sort':
                        {'count': -1}
                    },
                    {
                        '$match': {
                            'count': {'$gt': MIN_GESTURES_PER_SESSION}
                        }
                    },
                    {
                        '$limit': MAX_SESSIONS_PER_USER
                    }
                ]
            )

            res = [x for x in sessions]
            total_gestures = sum(x['count'] for x in res)
            dev[i]['total_gestures'] = total_gestures
            dev[i]['sessions'] = res

            for i,session in enumerate(res):
                data = gestures.aggregate([
                    {
                        '$match': {
                            'session_id': session['_id'],
                            't_start': {'$gt': 0},
                            'type': {'$in': GESTURES}
                        }
                    }, {
                        '$sort': {
                            't_start': 1
                        }
                    }
                ])

                data = [x for x in data]
                bad = []
                for di in range(len(data)):
                    if not len(data[di]['data']):
                        bad.append(data[di]['_id'])
                        continue
                    for dj in range(len(data[di]['data'])):
                        try:
                            data[di]['data'][dj]['dx'] /= width
                            data[di]['data'][dj]['dy'] /= height
                            data[di]['data'][dj]['moveX'] /= width
                            data[di]['data'][dj]['moveY'] /= height
                            data[di]['data'][dj]['vx'] /= width
                            data[di]['data'][dj]['vy'] /= height
                            data[di]['data'][dj]['x0'] /= width
                            data[di]['data'][dj]['y0'] /= height
                        except:
                            bad.append(data[di]['_id'])
                # if len(bad):
                #     print(bad)
                data = [x for x in data if x['_id'] not in bad]

                        # data[di]['data'][dj]['moveX'] = min(max(data[di]['data'][dj]['moveX'], 0), 1)
                        # data[di]['data'][dj]['moveY'] = min(max(data[di]['data'][dj]['moveY'], 0), 1)
                        # data[di]['data'][dj]['x0'] = min(max(data[di]['data'][dj]['x0'], 0), 1)
                        # data[di]['data'][dj]['y0'] = min(max(data[di]['data'][dj]['y0'], 0), 1)

                res[i]['gestures'] = data

        usr = {'user_id': user,
        'devices': sorted([x for x in dev if x['total_gestures'] != 0], key = lambda x: x['total_gestures'], reverse = True),
        'user_gestures': max(x['total_gestures'] for x in dev) if len(dev) > 0 else 0}
        if  usr['user_gestures'] >= MIN_GESTURES:
            all_users.append(usr)
            
    # print(len(all_users))

    # pj(all_users[0]['devices'][0]['sessions'][0]['data'])

    users = [x for x in sorted(all_users, key=lambda x:x['user_gestures'], reverse = True) if x['user_gestures'] >= MIN_GESTURES]
    # print(len(all_users))
    print(len(users))

    return users

def load_touchalytics(NUMBER_OF_USERS, GESTURES, MIN_GESTURES_PER_SESSION, MAX_SESSIONS_PER_USER, MIN_GESTURES, ORIENTATION = [0,1,2]):
    df = pd.read_csv('gestures_devices_users_games_data/touchalytics/data.csv', names = ['phoneId',
    'userId', 
    'documentId', 
    'time', 
    'action', 
    'phone_orientation', 
    'x', 
    'y', 
    'pressure', 
    'area covered', 
    'finger orientation'])

    df.sort_values(by = ['userId', 'documentId', 'time'], inplace = True)

    users = pd.unique(df['userId'])
    user_list = []

    for user in tqdm(users):
        user_list.append({
            'user_id': user,
            'devices': [{
                '_id': 0,
                'user_id': user,
                'device_id': 0,
                'width': 480,
                'height': 800,
                'sessions': [
                    {'gestures': [],},
                    {'gestures': [],},
                    {'gestures': [],},
                ]
            }],
        })
        u_index = user 

        gestures = []
        user_df = df[df['userId'] == user]

        touch_started = False
        swipe = []
        for index, row in df[(df['userId'] == user)].iterrows():
            if row['documentId'] in list(range(0,5)): session_index = 0
            if row['documentId'] in list(range(5,6)): session_index = 1
            if row['documentId'] in list(range(6,7)): session_index = 2

            if row['phone_orientation'] not in ORIENTATION:
                continue

            if not touch_started and row['action'] == 0:
                touch_started = True
                swipe.append(row)
            elif touch_started and row['action'] == 1:
                # Calculate features and append to gestures
                swipe.append(row)
                if swipe[0]['x'] == swipe[-1]['x'] and swipe[0]['y'] == swipe[-1]['y']:
                    # Discard swipe
                    touch_started = False
                    swipe = []
                    continue
                else:
                    # Calculate swipe features
                    p_point = swipe[0]
                    gesture = {
                        'data': [],
                        't_start': swipe[0]['time'],
                        't_stop': swipe[-1]['time'],
                        'type': 'swipe',
                        'screen': 'None',
                    }
                    for point in swipe:
                        point['x'] = point['x']  / 800 if point['phone_orientation'] == 2 else point['x'] / 480
                        point['y'] = point['y']  / 800 if point['phone_orientation'] == 2 else point['y'] / 480
                        gesture['data'].append({
                            'x0': point['x'],
                            'y0': point['y'],
                            'time': point['time'],
                            'dx': point['x'] - p_point['x'],
                            'dy': point['y'] - p_point['y'],
                            'vx': (point['x'] - p_point['x']) / (point['time'] - p_point['time']) if (point['time'] - p_point['time']) != 0 else 0,
                            'vy': (point['y'] - p_point['y']) / (point['time'] - p_point['time']) if (point['time'] - p_point['time']) != 0 else 0,
                            'moveX': point['x'],
                            'moveY': point['y'],
                            'pressure': point['pressure'],
                            'area': point['area covered'],
                            }
                            )
                        p_point = point
                    user_list[u_index]['devices'][0]['sessions'][session_index]['gestures'].append(gesture)

                    touch_started = False
                    swipe = []
            else:
                swipe.append(row)
    return user_list

def get_user_data(user_id, df, phone_resolutions):
    # df = df[df['actionType'].isin([0,1,2])]
    
    user = {
            'user_id': user_id,
            'devices': [{
                '_id': 0,
                'user_id': user_id,
                'device_id': 0,
                'width': 480,
                'height': 800,
                'sessions': [
                    {'gestures': [],},
                ]
            }],
        }

    touch_started = False
    swipe = []
    for index, row in df.iterrows():
        row['time'] = datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S:%f').timestamp() if row['time'] == row['time'] else 0

        if not touch_started and row['actionType'] == 0:
            touch_started = True
            swipe.append(row)
        elif touch_started and row['actionType'] == 1:
            # Calculate features and append to gestures
            swipe.append(row)
            if swipe[0]['Xvalue'] == swipe[-1]['Xvalue'] and swipe[0]['Yvalue'] == swipe[-1]['Yvalue']:
                # Discard swipe
                touch_started = False
                swipe = []
                continue
            else:
                # Calculate swipe features
                p_point = swipe[0]
                gesture = {
                    'data': [],
                    't_start': swipe[0]['time'],
                    't_stop': swipe[-1]['time'],
                    'type': 'swipe',
                    'screen': 'None',
                }
                for point in swipe:
                    point['Xvalue'] /= phone_resolutions[0]
                    point['Yvalue'] /= phone_resolutions[1]

                    gesture['data'].append({
                        'x0': point['Xvalue'],
                        'y0': point['Yvalue'],
                        'time': point['time'],
                        'dx': point['Xvalue'] - p_point['Xvalue'],
                        'dy': point['Yvalue'] - p_point['Yvalue'],
                        'vx': (point['Xvalue'] - p_point['Xvalue']) / (point['time'] - p_point['time']) if (point['time'] - p_point['time']) != 0 else 0,
                        'vy': (point['Yvalue'] - p_point['Yvalue']) / (point['time'] - p_point['time']) if (point['time'] - p_point['time']) != 0 else 0,
                        'moveX': point['Xvalue'],
                        'moveY': point['Yvalue'],
                        }
                        )
                    user['devices'][0]['sessions'][0]['gestures'].append(gesture)
                    p_point = point

                touch_started = False
                swipe = []
        else:
            swipe.append(row)
    return user

def load_mas(*args):
    phone_resolutions = {
        'Samsung_S6': (1440, 2560),
        'HTC_One': (1080, 1920),
    }

    all_users = []
    for user_id in tqdm(range(1, 117)):
        path = glob(f'gestures_devices_users_games_data/BB-MAS_Dataset/{user_id}/*_HandPhone_TouchEvent_*.csv')[0].replace('\\', '/')
        device_name = path.strip().split('(')[-1].split(')')[0]

        df = pd.read_csv(path)
        data = get_user_data(user_id, df, phone_resolutions[device_name])
        all_users.append(data)

    return all_users