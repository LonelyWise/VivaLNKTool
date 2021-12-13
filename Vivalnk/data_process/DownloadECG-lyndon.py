#!/usr/bin/env python 
# coding:utf-8

import argparse
import http.client
import json
import os.path
import sys
import zlib
import numpy as np
import matplotlib.pyplot as plt
import pyhrv.nonlinear as nl
import time
import datetime
import requests

from matplotlib import ticker
from scipy.signal import butter, filtfilt
import pyhrv.tools as tools
import pyhrv
import pyhrv.time_domain as td
import pyhrv.frequency_domain as fd

# curl -X GET --header 'Accept: application/json'
# 'http://310test-webapp.ap-northeast-1.elasticbeanstalk.com/api/data/full_ecg?sensorId=ECGRec_20148%2FC600101&start=1563325200000&end=1563335940000'

USE_RELEASE_SERVER = True
ENABLE_GZIP = False
ENABLE_ECG_ACC = True
MAX_DURATION = 1000*3600 # 1 hour
BASE_URL = "310test-webapp.ap-northeast-1.elasticbeanstalk.com"
if USE_RELEASE_SERVER:
    BASE_URL = "cardiac.vivalnk.com"
    ENABLE_GZIP = False
    print("Using release server")

URL_HEADER = {
    "accessKey": "s8DhdWmwUt",
    "secretKey": "psttZOf3UwBr3jdH"
}

CACHE_DIR = "/Users/xuwei/Documents/数据分析文档/FW2的数据分析/数据丢失/VVLogs"
TIME_ZONE = np.timedelta64(8, "h")
ECG_HZ = 128


SDNN_DURATION = 300
ACTIVITY_WINDOW = 5*10 # 10 seconds
ACC_HZ = 5
ACTIVITY_SCALE = 50


# https://www.kubios.com/about-hrv/
# The Baevsky’s stress index (SI)
#
def stress_score(rri):
    rri = np.array(rri)
    std_rri = np.std(rri)
    mean_rri = np.mean(rri)
    THRESHOLD = 2.5
    BIN_SIZE = 50
    FACTOR = 10

    # bin of 50 ms
    new_rri = [int(i/BIN_SIZE) for i in rri if (mean_rri - THRESHOLD*std_rri) < i < (mean_rri + THRESHOLD*std_rri)]
    if len(new_rri) < 60:
        return 0
    # if len(new_rri) < (len(rri) - 1):
    #     print("more than 1 RRI removed")

    N = len(new_rri)
    rr_dist = np.bincount(new_rri)
    mo_index = np.argmax(rr_dist)
    n = rr_dist[mo_index]
    Mo = mo_index*BIN_SIZE/1000

    MxDMn = len([i for i in rr_dist if i != 0])*BIN_SIZE/1000
    AMo = n/N

    SI = AMo/(2*Mo*MxDMn)

    return SI*FACTOR


def extract_feature_python(x, y, z, width=50, Wn=[0.1,0.9]):
    # Center each axis and calculate the total acceleration.
    total = np.sqrt((x - np.mean(x)) ** 2 + (y - np.mean(y)) ** 2 + (z - np.mean(z)) ** 2)

    # Filter the total acceleration.
    b, a = butter(2, Wn, btype="bandpass")
    total = filtfilt(b, a, total)

    feature = np.std(total)

    if feature > 1000:
        return 4
    elif feature > 400:
        return 3
    elif feature > 65:
        return 2
    elif feature > 0:
        return 1
    return 0


