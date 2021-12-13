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
#		- Corrected floating point arithmetic errors in the M, F, and R calculators.
#		- Fixed a seg fault due to a for loop typo in the noisy QRS detector.
#	08/29/2019:
#		- Version 1.0.3.0001
#		- Corrected floating point arithmetic errors in the QRS detector.
#		- Edited to agree with the Python version.
#		- Corrected version numbers.
#	09/12/2019:
#		- Version 1.0.4.0001
#		- Implemented backsearch for peaks under the threshold.
#		- Fixed misaligned peak detections at packet boundaries.
#		- Enforced predictive R wave detection during high-frequency noise.
#		- Tweaked some parameters for improved R peak detection.
#		- Turned off post-detection fast-forwarding.
#	09/16/2019:
#		- Version 1.0.5.0001
#		- Fixed peak mis-alignment in learning phase.
#	01/21/2020:
#		- Version 1.0.6.0001
#		- Fixed peak correction.
#		- Added more comprehensive documentation.
#	05/24/2020:
#		- Version 1.0.7.0001
#		- Implemented more advanced peak detection.
#		- Inverted QRS complexes can now be detected and accurately tracked.
#		- Updated documentation.
#	09/25/2020:
#		- Version 1.0.8.0001
#		- Reverted Lyndon's change which prevented preemptivwe QRS detection.
#		- Added a lower bound to new additions to the M array.
#		- Implemented an error code if 10+ seconds elapse without a detected heartbeat.
#	09/28/2020:
#		- Version 1.0.9.0001
#		- Added a lower bound for the MFR threshold to limit heartbeat detections during asystole.
#		- Decreased several noise thresholds to prevent high HR from being interpreted as noise.
#		- Prevented the algorithm from resetting while in the learning phase.
#		- Lowered the minimum RR interval length from 200 to 180 ms.
#	10/14/2020
#		- Version 1.0.10.0001
#		- Set high frequency noise threshold to 0 to detect high heartrates and tachycardia
#
#   Brittany M. Bowers
#   05/10/2021
#       - Version 1.0.11.001
#       - Changed THRESHOLD_NOISE to 1.1 to detect noise sooner
#       - Added "if clean" to save_peak function to only store M-Thresh if signal is clean
#       - Added logic to detect_qrs_noisy to recenter and expand the search window if a low amp peak is detected
#
#  TODO: Make sure output rri is clean (not too large for ex)
#  TODO: Check whether each peak is inverted for plotting purposes

import numpy as np
import matplotlib.pyplot as plt
import processing

FS_ECG = 128				# Sampling rate of the ECG sensor (mV).
N_SAVE = 5					# Maximum number of heartbeats per second.
N_PEAKS = 5					# Number of peaks to consider for the M and R thresholds.
N_RRI = 10					# Number of R-R intervals to use for HR-based calculations.
WIDTH_SEARCH = 0.15			# The search width for finding peaks (in milliseconds).
THRESHOLD_NOISE = 1.1		# Threshold for the high_noise result of detect_noise(). ## ORIGINAL 1.0
THRESHOLD_INVERSION = -1.2	# Threshold for inverted peaks to be detected.
SECONDS_LEARN = 5			# Number of seconds to calculate parameters when in learning phase.
SECONDS_NOISE = 5			# Number of seconds to prolong the high-frequency noise trigger.
SECONDS_NOBEATS = 3			# Number of seconds without a detected QRS complex to trigger reset.
SECONDS_INVERSION = 5		# Number of seconds for peak inversion to be toggled.
FACTOR_MFR = 1				# Scale factor for raising/lower the MFR threshold (default: 1).
FACTOR_F = 150				# Scale factor for the F threshold (default: 150).
DUMMY_RWL = -1				# Dummy value for entries in the RWL array.
DUMMY_RRI = 0				# Dummy value for entries in the RRI array.
DUMMY_PEAK = 1000			# Dummy value for peak detection.


