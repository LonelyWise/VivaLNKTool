import numpy as np
from scipy.interpolate import interp1d
import json
import time
from datetime import datetime


# Desired sampling rates (signals will be resampled to these rates).
FS_ECG = 128
FS_ACC = 5
FS_PPG = 150


class Packet():
	def __init__(self, timestamp, dict, num):
		date = None
		time = None
		device = None
		# self.unix = 1000 * timelib.mktime(datetime.strptime(str.replace("-", "/"), "%m/%d/%Y %H:%M:%S.%f").timetuple()) + int(time.split(".")[1])
		ecg = None
		x = None
		y = None
		z = None
		rwl = None
		rri = None
		hr = None
		rr = None
		sys = None
		dia = None
		bp_time = None
		button = None
		accuracy = None
		magnification = None
		offset = None
		leadon = None
		flash = None
		recordtime = None
		receivetime = None
		errors = []
		
		# Check if the timestamp is formatted correctly.
		if len(timestamp) > 0:
			dt = timestamp.split(" ")
			if len(dt) == 2:
				date = dt[0].strip()
				time = dt[1].strip()
				
				# Check the date format.
				if len(date) == 10:
					if date[4] == date[7] == "-":
						year = date[:4]
						month = date[5:7]
						day = date[8:]
						
						if year.isdigit():
							if int(year) < 2000:
								errors.append("Line {}: Formatting error: Year is less than 2000.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Year is not a digit.\n".format(num))
						
						if month.isdigit():
							if int(month) > 12:
								errors.append("Line {}: Formatting error: Month is greater than 12.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Month is not a digit.\n".format(num))
						
						if day.isdigit():
							if int(day) > 31:
								errors.append("Line {}: Formatting error: Day is greater than 31.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Day is not a digit.\n".format(num))
					else:
						errors.append("Line {}: Formatting error: Date does not have format YYYY-MM-DD.\n".format(num))
				else:
					errors.append("Line {}: Formatting error: Date has incorrect length.\n".format(num))
				
				# Check the time format.
				if len(time) == 12:
					if time[2] == time[5] == ":" or time[8] == ".":
						hour = time[:2]
						minute = time[3:5]
						second = time[6:8]
						millisecond = time[9:]
						
						if hour.isdigit():
							if int(hour) > 23:
								errors.append("Line {}: Formatting error: Hour is greater than 23.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Hour is not a digit.\n".format(num))
						
						if minute.isdigit():
							if int(minute) > 59:
								errors.append("Line {}: Formatting error: Hour is greater than 59.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Hour is not a digit.\n".format(num))
						
						if second.isdigit():
							if int(second) > 59:
								errors.append("Line {}: Formatting error: Second is greater than 59.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Second is not a digit.\n".format(num))
						
						if not millisecond.isdigit():
							errors.append("Line {}: Formatting error: Millisecond is not a digit.\n".format(num))
					else:
						errors.append("Line {}: Formatting error: Time does not have format HH:MM:SS.mmm.\n".format(num))
				else:
					errors.append("Line {}: Formatting error: Time has incorrect length.\n".format(num))
			else:
				errors.append("Line {}: Formatting error: Incorrect number of tokens in timestamp.\n".format(num))
		else:
			errors.append("Line {}: Formatting error: Timestamp not found.\n".format(num))
		
		# Check if the data is formatted correctly.
		keys = list(dict.keys())
		if len(keys) > 0:
			magnification = 1
			if "deviceId" in keys:
				temp = dict["deviceId"]
				device = temp.split("/")[-1]
			if "magnification" in keys:
				temp = dict["magnification"]
				if isinstance(temp, int):
					magnification = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer magnification value encountered.\n".format(num))
			else:
				errors.append("Line {}: Data integrity error: Magnification not found.\n".format(num))
			
			if "ecg" in keys:
				ecg = []
				temp = dict["ecg"]
				temp_ecg = []
				for e in temp:
					if isinstance(e, int):
						temp_ecg.append(float(e / magnification))
					else:
						temp_ecg.append(e)
						errors.append("Line {}: Data integrity error: Non-integer ECG value encountered.\n".format(num))
				if len(temp) != FS_ECG:
					if len(temp) < FS_ECG:
						errors.append("Line {}: Data integrity error: ECG undersampled ({} / {}).\n".format(num, len(temp), FS_ECG))
					elif len(temp) > FS_ECG:
						errors.append("Line {}: Data integrity error: ECG oversampled ({} / {}).\n".format(num, len(temp), FS_ECG))
					ecg = interp1d(np.linspace(0, 1, len(temp_ecg)), temp_ecg)(np.linspace(0, 1, FS_ECG))
				else:
					ecg = temp_ecg
			else:
				errors.append("Line {}: Data integrity error: ECG not found.\n".format(num))
			
			accuracy = 1
			if "accAccuracy" in keys:
				temp = dict["accAccuracy"]
				if isinstance(temp, int):
					accuracy = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer ACC accuracy value encountered.\n".format(num))
			else:
				errors.append("Line {}: Data integrity error: ACC accuracy not found.\n".format(num))
			
			if "acc" in keys:
				x = []
				y = []
				z = []
				xyz = dict["acc"]
				temp_x = []
				temp_y = []
				temp_z = []
				for a in xyz:
					if len(a) == 3:
						temp = a[0]
						if isinstance(temp, int):
							temp_x.append(float(temp / accuracy))
						else:
							errors.append("Line {}: Data integrity error: Non-integer X-axis ACC value encountered.\n".format(num))
						
						temp = a[1]
						if isinstance(temp, int):
							temp_y.append(float(temp / accuracy))
						else:
							errors.append("Line {}: Data integrity error: Non-integer Y-axis ACC value encountered.\n".format(num))
						
						temp = a[2]
						if isinstance(temp, int):
							temp_z.append(float(temp / accuracy))
						else:
							errors.append("Line {}: Data integrity error: Non-integer Z-axis ACC value encountered.\n".format(num))
					else:
						if len(a) < 3:
							errors.append("Line {}: Data integrity error: Fewer than 3 ACC axes encountered.\n".format(num))
						else:
							errors.append("Line {}: Data integrity error: More than 3 ACC axes encountered.\n".format(num))
				
				if (len(xyz) != FS_ACC) and (temp_x !=[]):
					if len(xyz) < FS_ACC:
						errors.append("Line {}: Data integrity error: ACC undersampled ({} / {}).\n".format(num, len(xyz), FS_ACC))
					elif len(xyz) > FS_ACC:
						errors.append("Line {}: Data integrity error: ACC oversampled ({} / {}).\n".format(num, len(xyz), FS_ACC))
					x = interp1d(np.linspace(0, 1, len(temp_x)), temp_x)(np.linspace(0, 1, FS_ACC))
					y = interp1d(np.linspace(0, 1, len(temp_y)), temp_y)(np.linspace(0, 1, FS_ACC))
					z = interp1d(np.linspace(0, 1, len(temp_z)), temp_z)(np.linspace(0, 1, FS_ACC))
				else:
					x = temp_x
					y = temp_y
					z = temp_z
			else:
				errors.append("Line {}: Data integrity error: ACC not found.\n".format(num))
			
			if "accOffset" in keys:
				offset = []
				temp = dict["accOffset"]
				for a in temp:
					if isinstance(a, int):
						offset.append(a)
					else:
						errors.append("Line {}: Data integrity error: Non-integer accOffset value encountered.\n".format(num))
			
			if "rwl" in keys:
				rwl = []
				temp = dict["rwl"]
				for r in temp:
					if isinstance(r, int):
						if r != -1:
							rwl.append(r + (num-2)*FS_ECG)
					else:
						errors.append("Line {}: Data integrity error: Non-integer RWL value encountered.\n".format(num))
			
			if "rri" in keys:
				rri = []
				temp = dict["rri"]
				for r in temp:
					if isinstance(r, int):
						if r != 0:
							rri.append(r)
					else:
						errors.append("Line {}: Data integrity error: Non-integer RRI value encountered.\n".format(num))
			
			if "hr" in keys:
				hr = -1
				temp = dict["hr"]
				if isinstance(temp, int):
					hr = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer HR value encountered.\n".format(num))
			
			if "rr" in keys:
				rr = -1
				temp = dict["rr"]
				if isinstance(temp, int) or isinstance(temp, float):
					if temp == 0:
						temp = np.nan
					rr = temp
				else:
					errors.append("Line {}: Data integrity error: Non-numeric RR value encountered.\n".format(num))
			
			#if "bp" in keys:
			#	bp_time = num
				
			#	temp = dict["bp"]
			#	sys = int(temp.split("/")[0])
			#	dia = int(temp.split("/")[1])
			
			if "button" in keys:
				button = num
			
			if "leadOn" in keys:
				leadon = -1
				temp = dict["leadOn"]
				if isinstance(temp, int):
					leadon = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer lead-on value encountered.\n".format(num))
			
			if "flash" in keys:
				flash = -1
				temp = dict["flash"]
				if isinstance(temp, int):
					flash = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer flash value encountered.\n".format(num))
			
			if "recordTime" in keys:
				recordtime = -1
				temp = dict["recordTime"]
				if isinstance(temp, int):
					recordtime = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer record time value encountered.\n".format(num))
			
			if "receiveTime" in keys:
				receivetime = -1
				temp = dict["receiveTime"]
				if isinstance(temp, int):
					receivetime = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer receive time value encountered.\n".format(num))
		else:
			errors.append("Line {}: Data integrity error: Data not found.\n".format(num))
		
		self.num = num
		self.date = date
		self.time = time
		self.device = device
		self.ecg = ecg
		self.x = x
		self.y = y
		self.z = z
		self.rwl = rwl
		self.rri = rri
		self.hr = hr
		self.rr = rr
		self.sys = sys
		self.dia = dia
		self.bp_time = bp_time
		self.button = button
		self.magnification = magnification
		self.accuracy = accuracy
		self.offset = offset
		self.leadon = leadon
		self.flash = flash
		self.recordtime = recordtime
		self.receivetime = receivetime
		self.errors = errors