def download_single(sn, start, end, force):
    snId = sn
    sn = sn.replace("/", "%2F")

    file_name = os.path.join(CACHE_DIR, f"{sn}_{start}_{end}")

    if not force:
        if os.path.exists(file_name):
            print(f"{file_name} exists, skip downloading")
            with open(file_name) as input:
                return json.load(input)

    try:
        # dec = zlib.decompressobj(16+zlib.MAX_WBITS)
        # if USE_RELEASE_SERVER:
        #     conn = http.client.HTTPSConnection(BASE_URL)
        # else:
        #     conn = http.client.HTTPConnection(BASE_URL, 80)
        #
        # url = f"/api/data/full_ecg?sensorId={sn}&start={start}&end={end}"
        # if ENABLE_GZIP:
        #     url = f"/api/data/full_ecg2?sensorId={sn}&start={start}&end={end}"
        start_time = time.time()
        # conn.request("GET", url, headers=URL_HEADER)
        # response = conn.getresponse()
        # if ENABLE_GZIP:
        #     result = response.read()
        #     result = dec.decompress(result)
        #     result = result.decode("UTF-8")
        # else:
        #     result = response.read().decode("UTF-8")
        # response.close()
        query_param_dict = {
            "sensorId": snId,
            "start": start,
            # start_millis to end_millis is a closed interval
            "end": end,
        }
        headers_dict = {
            "accessKey": "sejefpnsddsn",
            "secretKey": "psttZOf3UwBr3jdH"
        }
        base_url = "https://cardiac.vivalnk.com/api/data/full_ecg"
        start = time.time()
        response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
        print(f"elapsed time: {time.time() - start_time:.0f} seconds to fetch: {base_url}")
        result = response.content
        try:
            json_data = json.loads(result)
            if json_data["code"] != 200:
                print("failed:", json_data["code"], json_data["message"])
                return None
        except Exception as e:
            print("failed to load json string")
            print(e)
            print(result)

        data_part = json_data["data"]

        print(file_name)
        print(len(data_part))

        with open(file_name, "w") as output:
            json.dump(data_part, output)
            output.close()

    except Exception as e:
        print(e)

    return data_part


#download_single("ECGRec_201902%2FC500021", 1563275293000, 1563275333000)