class QRSInstance():
	def __init__(self):
		self.learn_flag = SECONDS_LEARN
		self.noise_flag = 0
		self.prev_rwl = DUMMY_PEAK
		self.max_m = 0
		self.m_arr = np.zeros(N_PEAKS)
		for i in range(0, N_PEAKS):
			self.m_arr[i] = 0
		self.r_arr = np.zeros(N_PEAKS)
		for i in range(0, N_PEAKS):
			self.r_arr[i] = 0
		self.nobeat_counter = 0
		self.clean_rri = np.zeros(N_RRI)
		for i in range(0, N_RRI):
			self.clean_rri[i] = 0
		self.n_rri = 0
		self.rwl_counter = 0
		self.rri_counter = 0
		self.rwl = np.zeros(N_SAVE)
		self.rri = np.zeros(N_SAVE)
		for i in range(0, N_SAVE):
			self.rwl[i] = DUMMY_RWL
			self.rri[i] = DUMMY_RRI
		self.next_peak = DUMMY_PEAK
		self.i = FS_ECG
		self.inverted = False
		self.inverted_timer = 0
		self.peak_arr = np.zeros(N_PEAKS)
		self.trough_arr = np.zeros(N_PEAKS)
		for i in range(0, N_PEAKS):
			self.peak_arr[i] = DUMMY_PEAK
			self.trough_arr[i] = DUMMY_PEAK
		self.peak_count = 0
		self.trough_count = 0
		self.max_fdai = np.zeros(N_PEAKS)
		for i in range(0, N_PEAKS):
			self.max_fdai[i] = 0
	
	def __destroy__(self):
		del self
	
	def reset(self):
		self.learn_flag = SECONDS_LEARN
		self.prev_rwl = DUMMY_PEAK
		self.max_m = 0
		self.m_arr = np.zeros(N_PEAKS)
		for i in range(N_PEAKS):
			self.m_arr[i] = 0
		self.r_arr = np.zeros(N_PEAKS)
		for i in range(N_PEAKS):
			self.r_arr[i] = 0
		self.rwl_counter = 0
		self.rri_counter = 0
		for i in range(0, N_SAVE):
			self.rwl[i] = DUMMY_RWL
			self.rri[i] = DUMMY_RRI
		self.next_peak = DUMMY_PEAK
		self.i = FS_ECG
		self.inverted_timer = 0
		for i in range(0, N_PEAKS):
			self.peak_arr[i] = DUMMY_PEAK
			self.trough_arr[i] = DUMMY_PEAK
		self.peak_count = 0
		self.trough_count = 0
		for i in range(0, N_PEAKS):
			self.max_fdai[i] = 0

# TODO: Remove non-essential variables!
class QRSResult():
	def __init__(self, rwl, rri, code, fdai, m_thresh, f_thresh, r_thresh, noise, res, learn):
		self.rwl = rwl				# An array of R wave locations (based on indices of the current packet).
		self.rri = rri				# An array of R-R intervals (measured in milliseconds).
		self.code = code			# Error code (1-bit binary string):
									#	Bit 1:  No detected heartbeats for 10+ seconds.
		self.fdai = fdai			# Non-essential -- for debugging only.
		self.m_thresh = m_thresh	# Non-essential -- for debugging only.
		self.f_thresh = f_thresh	# Non-essential -- for debugging only.
		self.r_thresh = r_thresh	# Non-essential -- for debugging only.
		self.noise = noise			# Non-essential -- for debugging only.
		self.res = res				# Non-essential -- for debugging only.
		self.learn = learn			# Non-essential -- for debugging only.


def calculate_m(i, fs, instance):
	t = (i - instance.prev_rwl) / fs * 1000
	
	m_avg = processing.mean_array(instance.m_arr, N_PEAKS)
	if t < 200:
		return m_avg
	elif t < 1200:
		return -0.4 * m_avg / 1000 * (t - 200) + m_avg
	else:
		return 0.6 * m_avg