class Recording():
	def __init__(self, packets, filename):
		self.filename = filename
		num = np.array([packet.num for packet in packets])
		date = np.array([packet.date for packet in packets])
		time = np.array([packet.time for packet in packets])
		device = np.array([packet.device for packet in packets])
		ecg = np.array([packet.ecg for packet in packets])
		x = np.array([packet.x for packet in packets])
		y = np.array([packet.y for packet in packets])
		z = np.array([packet.z for packet in packets])
		rwl = np.array([packet.rwl for packet in packets], dtype='object') # add dtype to avoid depr error
		rri = np.array([packet.rri for packet in packets], dtype='object') # add dtype to avoid depr error
		hr = np.array([packet.hr for packet in packets])
		rr = np.array([packet.rr for packet in packets])
		sys = np.array([packet.sys for packet in packets])
		dia = np.array([packet.dia for packet in packets])
		bp_time = np.array([packet.bp_time for packet in packets])
		button = np.array([packet.button for packet in packets])
		magnification = np.array([packet.magnification for packet in packets])
		accuracy = np.array([packet.accuracy for packet in packets])
		offset = np.array([packet.offset for packet in packets], dtype='object')
		leadon = np.array([packet.leadon for packet in packets])
		flash = np.array([packet.flash for packet in packets])
		recordtime = np.array([packet.recordtime for packet in packets])
		receivetime = np.array([packet.receivetime for packet in packets])
		errors = np.array([packet.errors for packet in packets], dtype='object')
		
		if len(remove_none(recordtime)) > 0:
			idx = np.argsort(recordtime)
			
			self.num = num[idx]
			self.date = date[idx]
			self.time = time[idx]
			self.device = device[idx]
			self.ecg = flatten(ecg[idx])
			self.x = flatten(x[idx])
			self.y = flatten(y[idx])
			self.z = flatten(z[idx])
			self.rwl = flatten(rwl[idx])
			self.rri = flatten(rri[idx])
			self.hr = hr[idx]
			self.rr = rr[idx]
			self.sys = remove_none(sys[idx])
			self.dia = remove_none(dia[idx])
			self.bp_time = bp_time[idx]
			self.button = button[idx]
			self.magnification = magnification[idx]
			self.accuracy = accuracy[idx]
			self.offset = offset[idx]
			self.leadon = leadon[idx]
			self.flash = flash[idx]
			self.recordtime = recordtime[idx]
			self.receivetime = receivetime[idx]
			self.errors = flatten(errors[idx])
		else:
			self.num = num
			self.date = date
			self.time = time
			self.device = device
			self.ecg = flatten(ecg)
			self.x = flatten(x)
			self.y = flatten(y)
			self.z = flatten(z)
			self.rwl = flatten(rwl)
			self.rri = flatten(rri)
			self.hr = hr
			self.rr = rr
			self.sys = remove_none(sys)
			self.dia = remove_none(dia)
			self.bp_time = bp_time
			self.button = button
			self.magnification = magnification
			self.accuracy = accuracy
			self.offset = offset
			self.leadon = leadon
			self.flash = flash
			self.recordtime = recordtime
			self.receivetime = receivetime
			self.errors = flatten(errors)