def download(sn, start, end, force=False):

    time_slice = []
    it = start
    while it < end:
        new_end = it + MAX_DURATION - 1
        if end <= new_end:
            time_slice.append((it, end))
            break
        else:
            time_slice.append((it, new_end))
            it = new_end+1
    all_data = []
    for i in time_slice:
        data_part = download_single(sn, i[0], i[1], force)
        if data_part is not None:
            all_data += data_part

    if len(all_data) == 0:
        print("no data is downloaded")

    all_data.sort(key=lambda f: f["recordTime"])
    print(len(all_data))
    missing_tick = []
    if True:
        missing = int((end - start)/1000 - len(all_data))
        print(f"totally {missing} seconds missing")
        for i in range(len(all_data)-1):
            end_tick = all_data[i+1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            start_str = datetime.datetime.fromtimestamp(start_tick/1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(end_tick/1000).strftime('%Y-%m-%d %H:%M:%S')

            if abs(delta) < 500:
                print(f"duplicated from {start_str} to {end_str}")

            if delta > 1100:
                print(f"part one: missing from {start_str} to {end_str}, count: {delta/1000-1:.0f}")
                missing_tick += [(start_tick, end_tick)]

    return all_data, missing_tick


def get_stress(hr, rmssd):
    return int(rmssd/hr*100)


def gen_hrv(rri, duration=300):
    segments, control = tools.segmentation(nni=rri, duration=duration)
    sdnns = []
    rmssd = []
    stress = []

    for seg in segments:
        sdnns.append(td.sdnn(seg)["sdnn"])
        rmssd.append(td.rmssd(seg)["rmssd"])
        stress.append(stress_score(seg))

    return sdnns, rmssd, stress


def time_domain_report(nni):
    # Time Domain results
    print("=========================")
    print("TIME DOMAIN Results")
    print("=========================")

    hr_ = td.hr_parameters(nni)
    print("HR Results")
    print("> Mean HR:			%f [bpm]" % hr_['hr_mean'])
    print("> Min HR:			%f [bpm]" % hr_['hr_min'])
    print("> Max HR:			%f [bpm]" % hr_['hr_max'])
    print("> Std. Dev. HR:		%f [bpm]" % hr_['hr_std'])

    nni_para_ = td.nni_parameters(nni)
    print("NN Results")
    print("> Mean NN:			%f [ms]" % nni_para_['nni_mean'])
    print("> Min NN:			%f [ms]" % nni_para_['nni_min'])
    print("> Max NN:			%f [ms]" % nni_para_['nni_max'])

    nni_diff_ = td.nni_differences_parameters(nni)
    print("∆NN Results")
    print("> Mean ∆NN:			%f [ms]" % nni_diff_['nni_diff_mean'])
    print("> Min ∆NN:			%f [ms]" % nni_diff_['nni_diff_min'])
    print("> Max ∆NN:			%f [ms]" % nni_diff_['nni_diff_max'])

    print("SDNN:				%f [ms]" % td.sdnn(nni)['sdnn'])
    print("SDNN Index:			%f [ms]" % td.sdnn_index(nni)['sdnn_index'])
    print("SDANN:				%f [ms]" % td.sdann(nni)['sdann'])
    print("RMMSD:				%f [ms]" % td.rmssd(nni)['rmssd'])
    print("SDSD:				%f [ms]" % td.sdsd(nni)['sdsd'])
    print("NN50:				%i [-]" % td.nn50(nni)['nn50'])
    print("pNN50: 				%f [%%]" % td.nn50(nni)['pnn50'])
    print("NN20:				%i [-]" % td.nn20(nni)['nn20'])
    print("pNN20: 				%f [%%]" % td.nn20(nni)['pnn20'])


def date_str2unix_time(date_str):
    epoch = time.mktime(datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").timetuple())
    return int(epoch * 1000)


def remove_baseline_wander(y):
    fs = ECG_HZ
    high_pass = 1.28 # hz
    nyq = 0.5 * fs
    high = high_pass / nyq

    b, a = butter(2, 0.02, 'high')
    return filtfilt(b, a, y)


def remove_power(y):
    fs = ECG_HZ
    nyq = 0.5 * fs
    low = 32 / nyq

    b, a = butter(2, low, 'low')
    return filtfilt(b, a, y)



if __name__ == "__main__":
    # eg:--sn=ECGRec_201913/C600018 --begin=2020-3-05T11:00:00 --end=2020-3-05T11:10:00 --force
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sn", help="LOT/SN number, see patch back, started with ECGRec, for example, ECGRec_201902/C500021")
    parser.add_argument("--begin", help="begin Epoch time in milli-seconds")
    parser.add_argument("--end", help="end Epoch time in milli-seconds")
    parser.add_argument("--force", action="store_true", help="skip cache, force downloading")

    parser.add_argument('rest', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.sn is None:
        parser.print_help()
        sys.exit(1)
    else:
        if "ECGRec_" not in args.sn:
            print("LOT/SN number must start with ECGRec_")
            parser.print_help()
            sys.exit(1)

    if ":" in args.begin:
        begin_time = date_str2unix_time(args.begin)
        end_time = date_str2unix_time(args.end)
    else:
        begin_time = int(args.begin)
        end_time = int(args.end)

    if ENABLE_GZIP:
        print("gzip enabled")

    all_data, missing_tick = download(args.sn, begin_time, end_time, args.force)

    first_data_time = all_data[0]['recordTime']
    last_data_time = all_data[len(all_data)-1]['recordTime']
    first_format = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(first_data_time/1000))
    last_format = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(last_data_time/1000))
    print(f'第一条数据时间点:'+first_format)
    print(f'最后一条数据时间:'+last_format)


    # preprocess ACC
    acc_time = []
    acc_x = []
    for index in range(len(all_data)):
        i = all_data[index]
        acc_hz = len(i["acc"])
        acc_cycle = 1000 / acc_hz
        for index2 in range(acc_hz):
            j = i["acc"][index2]
            acc_x.append(j[0])
            acc_time.append(
                np.datetime64(i["recordTime"], "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))

    acc_y = []
    for i in all_data:
        for j in i["acc"]:
            acc_y.append(j[1])

    acc_z = []
    for i in all_data:
        for j in i["acc"]:
            acc_z.append(j[2])
    acc_x = np.array(acc_x)
    acc_y = np.array(acc_y)
    acc_z = np.array(acc_z)


    # preprocess HR
    hr_x = np.array([np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data])
    hr_y = [i["hr"] for i in all_data]

    if len(all_data) == 0:
        print("no data")
        sys.exit(0)
    if len(all_data[0]["ecg"]) != ECG_HZ:
        print("wrong ECG_HZ value")
        sys.exit(0)


    lead_off_count = 0
    lead_off_time = []
    for i in all_data:
        if i["leadOn"] != 1:
            lead_off_count += 1
            time = np.datetime64(i["recordTime"], "ms") + TIME_ZONE
            lead_off_time.append(time)

    print(f"lead off count = {lead_off_count}")
    flash_count = 0
    for i in all_data:
        if i["flash"] == 1:
            flash_count += 1
    print(f"flash% = {int(flash_count*100/len(all_data))}%")

    if ENABLE_ECG_ACC:
        raw_ecg_x = [np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data]
        raw_ecg_y = [i["ecg"] for i in all_data]
        rwl_x = []
        rwl_y = []
        ecg_x = []
        ecg_y = []
        for i in range(len(raw_ecg_x)):
            if len(raw_ecg_y[i]) != ECG_HZ:
                print("wrong ECG length found, padding with zero")
                raw_ecg_y[i] = [0]*ECG_HZ

            for j in range(ECG_HZ):
                raw_x = raw_ecg_x[i] + np.timedelta64(int(j*1000/ECG_HZ), "ms")
                raw_y = raw_ecg_y[i][j]
                ecg_x.append(raw_x)
                ecg_y.append(raw_y)
        for i in all_data:
            for j in i["rwl"]:
                if 0 <= j < ECG_HZ:
                    time = np.datetime64(i["recordTime"], "ms") + TIME_ZONE
                    time += np.timedelta64(int(j*1000/ECG_HZ), "ms")
                    rwl_x.append(time)
                    if len(i["ecg"]) != ECG_HZ:
                        pass
                    else:
                        rwl_y.append(i["ecg"][j])
                else:
                    break

    else:
        all_rri = []
        for i in all_data:
            all_rri += [j for j in i["rri"] if 0 < j < 3000]

        activity_feature = []
        x_activity_feature = []
        for index in range(int(len(acc_x)/ACTIVITY_WINDOW)):
            feature = extract_feature_python(acc_x[index*ACTIVITY_WINDOW:(index+1)*ACTIVITY_WINDOW],
                                             acc_y[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                             acc_z[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW], ACTIVITY_WINDOW)
            activity_feature.append(feature*ACTIVITY_SCALE)
            index = int(index*(ACTIVITY_WINDOW/ACC_HZ))
            x_activity_feature.append(hr_x[np.clip(index, 0, len(hr_x)-1)])

    if ENABLE_ECG_ACC:
        ax = plt.subplot(211)
        plt.title("HR")
        plt.ylim(-10, 180)
        ax.set_yticks(np.arange(0, 180, 20))
        plt.grid()
        plt.plot(hr_x, hr_y)
        plt.axhline(80, linestyle="--", color="red")
        plt.axhline(120, linestyle="--", color="red")
        plt.axhline(160, linestyle="--", color="red")

        ax2 = plt.subplot(212, sharex=ax)

        plt.ylim(-5000, 5000)

        new_ecg_y = np.array(ecg_y)
        if False:
            plt.title("Filtered ECG")
            new_ecg_y = remove_baseline_wander(ecg_y)
            new_ecg_y = remove_power(new_ecg_y)
            plt.plot(ecg_x, new_ecg_y)
        else:
            plt.title("Raw ECG")
            magnification = 1000
            if ECG_HZ == 250:
                magnification = 3776
            formatter = ticker.FuncFormatter(lambda x, y : f"{x/magnification:.3}mV")
            ax2.yaxis.set_major_formatter(formatter)

            plt.plot(ecg_x, new_ecg_y)
            plt.scatter(rwl_x, rwl_y, color="red", marker="x")
            plt.scatter(lead_off_time, [0]*len(lead_off_time), color="red", marker="o")


        for i in missing_tick:
            begin = np.datetime64(i[0], "ms") + TIME_ZONE
            end = np.datetime64(i[1], "ms") + TIME_ZONE
            plt.axvspan(begin, end, facecolor='red', alpha=0.5)

        color = "red"
        ax22 = ax2.twinx()
        ax22.set_ylabel('acc', color=color)
        ax22.tick_params(axis='y', labelcolor=color)

        ax22.plot(acc_time, acc_x, label="ACC(x)")
        ax22.plot(acc_time, acc_y, label="ACC(y)")
        ax22.plot(acc_time, acc_z, label="ACC(z)")
        ax22.set_ylim(-4096, 14000)
        plt.legend()
        plt.show()


    else:
        plt.ylim(-10, 160)
        plt.plot(hr_x, hr_y)
        plt.axhline(80, linestyle="--", label="80")
        sdnn, rmssd, stress = gen_hrv(all_rri, SDNN_DURATION)
        plt.plot(hr_x[[SDNN_DURATION * i for i in range(len(sdnn))]], stress)
        plt.scatter(x_activity_feature, activity_feature, color='purple')
        nl.poincare(all_rri)
        fd.welch_psd(all_rri)