def calculate_f(i, fs, fdai, instance):
	# Find the maximum value between 350 and 300 milliseconds ago.
	max_early = 0
	for j in range(i-int(0.35*fs), i-int(0.3*fs)+1):
		if fdai[j] > max_early:
			max_early = fdai[j]
	
	# Find the maximum value between now and 50 milliseconds ago.
	max_late = 0
	for j in range(i-int(0.05*fs), i+1):
		if fdai[j] > max_late:
			max_late = fdai[j]
	
	# Calculate the mean FDAI over the last 350 milliseconds.
	mean = 0
	counter = 0
	for j in range(max(0, i-int(0.35*fs)), min(3*fs, i+1)):
		mean += fdai[j]
		counter += 1
	mean /= counter
	
	# Update the F threshold.
	f_thresh = mean/2.0 + (max_late - max_early) / FACTOR_F
	
	return f_thresh

def calculate_r(i, fs, instance):
	t = (i - instance.prev_rwl) / fs * 1000
	
	m_avg = processing.mean_array(instance.m_arr, N_PEAKS)
	r_avg = processing.mean_array(instance.clean_rri, instance.n_rri) / fs * 1000
	if t < 2.0/3.0*r_avg:
		return 0
	elif t < r_avg:
		return -0.4 * m_avg / 1000 / 1.4 * (t - 2.0/3.0*r_avg)
	else:
		return -0.4 * m_avg / 1000 / 1.4 * (1.0/3.0*r_avg)

def correct_peak(ecg, i, length, fs, width, update_inversion, instance):
	peak_idx = i
	peak_val = ecg[i]
	peak_avg = 0
	trough_idx = i
	trough_val = ecg[i]
	trough_avg = 0
	
	if update_inversion:
		# Find the absolute min and max within a small window.
		for j in range(max(fs,i-int(width*fs)), min(length,i+int(width*fs)+1)):
			if ecg[j] > peak_val:
				peak_idx = j
				peak_val = ecg[j]
			elif ecg[j] < trough_val:
				trough_idx = j
				trough_val = ecg[j]
		
		if instance.peak_count < N_PEAKS:
		    instance.peak_count += 1
		    instance.trough_count += 1
		else:
		    instance.peak_count = N_PEAKS
		    instance.trough_count = N_PEAKS
		
		# Update the peak/trough memory.
		for i in range(N_PEAKS-1, 0, -1):
			instance.peak_arr[i] = instance.peak_arr[i-1]
			instance.trough_arr[i] = instance.trough_arr[i-1]
		instance.peak_arr[0] = peak_val
		instance.trough_arr[0] = trough_val
		
		# Calculate the average peak/trough amplitude.
		for i in range(0, instance.peak_count):
			peak_avg += instance.peak_arr[i]
			trough_avg += instance.trough_arr[i]
		peak_avg /= instance.peak_count
		trough_avg /= instance.trough_count
		
		# Toggle inversion is a threshold is met.
		if instance.inverted_timer == 0:
			if instance.inverted:
				if peak_avg > THRESHOLD_INVERSION * trough_avg:
					instance.inverted = False
					instance.inverted_timer = SECONDS_INVERSION
			else:
				if trough_avg < THRESHOLD_INVERSION * peak_avg:
					instance.inverted = True
					instance.inverted_timer = SECONDS_INVERSION
		else:
			instance.inverted_timer -= 1
		
		# Return the peak index (or trough index, if inverted).
		if instance.inverted:
			return trough_idx
		else:
			return peak_idx
	else:
		for j in range(max(fs,i-int(width*fs)), min(length,i+int(width*fs)+1)):
			if ecg[j] > peak_val:
				peak_idx = j
				peak_val = ecg[j]
			elif ecg[j] < trough_val:
				trough_idx = j
				trough_val = ecg[j]
		
		if instance.inverted:
			return trough_idx
		else:
			return peak_idx