class PPGPacket():
	def __init__(self, timestamp, dict, num):
		date = None
		time = None
		red = None
		ir = None
		motion = None
		count = None
		recordtime = None
		errors = []
		
		# Check if the timestamp is formatted correctly.
		if len(timestamp) > 0:
			dt = timestamp.split(" ")
			if len(dt) == 2:
				date = dt[0].strip()
				time = dt[1].strip()
				
				# Check the date format.
				if len(date) == 10:
					if date[4] == date[7] == "-":
						year = date[:4]
						month = date[5:7]
						day = date[8:]
						
						if year.isdigit():
							if int(year) < 2000:
								errors.append("Line {}: Formatting error: Year is less than 2000.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Year is not a digit.\n".format(num))
						
						if month.isdigit():
							if int(month) > 12:
								errors.append("Line {}: Formatting error: Month is greater than 12.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Month is not a digit.\n".format(num))
						
						if day.isdigit():
							if int(day) > 31:
								errors.append("Line {}: Formatting error: Day is greater than 31.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Day is not a digit.\n".format(num))
					else:
						errors.append("Line {}: Formatting error: Date does not have format YYYY-MM-DD.\n".format(num))
				else:
					errors.append("Line {}: Formatting error: Date has incorrect length.\n".format(num))
				
				# Check the time format.
				if len(time) == 12:
					if time[2] == time[5] == ":" or time[8] == ".":
						hour = time[:2]
						minute = time[3:5]
						second = time[6:8]
						millisecond = time[9:]
						
						if hour.isdigit():
							if int(hour) > 23:
								errors.append("Line {}: Formatting error: Hour is greater than 23.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Hour is not a digit.\n".format(num))
						
						if minute.isdigit():
							if int(minute) > 59:
								errors.append("Line {}: Formatting error: Hour is greater than 59.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Hour is not a digit.\n".format(num))
						
						if second.isdigit():
							if int(second) > 59:
								errors.append("Line {}: Formatting error: Second is greater than 59.\n".format(num))
						else:
							errors.append("Line {}: Formatting error: Second is not a digit.\n".format(num))
						
						if not millisecond.isdigit():
							errors.append("Line {}: Formatting error: Millisecond is not a digit.\n".format(num))
					else:
						errors.append("Line {}: Formatting error: Time does not have format HH:MM:SS.mmm.\n".format(num))
				else:
					errors.append("Line {}: Formatting error: Time has incorrect length.\n".format(num))
			else:
				errors.append("Line {}: Formatting error: Incorrect number of tokens in timestamp.\n".format(num))
		else:
			errors.append("Line {}: Formatting error: Timestamp not found.\n".format(num))
		
		# Check if the data is formatted correctly.
		keys = list(dict.keys())
		if len(keys) > 0:
			if "count" in keys:
				count = -1
				temp = dict["count"]
				if isinstance(temp, int):
					count = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer count value encountered.\n".format(num))
			
			if "PPG" in keys:
				ppg = dict["PPG"]
				temp_red = []
				temp_ir = []
				temp_motion = []
				
				for sample_dict in ppg:
					sample_keys = list(sample_dict.keys())
					
					if "red" in sample_keys:
						temp = sample_dict["red"]
						if isinstance(temp, int):
							# TODO: Figure out magnification value for PPG red.
							temp_red.append(temp)
						else:
							errors.append("Line {}: Data integrity error: Non-integer PPG red value encountered.\n".format(num))
					else:
						errors.append("Line {}: Data integrity error: PPG red not found.\n".format(num))
					
					if "ir" in sample_keys:
						temp = sample_dict["ir"]
						if isinstance(temp, int):
							# TODO: Figure out magnification value for PPG IR.
							temp_ir.append(temp)
						else:
							errors.append("Line {}: Data integrity error: Non-integer PPG IR value encountered.\n".format(num))
					else:
						errors.append("Line {}: Data integrity error: PPG IR not found.\n".format(num))
					
					if "motion" in sample_keys:
						temp = sample_dict["motion"]
						if isinstance(temp, int):
							temp_motion.append(temp)
						else:
							errors.append("Line {}: Data integrity error: Non-integer PPG motion value encountered.\n".format(num))
					else:
						errors.append("Line {}: Data integrity error: PPG motion not found.\n".format(num))
				
				if len(temp_red) != count:
					if len(temp_red) < count:
						errors.append("Line {}: Data integrity error: PPG red undersampled ({} / {}).\n".format(num, len(temp_red), count))
					elif len(temp_red) > count:
						errors.append("Line {}: Data integrity error: PPG red oversampled ({} / {}).\n".format(num, len(temp_red), count))
					red = interp1d(np.linspace(0, 1, len(temp_red)), temp_red)(np.linspace(0, 1, count))
				else:
					red = temp_red
				
				if len(temp_ir) != count:
					if len(temp_ir) < count:
						errors.append("Line {}: Data integrity error: PPG IR undersampled ({} / {}).\n".format(num, len(temp_ir), count))
					elif len(temp_ir) > count:
						errors.append("Line {}: Data integrity error: PPG IR oversampled ({} / {}).\n".format(num, len(temp_ir), count))
					ir = interp1d(np.linspace(0, 1, len(temp_ir)), temp_ir)(np.linspace(0, 1, count))
				else:
					ir = temp_ir
				
				if len(temp_motion) != count:
					if len(temp_motion) < count:
						errors.append("Line {}: Data integrity error: PPG motion undersampled ({} / {}).\n".format(num, len(temp_motion), count))
					elif len(temp_motion) > count:
						errors.append("Line {}: Data integrity error: PPG motion oversampled ({} / {}).\n".format(num, len(temp_motion), count))
					motion = interp1d(np.linspace(0, 1, len(temp_motion)), temp_motion)(np.linspace(0, 1, count))
				else:
					motion = temp_motion
			else:
				errors.append("Line {}: Data integrity error: PPG not found.\n".format(num))
			
			if "recordTime" in keys:
				recordtime = -1
				temp = dict["recordTime"]
				if isinstance(temp, int):
					recordtime = temp
				else:
					errors.append("Line {}: Data integrity error: Non-integer record time value encountered.\n".format(num))
		
		self.num = num
		self.date = date
		self.time = time
		self.count = count
		self.red = red
		self.ir = ir
		self.motion = motion
		print(red)
		print(ir)
		print(motion)
		input()
		self.recordtime = recordtime
		self.errors = errors

