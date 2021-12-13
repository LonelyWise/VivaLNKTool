import numpy as np
from scipy import signal, ndimage
from collections import defaultdict


class ActivityInstance():
    def __init__(self):
        self.temp = 0

    def __destroy__(self):
        del self

class ActivityResult():
    def __init__(self, max_activity, all_activities, code):
        self.max_activity = max_activity
        self.all_activities = all_activities
        self.code = code

def get_activities(diff, cal_amp, win_len, buffer):
    i_start = 0
    labels = []
    for i_end in range(win_len, len(diff), win_len):
        # Get average difference over sliding window
        avg_diff = np.mean(diff[i_start:i_end])
        if avg_diff >= (cal_amp+0.33):
            labels.append('high_activity')
        elif avg_diff < (cal_amp+0.33) and avg_diff >=(cal_amp+buffer):
            labels.append('low_activity')
        else:
            labels.append('no_activity')
        i_start+=win_len
        
    # Get most frequent label
    freq = defaultdict(int)
    for label in labels:
        freq[label]+=1
    max_label = max(freq, key=freq.get)
    return max_label, labels

def get_diff(sig, FS_ACC):
    # Calculate min and max envelopes for ACC amplitude
    upper = ndimage.maximum_filter1d(sig, size=int(2*FS_ACC))
    lower = -ndimage.maximum_filter1d(-sig, size=int(2*FS_ACC))
    diff = upper - lower
    return diff

def detect_activity(sig, cal, FS_ACC, instance, buffer=0.02, win_len=100):
    '''
    :param sig:  Combined x,y,z accelerometer signal
    :param cal:  Combined x,y,z accelerometer calibration signal
    :param FS_ACC: Sampling rate of accelerometer signal
    :param instance: ActivityInstance()
    :param buffer: Buffer to add to calibration amplitude
    :param win_len: Window length for sliding activity detection
    :return: ActivityResult() object containing the max activity and all activities in signal
    '''

    pca = np.array(sig)
    pca_cal = np.array(cal)
        
    # Calculate calibration diff
    cal_amp = np.median(get_diff(pca_cal, FS_ACC))
    
    # Calculate signal diff
    diff = get_diff(pca, FS_ACC)
    
    # Get the most common activity
    activity = get_activities(diff, cal_amp, win_len, buffer)
    
    # Troy Activity
    #std_x = processing.std_array(x, length) / acc_accuracy
    #std_y = processing.std_array(y, length) / acc_accuracy
    #std_z = processing.std_array(z, length) / acc_accuracy
    #activity = (std_x + std_y + std_z) / 3.0

    return ActivityResult(activity[0], activity[1], 0)