def update_clean_rri(current_rri, clean, instance):
	med_rri = processing.median_array(instance.clean_rri, instance.n_rri)
	if clean or med_rri == 0 or (current_rri > 0.5*med_rri and current_rri < 1.5*med_rri):
		instance.n_rri = min(N_RRI, instance.n_rri+1)
		
		for i in range(N_RRI-1, 0, -1):
			instance.clean_rri[i] = instance.clean_rri[i-1]
		instance.clean_rri[0] = current_rri

def save_peak(peak, fs, fdai, clean, instance):
	current_rri = 0
	new_m = 0
	# Check if the peak is reasonable.
	if instance.prev_rwl != DUMMY_PEAK:
		current_rri = int(1000 * (peak - instance.prev_rwl) / fs)
		if current_rri >= 180 and instance.rwl_counter < N_SAVE and instance.rri_counter < N_SAVE:
			# Update the RWL and RRI arrays.
			instance.rwl[instance.rwl_counter] = peak - fs
			instance.rri[instance.rri_counter] = current_rri
			instance.rwl_counter += 1
			instance.rri_counter += 1
			update_clean_rri(peak - instance.prev_rwl, clean, instance)
			
			if clean:  ## NEW
			# Update the M array.
				new_m = 0.6 * fdai[peak]
				if new_m > 1.5 * instance.m_arr[N_PEAKS-1]:
					new_m = 1.1 * instance.m_arr[N_PEAKS-1]
				if new_m < 0.5 * instance.m_arr[N_PEAKS-1]:
					new_m = 0.75 * instance.m_arr[N_PEAKS-1]
				for k in range(0, N_PEAKS-1):
					instance.m_arr[k] = instance.m_arr[k+1]
				instance.m_arr[N_PEAKS-1] = new_m
			
			# Update the R array.
			# TODO: What if new RRI is absurd?
			for k in range(0, N_PEAKS-1):
				instance.r_arr[k] = instance.r_arr[k+1]
			instance.r_arr[N_PEAKS-1] = peak - instance.prev_rwl
	
	# Update the previous peak.
	instance.prev_rwl = peak

