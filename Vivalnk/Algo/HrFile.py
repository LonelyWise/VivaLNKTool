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
#		- Version 1.0.1.0002
#		- Corrected documentation.
#	08/29/2019:
#		- Version 1.0.1.0003
#		- Edited to agree with the Python version.
#		- Corrected version numbers.
#	10/09/2019:
#		- Version 1.0.2.0001
#		- Set HR correction factor to 1 instead of 1.033.
#	01/30/2020:
#		- Version 1.0.3.0001
#		- Implemented heart rate variability.
#	09/25/2020:
#		- Version 1.0.4.0001
#		- Added error codes for HR outside of 40-300 bpm.
#		- Changed initial HR and HRV to -1.
#		- Improved HRV calculation and some internal logic.
#		- Revised variable names and removed unnecessary ones.
#	09/26/2020:
#		- Version 1.0.4.0002
#		- Increased RRI memory to 60.
#	09/26/2020:
#		- Version 1.0.4.0003
#		- Corrected error in raw HR calculation.
#

import numpy as np
import processing

DUMMY_HR = -1				# Dummy HR value.
DUMMY_HRV = -1				# Dummy HRV value.
N_RRI = 60					# Number of R-R intervals to save.
N_RRI_RAW_HR = 10			# Number of R-R intervals to use when calculating raw HR.
N_RAW_HR = 5				# Number of raw HR values to save / use when calculating HR.
N_RRI_HRV = 60				# Number of R-R intervals to use when calculating HRV.
HR_CORRECTION = 1			# Correction factor for under/over-sampled ECG (default: 1).


class HRInstance():
	def __init__(self):
		self.rri = np.zeros(N_RRI)
		for i in range(0, N_RRI):
			self.rri[i] = 0
		self.raw_hr = np.zeros(N_RAW_HR)
		for i in range(0, N_RAW_HR):
			self.raw_hr[i] = 0
		self.n_rri = 0
		self.n_raw_hr = 0
	
	def __destroy__(self):
		del self
	
	def update_rri(self, rri, length):
		counter = 0
		for i in range(0, length):
			if rri[i] != 0:
				counter += 1
		
		if counter > 0:
			self.n_rri = min(N_RRI, self.n_rri + counter)
			
			for i in range(N_RRI-1, counter-1, -1):
				self.rri[i] = self.rri[i-counter]
			for i in range(counter-1, -1, -1):
				self.rri[i] = rri[counter-i-1]
	
	def update_raw_hr(self, raw_hr):
		self.n_raw_hr = min(N_RAW_HR, self.n_raw_hr + 1)
		
		for i in range(N_RAW_HR-1, 0, -1):
			self.raw_hr[i] = self.raw_hr[i-1]
		self.raw_hr[0] = raw_hr

class HRResult():
	def __init__(self, hr, hrv, code):
		self.hr = hr		# Heart rate (in beats per minute).
		self.hrv = hrv		# Heart rate variability (in milliseconds).
		self.code = code	# Error code (2-bit binary string):
							#	Bit 1:  HR < 40 bpm
							#	Bit 2:  HR > 300 bpm


def detect_hr(rri, length, instance):
	"""
	Calculates heart rate and heart rate variability from an array of RR intervals.
	
	Parameters
		rri:				An array of RR intervals (in ms).
		length:				Number of elements in the rri array.
		instance:			A struct containing instance variables.
		result:             A pointer to an hr_result struct (C VERSION ONLY).
	Returns
		An HRResult object (Python version only).
	"""
	
	instance.update_rri(rri, length)
	
	raw_hr = DUMMY_HR
	hr = DUMMY_HR
	hrv = DUMMY_HRV
	if instance.n_rri > 0:
		# Calculate raw HR based on the median RR interval.
		raw_hr = 60.0 * 1000.0 / processing.median_array(instance.rri, min(instance.n_rri, N_RRI_RAW_HR))
		instance.update_raw_hr(raw_hr)
		
		# Calculate HR as the mean of the most recent raw HR values.
		hr = int(processing.mean_array(instance.raw_hr, instance.n_raw_hr) / HR_CORRECTION)
		
		# Calculate HRV using the RMSSD formula.
		hrv = int(processing.std_array(instance.rri, min(instance.n_rri, N_RRI_HRV)) / HR_CORRECTION)
	
	code = [0, 0]
	code[0] = 1 if hr < 40 else 0
	code[1] = 1 if hr > 300 else 0
	
	return HRResult(hr, hrv, code)