class PPGRecording():
	def __init__(self, packets, filename):
		self.filename = filename
		num = np.array([packet.num for packet in packets])
		date = np.array([packet.date for packet in packets])
		time = np.array([packet.time for packet in packets])
		count = np.array([packet.count for packet in packets])
		red = np.array([packet.red for packet in packets])
		ir = np.array([packet.ir for packet in packets])
		motion = np.array([packet.motion for packet in packets])
		recordtime = np.array([packet.recordtime for packet in packets])
		errors = np.array([packet.errors for packet in packets])
		
		if len(remove_none(recordtime)) > 0:
			idx = np.argsort(recordtime)
			self.num = num[idx]
			self.date = date[idx]
			self.time = time[idx]
			self.count = count[idx]
			self.red = flatten(red[idx])
			self.ir = flatten(ir[idx])
			self.motion = flatten(motion[idx])
			self.recordtime = recordtime[idx]
			self.errors = flatten(errors[idx])
		else:
			self.num = num
			self.date = date
			self.time = time
			self.count = count
			self.red = flatten(red)
			self.ir = flatten(ir)
			self.motion = flatten(motion)
			self.recordtime = recordtime
			self.errors = flatten(errors)

class Reference():
	def __init__(self, timestamps, data, filename):
		idx = np.argsort(timestamps)
		
		self.filename = filename
		if len(timestamps) > 0:
			self.timestamps = np.array(timestamps)[idx]
			self.data = np.array(data)[idx]
		else:
			self.timestamps = []
			self.data = data