def detect_qrs_learn(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance):
	# Update the maximum M value.
	for i in range(fs, 2*fs):
		if fdai[i] > instance.max_m:
			instance.max_m = fdai[i]
	
	# Initialize the M array to 60% of the maximum.
	instance.learn_flag -= 1
	if not instance.learn_flag:
		for i in range(0, N_PEAKS):
			instance.m_arr[i] = 0.6 * instance.max_m
	
	# Track the maximum FDAI value.
	max_fdai_val = 0
	for i in range(0, N_PEAKS):
		if instance.max_fdai[i] > max_fdai_val:
			max_fdai_val = instance.max_fdai[i]
	
	# # Update the M threshold.
	# temp = 0.6 * instance.max_m
	# for i in range(0, fs):
		# m_thresh[i] = temp
	
	# # Update the F threshold.
	# mean = 0
	# counter = 0
	# if instance.learn_flag == 5:
		# for i in range(fs, fs+int(0.35*fs)):
			# mean += fdai[i]
			# counter += 1
		# mean /= counter
		# for i in range(fs, fs+int(0.35*fs)):
			# f_thresh[i-fs] = mean / 2.0
		# for i in range(fs+int(0.35*fs), 2*fs):
			# f_thresh[i-fs] = calculate_f(i, fs, fdai, instance)
	# else:
		# for i in range(fs, 2*fs):
			# f_thresh[i-fs] = calculate_f(i, fs, fdai, instance)
	
	# # Update the R threshold.
	# for i in range(0, fs):
		# r_thresh[i] = 0
	
	# Compute a peak detection threshold.
	avg = processing.mean_array(fdai, length)
	std = processing.std_array(fdai, length)
	threshold = min(avg + 1.5 * std, processing.max_array(fdai, length))
	
	m_thresh = np.zeros(fs)
	f_thresh = np.zeros(fs)
	r_thresh = np.zeros(fs)
	for i in range(0, fs):
		m_thresh[i] = threshold
		f_thresh[i] = 0
		r_thresh[i] = 0
	
	# Detect peaks in a simplified way.
	max_val = 0
	peak = 0
	i = fs
	if instance.next_peak == DUMMY_PEAK:
		i = instance.i
	else:
		save_peak(instance.next_peak, fs, fdai, True, instance)
		i = instance.next_peak + 1 # + int(0.2*fs)
		instance.next_peak = DUMMY_PEAK
	while i < 2*fs:
		max_val = 0
		for j in range(max(fs,i-int(fs/10)), min(2*fs+int(fs/10)+1,i+int(fs/10)+1)):
			if fdai[j] > max_val:
				max_val = fdai[j]
		# Heartbeats must be above some small baseline.
		if fdai[i] > max(0.1 * magnification, 0.1 * max_fdai_val):
			# Detect a heartbeat if it is a local extremum and an outlier.
			if fdai[i] > threshold and fdai[i] == max_val:
				# Correct the peak location based on the raw ECG signal.
				peak = correct_peak(f, i, length, fs, 0.025, True, instance)
				peak = correct_peak(ecg, peak, length, fs, 0.0125, False, instance)
				
				if peak < 2*fs:
					# Save the peak.
					save_peak(peak, fs, fdai, True, instance)
					
					# Increment the counter by 200 milliseconds.
					# i += int(0.2 * fs)
				else:
					instance.next_peak = peak - fs
		
		i += 1
	
	instance.i = i - fs
	
	# Store results.
	code = [0]
	
	if instance.noise_flag:
		noise = 1
	else:
		noise = 0
	
	return QRSResult(instance.rwl, instance.rri, code, fdai[fs:2*fs], m_thresh, f_thresh, r_thresh, noise, learn, res)

