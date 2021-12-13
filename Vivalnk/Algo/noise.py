#
#	=================
#	=  CHANGE LOG   =
#	= Troy P. Kling =
#	=================
#	
#	08/22/2019:
#		- Version 1.0.1.0001
#		- Initial release.
#	08/27/2019:
#		- Version 1.0.2.0001
#		- Corrected a floating point arithmetic error in the high-frequency noise detector.
#	08/29/2019:
#		- Version 1.0.2.0002
#		- Edited to agree with the Python version.
#		- Corrected version numbers.
#	09/25/2020:
#		- Version 1.0.3.0001
#		- Lowered INIT_AMP to 1.
#		- Changed the saturation return value to a percentage.
#		- Simplified some code.
#

import numpy as np
import processing

MAX_MV = 8.6				# The maximum value the ECG signal can have, in millivolts (absolute value).
INIT_AMP = 1.0				# The assumed initial amplitude of the subject's QRS complexes.


class NoiseInstance():
	def __init__(self):
		self.prev_amp = INIT_AMP
	
	def __destroy__(self):
		del self

class NoiseResult():
	def __init__(self, saturation, high_noise, low_noise, code):
		self.saturation = saturation		# The percentage of samples outside of the measurement range.
		self.high_noise = high_noise		# The estimated signal-to-noise ratio of the ECG signal.
		self.low_noise = low_noise			# The amount of baseline wander in the ECG signal.
		self.code = code					# A success/error code.
											#	0: Success
											#	1: Failure


def detect_noise(ecg, length, fs, magnification, instance):
	"""
	Quantifies noise in an ECG signal.
	
	Parameters
		ecg:				An array containing three seconds of ECG data.
		length:				Number of elements in the ecg array (should be equal to 3*fs).
		fs:					Sampling rate of the signal (in Hertz).
		magnification:		Conversion factor to convert from raw sensor data to mV.
		instance:			A struct containing instance variables.
		result:				A pointer to a noise_result struct (C VERSION ONLY).
	Returns
		A NoiseResult object (Python version only).
	"""
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Pre-Processing
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Hard-code some parameter values.
	width = 7
	degree = 3
	kernel = np.array([-0.07058824, -0.01176471,  0.03800905,  0.07873303,  0.11040724, 
						0.13303167,  0.14660633,  0.15113122,  0.14660633,  0.13303167, 
						0.11040724,  0.07873303,  0.03800905, -0.01176471, -0.07058824])
	
	# Apply a Savitzky-Golay filter to the signal.
	savgol = processing.savgol_filter(ecg, length, kernel, width)
	
	# Subtract the filtered signal from the raw signal.
	diff = np.zeros(fs)
	for i in range(0, fs):
		diff[i] = ecg[i+fs] - savgol[i+fs]
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Saturation Detector
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Count the number of samples above or below the saturation threshold.
	saturation = 0.0
	max_amp = magnification * MAX_MV
	for i in range(fs, 2*fs):
		if np.abs(ecg[i]) >= max_amp:
			saturation += 1.0
	saturation /= fs
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	High-Frequency Noise Detector
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Hard-code some parameter values.
	n = 3
	half_window = int(0.075*fs)
	
	# Mask the n largest peaks.
	mask = np.zeros(fs)
	for i in range(0, fs):
		mask[i] = 0
	temp = 0
	for i in range(0, n):
		# Find the index of the highest/lowest peak in the difference signal.
		idx = 0
		val = 0
		for j in range(0, fs):
			if mask[j] == 0:
				temp = np.abs(diff[j])
				if temp > val:
					idx = j
					val = temp
		
		# Mask a region around the highest peak.
		for j in range(max(0, idx-half_window), min(fs, idx+half_window+1)):
			mask[j] = 1
	
	# Calculate the largest amplitude difference in the masked regions.
	abs_idx = 0
	abs_val = 0
	for i in range(0, fs):
		if mask[i] == 1:
			temp = np.abs(diff[i])
			if temp > abs_val:
				abs_idx = i
				abs_val = temp
	min_val = abs_val
	max_val = -abs_val
	for i in range(max(0, abs_idx-half_window), min(fs, abs_idx+half_window+1)):
		temp = diff[i]
		if temp < min_val:
			min_val = temp
		if temp > max_val:
			max_val = temp
	
	# Update the amplitude.
	curr_amp = (max_val - min_val) / magnification
	amp = 0.95 * instance.prev_amp + 0.05 * curr_amp
	instance.prev_amp = amp
	
	# Calculate the mean of the non-masked difference signal.
	mean = 0
	counter = 0
	for i in range(0, fs):
		if mask[i] == 0:
			mean += diff[i]
			counter += 1
	if counter > 0:
		mean = mean / counter
	
	# Calculate the standard deviation of the non-masked difference signal.
	dev = 0
	std = 0
	counter = 0
	for i in range(0, fs):
		if mask[i] == 0:
			dev = diff[i] - mean
			std += dev * dev
			counter += 1
	if counter > 0:
		std = np.sqrt(std / counter) / magnification
	
	# Calculate the signal-to-noise ratio.
	high_noise = np.log10(amp / max(std, 0.001))
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Low-Frequency Noise Detector
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Find the area under the Savitzky-Golay filtered signal.
	low_noise = 0
	for i in range(0, fs):
		low_noise += np.abs(savgol[i+fs])
	low_noise = low_noise / (fs * magnification)
	
	code = [0]
	
	return NoiseResult(saturation, high_noise, low_noise, code)