class Info():
	def __init__(self, dict):
		self.systolic = dict["Systolic"]
		self.diastolic = dict["Diastolic"]
		self.hr = dict["Heart Rate"]
		self.age = dict["Age"]
		self.gender = dict["Gender"]
		self.ethnicity = dict["Ethnicity"]
		self.height = dict["Height (cm)"]
		self.weight = dict["Weight (kg)"]
		self.bmi = dict["Weight (kg)"] / (dict["Height (cm)"] / 100)**2
		


def flatten(arr):
	return np.array([item for sublist in arr if sublist is not None for item in sublist])

def remove_none(arr):
	return np.array([item for item in arr if item is not None])

def read_info(filename):
	dict = {}
	
	with open(filename, "r") as f:
		for line in f:
			contents = line.strip().split(",")
			if contents[0] == "Systolic":
				dict["Systolic"] = int(contents[1])
			elif contents[0] == "Diastolic":
				dict["Diastolic"] = int(contents[1])
			elif contents[0] == "Heart Rate":
				dict["Heart Rate"] = int(contents[1])
			elif contents[0] == "Age":
				dict["Age"] = int(contents[1])
			elif contents[0] == "Gender":
				dict["Gender"] = contents[1]
			elif contents[0] == "Ethnicity":
				dict["Ethnicity"] = contents[1]
			elif contents[0] == "Height (cm)":
				dict["Height (cm)"] = int(contents[1])
			elif contents[0] == "Weight (kg)":
				dict["Weight (kg)"] = int(contents[1])
	
	return Info(dict)

def read_bp(filename):
	sys = 0
	dia = 0
	
	with open(filename, "r") as f:
		contents = f.readlines()[0].strip().split(",")
		sys = int(contents[0])
		dia = int(contents[1])
	
	return sys, dia

def read_packets(filename, device="ECG"):
	packets = []
	
	with open(filename, "r") as f:
		lines = f.readlines()
		for i in range(len(lines)):
			line = lines[i]

			# Split the packet into timestamp and data.
			brace_idx1 = line.find("{")
			brace_idx2 = line.rfind("}")
			timestamp = line[:brace_idx1-1].split("--")[0].strip()
			dict = json.loads(line[brace_idx1:brace_idx2+1].strip())
			if device == "ECG":
				packets.append(Packet(timestamp, dict, i+1))
			elif device == "PPG":
				packets.append(PPGPacket(timestamp, dict, i+1))  
	return packets

def read_recording(filename):
	return Recording(read_packets(filename), filename.split("/")[-1])