def detect_qrs_clean(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance):
	m_thresh = np.zeros(fs)
	f_thresh = np.zeros(fs)
	r_thresh = np.zeros(fs)
	
	med_rri = int(max(fs/5, processing.median_array(instance.clean_rri, instance.n_rri)))
	
	prev_center = 0
	prev_left = 0
	prev_right = 0
	next_center = 0
	next_left = 0
	next_right = 0
	
	threshold = 0
	max_val = 0
	max_idx = 0
	peak = 0
	peak_found = False
	
	max_fdai_val = 0
	for i in range(0, N_PEAKS):
		if instance.max_fdai[i] > max_fdai_val:
			max_fdai_val = instance.max_fdai[i]
	
	i = fs
	if instance.next_peak == DUMMY_PEAK:
		i = instance.i
	else:
		save_peak(instance.next_peak, fs, fdai, True, instance)
		i = instance.next_peak + 1 # + int(0.2*fs)
		instance.next_peak = DUMMY_PEAK
	
	while i < 2*fs:
		# Calculate the M, F, and R thresholds.
		m_thresh[i-fs] = FACTOR_MFR * calculate_m(i, fs, instance)
		f_thresh[i-fs] = FACTOR_MFR * calculate_f(i, fs, fdai, instance)
		r_thresh[i-fs] = FACTOR_MFR * calculate_r(i, fs, instance)
		threshold = m_thresh[i-fs] + f_thresh[i-fs] + r_thresh[i-fs]
		peak_found = False
		
		# Heartbeats must be above some small baseline.
		if fdai[i] > max(0.1 * magnification, 0.1 * max_fdai_val):
			# Heartbeats must be local maxima of FDAI.
			if fdai[i] >= fdai[i-1] and fdai[i] >= fdai[i+1]:
				max_val = 0
				max_idx = i
				for j in range(max(fs,i-int(WIDTH_SEARCH*fs)), min(2*fs+int(WIDTH_SEARCH*fs)+1, i+int(WIDTH_SEARCH*fs)+1)):
					if fdai[j] > max_val:
						max_val = fdai[j]
						max_idx = j
				if i == max_idx:
					# Detect a heartbeat if it exceeds the MFR threshold.
					# Allow for lower peaks if they occur at a predictable time.
					peak_found = False
					if fdai[i] > threshold:
						peak_found = True
					elif fdai[i] > 0.667 * threshold:
						prev_center = i - med_rri
						prev_left = prev_center - int(0.25*med_rri)
						prev_right = prev_center + int(0.25*med_rri)
						next_center = i + med_rri
						next_left = next_center - int(0.25*med_rri)
						next_right = next_center + int(0.25*med_rri)
						
						# If the previously-detected RWL is placed correctly...
						if instance.prev_rwl >= prev_left and instance.prev_rwl < prev_right:
							# If the next prediction window is fully contained in the available data...
							if next_right < length:
								for j in range(next_left, next_right):
									if fdai[j] > 0.667 * threshold:
										peak_found = True
										break
							# If the next prediction window is partially contained in the available data...
							elif next_left < length:
								for j in range(next_left, length):
									if fdai[j] > 0.667 * threshold:
										peak_found = True
										break
								if not peak_found and fdai[i] > 0.8 * threshold:
									peak_found = True
							# If the next prediction window is not contained in the available data...
							else:
								if fdai[i] > 0.8 * threshold:
									peak_found = True
				
				# Process the detected heartbeat.
				if peak_found:
					# Correct the peak location based on the raw ECG signal.
					peak = correct_peak(f, i, length, fs, 0.025, True, instance)
					peak = correct_peak(ecg, peak, length, fs, 0.0125, False, instance)
					
					if peak < 2*fs:
						# Save the peak.
						save_peak(peak, fs, fdai, True, instance)
						
						# Increment the counter by 200 milliseconds.
						# i += int(0.2 * fs)
					else:
						instance.next_peak = peak - fs
					
					# Update the median RR interval.
					med_rri = int(max(fs/5, processing.median_array(instance.clean_rri, instance.n_rri)))
		
		i += 1
	
	instance.i = i - fs
	
	# Store results.
	code = [0]
	
	return QRSResult(instance.rwl, instance.rri, code, fdai[fs:2*fs], m_thresh, f_thresh, r_thresh, noise, learn, res)

