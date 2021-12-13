#!/usr/bin/env python 
# coding:utf-8
import biosppy
import numpy as np
import pyhrv.tools as tools
import pyhrv
import pyhrv.time_domain as td
import pyhrv.frequency_domain as fd
from opensignalsreader import OpenSignalsReader

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


def gen_hrv(rri, duration=300):
    segments = tools.tachogram(nni=rri)

    sdnn = td.sdnn(rri)["sdnn"]
    rmssd = td.rmssd(rri)["rmssd"]

    print('SDNN = ' + str(sdnn))
    print('RMSSD = ' + str(rmssd))


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

if __name__ == "__main__":
    rri = [800,789,797,819,858,828,789,781,794,828,825,833,828,822,800,775,797,811,858,847,811,794,789,797,811,825,850,847,808,769,800,803,814,836,819,828,797,781,778,817]
    # gen_hrv(rri,300)
    #
    # Load ECG data
    signal = OpenSignalsReader('/Users/xuwei/Desktop/SampleECG.txt').signal('ECG')
    print(signal)

    rpeaks = biosppy.signals.ecg.ecg(signal)[2]
    # Plot ECG
    tools.plot_ecg(signal)
    tools.hr_heatplot(signal=signal)
    # time_domain_report(rri)
    #
    # #- VLF:	0.00Hz to 0.04Hz
    # #- LF: 	0.04Hz to 0.15Hz
    # #- HF: 	0.15Hz to 0.40Hz
    # result = fd.lomb_psd(nni=rri)
    # print(result['lomb_peak'])
    #
    # results = pyhrv.hrv(nni=rri)
    # # Create HRV Report
    # pyhrv.tools.hrv_export(results, efile='SampleReport', path='/Users/xuwei/Desktop/产品调整图2PNG')

    # nni = np.load('series_1.npy')

    # Compute HRV results
    # results = pyhrv.hrv(nni=rri)
    #
    # # Export HRV results
    # tools.hrv_export(results, efile='SampleExport', path='/my/favorite/path/')