def detect_qrs_noisy(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance):
	m_thresh = np.zeros(fs)
	f_thresh = np.zeros(fs)
	r_thresh = np.zeros(fs)
	
	# # Calculate the M, F, and R thresholds.
	# for i in range(fs, 2*fs):
		# m_thresh[i-fs] = FACTOR_MFR * calculate_m(i, fs, instance)
		# f_thresh[i-fs] = FACTOR_MFR * calculate_f(i, fs, fdai, instance)
		# r_thresh[i-fs] = FACTOR_MFR * calculate_r(i, fs, instance)
	
	i = 0
	buffer = 0.25
	#h = 1
	if instance.next_peak != DUMMY_PEAK:
		save_peak(instance.next_peak, fs, fdai, False, instance)
		i = instance.next_peak + 1 # + int(0.2*fs)
		instance.next_peak = DUMMY_PEAK
	
	# Create a reasonable search window based on the median of the clean RRIs.
	med_rri = int(max(fs/5, processing.median_array(instance.clean_rri, instance.n_rri)))
	#order_one = processing.differentiate(instance.clean_rri, instance.n_rri, h)
	#order_two = processing.differentiate(order_one, instance.n_rri, h)
	#if order_two[-1] >=5:
	#	med_rri += int(order_one[-1])

	center = instance.prev_rwl
	left = center - int(buffer*med_rri)
	right = center + int(buffer*med_rri)
	max_val = 0
	max_idx = 0
	peak = 0
	sigma = 0
	gauss = 0
	while right < fs:
		center += med_rri
		left += med_rri
		right += med_rri
	count = 0
	while right >= fs and left < 2*fs:
		count += 1
		left = max(0, left)
		right = min(length, right)
		max_val = -1
		max_idx = left
		sigma = (right - left) / 2.0
		for j in range(max(i, left), right):
			gauss = fdai[j] * np.exp(-(j-center)*(j-center)/(2.0*sigma*sigma))
			if gauss > max_val:
				max_val = gauss
				max_idx = j
		
		for j in range(max(i, left), right):
			if fs <= j and j < 2*fs:
				m_thresh[j-fs] = max_val
				f_thresh[j-fs] = 0
				r_thresh[j-fs] = 0
		

		# Correct the peak location based on the raw ECG signal.
		peak = correct_peak(f, max_idx, length, fs, 0.025, False, instance)
		peak = correct_peak(ecg, peak, length, fs, 0.0125, False, instance)
		
		if buffer >= 0.4:
			if peak < 2*fs:
				# Save the peak.
				save_peak(peak, fs, fdai, False, instance)
				center = peak
			else:
				instance.next_peak = peak - fs
			# Update the search window smaller
			med_rri = int(max(fs/5, processing.median_array(instance.clean_rri, instance.n_rri)))
			center += max(1, med_rri) # Maybe make this previous rri
			left = center - int(buffer*med_rri)
			right = center + int(buffer*med_rri)
			buffer = 0.25
			#print('In loop 1 count: {}'.format(count))
			#print(buffer)

		elif fdai[peak] < 0.6 * processing.mean_array(instance.m_arr, N_PEAKS):
			# Update the search window bigger
			med_rri = int(max(fs / 5, processing.median_array(instance.clean_rri, instance.n_rri)))
			buffer += 0.05
			left = center - int(buffer * med_rri)
			right = center + int(buffer * med_rri)
			#print('In loop 2 count: {}'.format(count))
			#print(buffer)
		else:
			if peak < 2*fs:
				# Save the peak.
				save_peak(peak, fs, fdai, False, instance)
				center = peak
			else:
				instance.next_peak = peak - fs
			# Update the search window smaller
			med_rri = int(max(fs/5, processing.median_array(instance.clean_rri, instance.n_rri)))
			center += max(1, med_rri)
			left = center - int(buffer*med_rri)
			right = center + int(buffer*med_rri)
			buffer = 0.25
			#print('In loop 3 count: {}'.format(count))
			#print(buffer)
		#print('Center: {}'.format(center))
		#print('Left: {}'.format(left))
		#print('Right: {}'.format(right))
		#print('Med RRI: {}'.format(med_rri))
		#print('Peak: {}'.format(peak))
	
	instance.i = fs
	
	# Store results.
	code = [0]
	
	return QRSResult(instance.rwl, instance.rri, code, fdai[fs:2*fs], m_thresh, f_thresh, r_thresh, noise, learn, res)

def detect_qrs_saturated(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance):
	fdai = np.zeros(3*fs)
	
	m_thresh = np.zeros(fs)
	f_thresh = np.zeros(fs)
	r_thresh = np.zeros(fs)
	
	# Store results.
	for i in range(0, N_SAVE):
		instance.rwl[i] = DUMMY_RWL
		instance.rri[i] = DUMMY_RRI
	
	instance.reset()
	res = 1
	
	instance.i = fs
	
	# Store results.
	code = [0]
	
	return QRSResult(instance.rwl, instance.rri, code, fdai[fs:2*fs], m_thresh, f_thresh, r_thresh, noise, learn, res)

def detect_qrs(ecg, length, fs, magnification, saturation, high_noise, low_noise, instance):
	'''
	Detects QRS complexes in an electrocardiogram signal.
	
	Parameters
		ecg:				An array containing three seconds of ECG data.
		length:				Number of elements in the ecg array (should be 3*fs).
		fs:					Sampling rate of the signal (in Hertz).
		magnification:		Conversion factor to convert from raw sensor data to mV.
		saturation:			How much saturation is in the ECG packet - output by detect_noise().
		high_noise:			How much high-frequency noise is in the ECG packet - output by detect_noise().
		low_noise:			How much low-frequency noise is in the ECG packet - output by detect_noise().
		instance:			A struct containing instance variables.
		result:				A pointer to a qrs_result struct (C VERSION ONLY).
	Returns
		A QRSResult object (Python version only).
	'''
	
	if instance.noise_flag:
		noise = 1
	else:
		noise = 0
	
	if instance.learn_flag:
		learn = 1
	else:
		learn = 0
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Decision Making
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Reset if several seconds have elapsed with no heartbeat detections.
	res = 0
	if instance.nobeat_counter >= SECONDS_NOBEATS and not instance.learn_flag:
		instance.reset()
		res = 1
	
	# Set a flag if the high-frequency noise exceeds a threshold.
	# TODO: Check is this threhold should be changed!
	if high_noise < THRESHOLD_NOISE:
		instance.noise_flag = SECONDS_NOISE
	else:
		instance.noise_flag = max(0, instance.noise_flag-1)
	
	# Adjust the previous R wave location relative to the current packet.
	if instance.prev_rwl != DUMMY_PEAK:
		instance.prev_rwl = instance.prev_rwl - fs
	
	# Initialize the RWL and RRI arrays.
	instance.rwl_counter = 0
	instance.rri_counter = 0
	for i in range(0, N_SAVE):
		instance.rwl[i] = DUMMY_RWL
		instance.rri[i] = DUMMY_RRI
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Pre-Processing
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# Hard-code some parameter values.
	n = 5
	b = np.array([ 0.13993929,  0.00000000, -0.27987857,  0.00000000,  0.13993929])
	a = np.array([ 1.00000000, -2.26820013,  2.08268532, -1.02392152,  0.25949518])
	zi = np.array([-0.13993929, -0.13993929,  0.13993929,  0.13993929])
	h = 1
	width = int(0.04 * fs)
	
	# Filter, differentiate, absolute value, and integrate the ECG signal.
	f = np.zeros(length)
	fd = np.zeros(length)
	fda = np.zeros(length)
	fdai = np.zeros(length)
	f = processing.filtfilt(ecg, length, b, a, zi, n)
	fd = processing.differentiate(f, length, h)
	fda = processing.abs_array(fd, length)
	fdai = processing.integrate(fda, length, width)
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	QRS Detection
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	max_val = 0
	for i in range(fs, 2*fs):
		if fdai[i] > max_val:
			max_val = fdai[i]
	for i in range(N_PEAKS-1, 0, -1):
		instance.max_fdai[i] = instance.max_fdai[i-1]
	instance.max_fdai[0] = max_val
	
	# Reset if saturation is detected, and return nothing.
	if saturation:
		result = detect_qrs_saturated(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance)
	# TODO: What if learning AND noisy?
	if instance.learn_flag:
		result = detect_qrs_learn(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance)
	elif instance.noise_flag:
		result = detect_qrs_noisy(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance)
	else:
		result = detect_qrs_clean(ecg, f, fdai, length, fs, magnification, saturation, high_noise, low_noise, noise, learn, res, instance)
	
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# 
	#	Cleanup
	# 
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	# If no heartbeats were detected, increment a counter.
	if instance.rwl_counter == 0:
		instance.nobeat_counter = instance.nobeat_counter + 1
	else:
		instance.nobeat_counter = 0
	
	# Throw an error code if 10+ seconds elapse without a detected heartbeat.
	result.code[0] = 1 if instance.nobeat_counter >= 10 else 0
	
	return result
