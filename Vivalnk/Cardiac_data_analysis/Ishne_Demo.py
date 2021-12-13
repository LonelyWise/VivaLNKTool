import json
import time
import datetime
import os
import sys
import numpy as np
import numpy
from crccheck.crc import Crc16CcittFalse

class ReadFile:
    def __init__(self,ReadFile_log):
        self.ReadFile_log = ReadFile_log

    # 读取单个文件的数据
    def read_file_data(self,read_file_path):
        '''
        :param read_file_path:文件路径
        :return:解析后的所有数据，丢失的数据，类型
        '''
        all_data = []

        with open(read_file_path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break

                if lines[0] == '[' and lines[1] == '{':
                    if lines.find('},]') > 0:
                        lines = lines.replace('},]','}]')
                    json_array = json.loads(lines)
                    for jsonData in json_array:
                        all_data.append(jsonData)
                elif lines.find(':{') > 0:
                    index = lines.index("{")
                    lines = lines[index:len(lines)]
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                elif lines[0] == '{' and lines.find('}') > 0:
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                elif lines.find('{') > 0 and lines.find('}') > 0:
                    index = lines.index("{")
                    lines = lines[index:len(lines)]
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                else:
                    self.ReadFile_log('file format is error')

        all_data.sort(key=lambda f: f["recordTime"])
        if len(all_data) == 0:
            self.ReadFile_log('File no data')
            return None, None, ''

        first_dict = all_data[0]
        if 'ecg' in first_dict:
            self.ReadFile_log('ECG data')

            missing_tick = self.analysis_ecg_loss(all_data)
            return all_data, missing_tick, 'ecg'
        else:
            self.ReadFile_log('No parsable file')
            return None, None, ''

    # 读取一批文件的数据
    def read_batch_files_data(self,batch_files_array,compensatory_value):
        all_file_data = []
        all_missing_tick = []
        data_type = ''
        for file_path_name in batch_files_array:
            self.ReadFile_log('Analyse file:' + file_path_name)

            data_buffer, single_missing_tick, type = self.read_file_data(file_path_name)
            if data_buffer is None or len(data_buffer) == 0:
                self.ReadFile_log(file_path_name + ' file is empty')
                continue
            data_type = type

            for file_dict in data_buffer:
                all_file_data.append(file_dict)
            for file_missing_dict in single_missing_tick:
                all_missing_tick.append(file_missing_dict)

        # -1是不需要将缺失的值补偿 补偿是生成mit16的做法
        if compensatory_value != -1:
            print(all_missing_tick)
            compensatory_Array = []
            array_count = 128
            while array_count > 0:
                compensatory_Array.append(compensatory_value)
                array_count -= 1

            for miss_tuple in all_missing_tick:
                st = int(miss_tuple[0]) + 1000
                et = int(miss_tuple[1])
                while st < et:
                    miss_dict = {}
                    miss_dict['ecg'] = compensatory_Array
                    miss_dict['recordTime'] = st
                    miss_dict['flash'] = 1
                    all_file_data.append(miss_dict)
                    st += 1000

        all_file_data.sort(key=lambda f: f["recordTime"])

        ecg_missing_tick = self.analysis_data_loss(all_file_data,data_type)

        return all_file_data,ecg_missing_tick,data_type

    def analysis_data_loss(self,all_data,data_type):
        caculate_miss = 1
        miss_mill_scope = 1050

        zero_dict = all_data[0]
        last_dict = all_data[len(all_data) - 1]
        startTime = zero_dict['recordTime']
        endTime = last_dict['recordTime']
        #云端接收时间分析
        min_receive = 0
        max_receive = 0
        #lead off统计
        last_lead_status = 1
        lead_off_count = 0
        lead_off_time_set = []
        #用于体温的分钟接收率
        record_minute = startTime/1000/60
        miss_minute = 0
        # 丢失列表
        missing_tick = []

        rf_count = 0
        real_total = 0
        last_appear = 0
        time_value = 1621569600000
        tiger = 1
        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            if abs(delta) < 500:
                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f"duplicated from {start_str} to {end_str}")

            if delta > miss_mill_scope:

                # 丢失时间从lead on到lead on，不能算lead off
                value = 0
                if 'leadOn' in all_data[i]:
                    value = i
                    while (all_data[value]['leadOn'] == 0):
                        value -= 1
                if value != 0:
                    start_tick = all_data[value]["recordTime"]

                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f"part one: missing from {start_str} to {end_str}, count: {(delta / 1000) / caculate_miss - 1:.0f}")
                missing_tick += [(start_tick, end_tick)]


            if 'leadOn' in all_data[i]:
                lead_status = all_data[i]['leadOn']
                if lead_status == 0:
                    if last_lead_status == 1:
                        lead_off_time_set.append(start_tick)
                        lead_off_count += 1
                    else:
                        if (start_tick - lead_off_time_set[len(lead_off_time_set) - 1]) >= 10000:
                            lead_off_time_set.append(start_tick)
                            lead_off_count += 1
                last_lead_status = lead_status

            if data_type == 'temp':
                diff_minute = end_tick/1000/60 - record_minute
                if diff_minute >= 2:
                    miss_minute += diff_minute-1
                record_minute = end_tick/1000/60


            if 'receiveTime' in all_data[i]:
                receive_time = all_data[i]['receiveTime']
                recor_ttime = all_data[i]['recordTime']

                if min_receive == 0:
                    min_receive = receive_time
                    max_receive = receive_time
                else:
                    if receive_time < min_receive:
                        min_receive = receive_time
                    if receive_time > max_receive:
                        max_receive = receive_time

        # lead off的日志
        if lead_off_count != 0:
            self.ReadFile_log(f'lead off times:{lead_off_count}')
            for lead_off_time in lead_off_time_set:
                lead_off_time_str = datetime.datetime.fromtimestamp(lead_off_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f'Every time the lead falls off:{lead_off_time_str}')
        #丢失统计
        theory_count = (endTime - startTime) / 1000 + 1
        theory_count = int(theory_count / caculate_miss)
        self.ReadFile_log(f"Theoretical number:{theory_count}") #理论数量
        self.ReadFile_log(f"Actual number:{len(all_data)}") #实际数量
        theory_missing = int(theory_count - len(all_data))
        self.ReadFile_log(f"Query the number of theoretical losses in the time range: {theory_missing}") #查询时间范围理论丢失数量
        scope_count = (all_data[len(all_data) - 1]['recordTime'] / 1000 - zero_dict['recordTime'] / 1000) / caculate_miss +1
        self.ReadFile_log(f"Query time range actual data start and end lost quantity: {int(scope_count) - len(all_data)}") #查询时间范围实际数据起始结束丢失数量

        # 这段数据上传所用的时间
        if min_receive != 0:
            min_receive_str = datetime.datetime.fromtimestamp(min_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            max_receive_str = datetime.datetime.fromtimestamp(max_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            total_receivce_time = (max_receive - min_receive)/1000
            self.ReadFile_log(f"This piece of data upload server receiving time:{min_receive_str},{max_receive_str},spending {int(total_receivce_time)} second") #此段数据上传服务端接收时间

        return missing_tick

    # 分析ecg数据丢失
    def analysis_ecg_loss(self,all_data):
        missing_tick = []

        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

            # if abs(delta) < 500:
            #     self.ReadFile_log(f"duplicated from {start_str} to {end_str}")

            if delta > 1100:
                # self.ReadFile_log(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")
                missing_tick += [(start_tick, end_tick)]
        return missing_tick


class ProcessISHNE():
    def __init__(self,ishne_log):
        self.ishne_log = ishne_log

    def read_file_data(self):
        all_data = []
        first_time = 0
        with open('/Users/cyanxu/Desktop/C5/VVDeviceDataLog 2021-02-19 16-53.log') as  file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break

                index = lines.index("{")
                lines = lines[index:len(lines)]
                json_dict = json.loads(lines)
                ecg_array = json_dict['ecg']
                if first_time == 0:
                    first_time = json_dict['recordTime']
                for ecg_value in ecg_array:
                    ecg_float_value = ecg_value / 1000.0
                    all_data.append(ecg_float_value)

        ishne_file_name = '/Users/cyanxu/Desktop/C5/'+str(first_time)+'.log'
        self.generate_ishne_format_file(all_data, first_time,ishne_file_name)

    def generate_ishne_format_file(self,ecg_data_list, first_time,output_file_path):

        x = Holter(filename=output_file_path,read_file=False)
        x.first_name = 'Xu'
        x.last_name = 'Cyan'
        x.id = ''
        x.file_version = 1
        x.sex = 1
        x.race = 3
        x.pm = 0
        # x.load_data()
        x.sr = 128
        x.ecg_size = len(ecg_data_list)
        x.lead = [None for _ in range(1)]
        x.lead[0] = Lead(qual=1, spec=0, res=1000)
        x.lead[0].data = numpy.array(ecg_data_list, dtype=numpy.float64)
        x.lead[0].res = 1000
        x.lead = [x.lead[0]]
        x.birth_date = datetime.datetime.fromtimestamp(first_time / 1000).date()
        x.record_date = datetime.datetime.fromtimestamp(first_time / 1000).date()
        x.start_time = datetime.datetime.fromtimestamp(first_time / 1000).time()
        x.nleads = 1
        x.recorder_type = bytes('digital', encoding="utf8")
        x.proprietary = 'Proprietary'
        x.copyright = 'Copyright VivaLNK 2019'
        x.reserved = 'This is reserved block'
        x.var_block = bytes('This is variable-length block', encoding="utf8")
        x.write_file(overwrite=True)
        self.ishne_log(f'file {output_file_path} output')

    def read_iSHNE_data(self,ishne_file_path):
        x = Holter(filename=ishne_file_path,read_file=True)
        x.load_data()
        # 切割数据为128长度的数组
        ishne_ecg_array = x.lead[0].data
        ishne_split_ecg_buffer = [ishne_ecg_array[i:i + 128] for i in range(0, len(ishne_ecg_array), 128)]

        start_time_str = str(x.record_date) +' '+ str(x.start_time)
        timeArray = time.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        start_time_stamp = int(time.mktime(timeArray))*1000
        self.ishne_log('数据的起始时间:'+start_time_str)
        # 组装完整可绘制图形的数据
        data_buffer = []
        for ecg_buffer in ishne_split_ecg_buffer:
            data_dict = {}
            ecg_array = []
            start_time_stamp += 1000
            for ecg in ecg_buffer:
                ecg_value = ecg * 1000
                ecg_array.append(ecg_value)

            data_dict['ecg'] = ecg_array
            data_dict['recordTime'] = start_time_stamp
            data_buffer.append(data_dict)

        return data_buffer


################################## Functions: ##################################

def get_val(filename, ptr, datatype):
    """Jump to position 'ptr' in file and read a value of a given type (e.g. int16)."""
    val = None
    with open(filename, 'rb') as f:
        f.seek(ptr, os.SEEK_SET)
        val = np.fromfile(f, dtype=datatype, count=1)
        val = val[0]
    return val

def get_short_int(filename, ptr):
    """Jump to position 'ptr' in file and read a 16-bit integer."""
    val = get_val(filename, ptr, np.int16)
    return int( val )

def get_long_int(filename, ptr):
    """Jump to position 'ptr' in file and read a 32-bit integer."""
    val = get_val(filename, ptr, np.int32)
    return int( val )

def get_datetime(filename, offset, time=False):
    """Read three consecutive 16-bit values from file and interpret them as (day,
    month, year) or (hour, minute, second).  Return a date or time object.

    Keyword arguments:
    filename -- file to read
    offset -- start address of first value in file
    time -- True if we're getting (h,m,s), False if we're getting (d,m,y)
    """
    a,b,c = [get_short_int(filename, offset+2*i) for i in range(3)]
    try:
        if time:
            output = datetime.time(a,b,c)
        else:
            output = datetime.date(c,b,a)
    except ValueError:
        output = None
    return output

def ckstr(checksum):
    """Return a value as e.g. 'FC8E', i.e. an uppercase hex string with no leading
    '0x' or trailing 'L'.
    """
    return hex(checksum)[2:].rstrip('L').upper()

################################### Classes: ###################################

class Holter:
    def __init__(self, filename, check_valid=True, annfile=False,read_file=False):
        self.filename = filename
        self.is_annfile = annfile
        self.read_file = read_file
        self.beat_anns = []
        if read_file:
            self.load_header()
            if check_valid and not self.is_valid():
                print( "Warning: file appears to be invalid or corrupt. (%s)" % filename )
        # else:
        #     print( "Loaded header successfully.  Remember to run load_data() if you need the data too." )
        # TODO: set up for creating a *new* Holter, not just loading an existing one from a file
        # TODO: modify/disable parts of whole class appropriately when is_annfile is True.

    def __str__(self):
        result = ''
        for key in vars(self):
            if key == 'lead':
                result += 'leads: ' + str([str(l) for l in self.lead]) + '\n'
            elif key == 'beat_anns':
                result += 'beat_anns: %d beat annotations\n' % len(self.beat_anns)
            else:
                result += key + ': ' + str(vars(self)[key]) + '\n'
        return result.rstrip()
        # TODO: convert gender, race, pacemaker to readable form.  maybe do
        # ckstr(checksum) too.  units on values?

    def load_header(self):
        filename = self.filename
        assert os.path.getsize(filename) >= 522, "File is too small to be an ISHNE Holter."

        self.magic_number = get_val(filename, 0, 'a8')
        self.checksum = get_val(filename, 8, np.uint16)
        #print( "Checksum in file: %s" % ckstr(self.checksum) )

        # Fixed-size part of header:
        self.var_block_size   =   get_long_int(filename,  10)
        self.ecg_size         =   get_long_int(filename,  14)  # in number of samples
        self.var_block_offset =   get_long_int(filename,  18)  # start of variable-length block
        self.ecg_block_offset =   get_long_int(filename,  22)  # start of ECG samples
        self.file_version     =  get_short_int(filename,  26)
        self.first_name       =        get_val(filename,  28, 'a40').split(b'\x00')[0]
        self.last_name        =        get_val(filename,  68, 'a40').split(b'\x00')[0]
        self.id               =        get_val(filename, 108, 'a20').split(b'\x00')[0]
        self.sex              =  get_short_int(filename, 128)  # 1=male, 2=female
        self.race             =  get_short_int(filename, 130)  # 1=white, 2=black, 3=oriental
        self.birth_date       =   get_datetime(filename, 132)
        self.record_date      =   get_datetime(filename, 138)  # recording date
        self.file_date        =   get_datetime(filename, 144)  # date of creation of output file
        self.start_time       =   get_datetime(filename, 150, time=True)  # start time of Holter
        self.nleads           =  get_short_int(filename, 156)
        lead_spec             = [get_short_int(filename, 158+i*2) for i in range(12)]
        lead_quality          = [get_short_int(filename, 182+i*2) for i in range(12)]
        ampl_res              = [get_short_int(filename, 206+i*2) for i in range(12)]  # lead resolution in nV
        self.pm               =  get_short_int(filename, 230)  # pacemaker
        self.recorder_type    =        get_val(filename, 232, 'a40').split(b'\x00')[0]  # analog or digital
        self.sr               =  get_short_int(filename, 272)  # sample rate in Hz
        self.proprietary      =        get_val(filename, 274, 'a80').split(b'\x00')[0]
        self.copyright        =        get_val(filename, 354, 'a80').split(b'\x00')[0]
        self.reserved         =        get_val(filename, 434, 'a88').split(b'\x00')[0]
        # TODO?: read all the above with one open()

        # Variable-length part of header:
        if self.var_block_size > 0:
            self.var_block = get_val(filename, 522, 'a'+str(self.var_block_size)).split(b'\x00')[0]
        else:
            self.var_block = None

        # Create array of Leads (where lead specs and data will be stored):
        self.lead = [None for _ in range(self.nleads)]
        for i in range(self.nleads):
            self.lead[i] = Lead(lead_spec[i], lead_quality[i], ampl_res[i])

    def load_data(self, convert=True):
        """This may take some time and memory, so we don't do it until we're asked.  The
        'lead' variable is a list of Lead objects where lead[i].data is the data
        for lead number i.
        """
        # Get the data:
        with open(self.filename, 'rb') as f:
            f.seek(self.ecg_block_offset, os.SEEK_SET)
            data = np.fromfile(f, dtype=np.int16)
        # Convert it to a 2D array, cropping the end if necessary:
        nleads = self.nleads
        data = np.reshape( data[:int(len(data)/nleads)*nleads],
                                (nleads, int(len(data)/nleads)),
                                order='F' )
        # Save each row (lead), converting measurements to mV in the process:
        for i in range(nleads):
            self.lead[i].save_data( data[i], convert=convert )

    def load_ann(self, annfile=None):
        """Load beat annotations in accordance with
        http://thew-project.org/papers/ishneAnn.pdf.  The path to the annotation
        file can be specified manually, otherwise we will look for a file with a
        .ann extension alongside the original ECG.  self.beat_anns is indexed as
        beat_anns[beat number]['key']."""
        if annfile==None:
            annfile = os.path.splitext(self.filename)[0]+'.ann'
        annheader = Holter(annfile, annfile=True)  # note, var_block_offset may be wrong in .ann files
        filesize = os.path.getsize(annfile)
        headersize = 522 + annheader.var_block_size + 4
        self.beat_anns = []
        with open(annfile, 'rb') as f:
            f.seek(headersize-4, os.SEEK_SET)
            first_sample = np.fromfile(f, dtype=np.uint32, count=1)[0]
            current_sample = first_sample
            timeout = False  # was there a gap in the annotations?
            for beat in range( int((filesize - headersize) / 4) ):
                # note, the beat at first_sample isn't annotated.  so the first beat
                # in beat_anns is actually the second beat of the recording.
                ann      = chr(np.fromfile(f, dtype=np.uint8, count=1)[0])
                internal = chr(np.fromfile(f, dtype=np.uint8, count=1)[0])
                toc      =     np.fromfile(f, dtype=np.int16, count=1)[0]
                current_sample += toc
                if ann == '!':
                    timeout = True  # there was a few minutes gap in the anns; don't
                                    # know how to line them up to rest of recording
                self.beat_anns.append( {'ann': ann, 'internal': internal, 'toc': toc} )
                if not timeout:
                    self.beat_anns[-1]['samp_num'] = current_sample

    def deidentify(self):
        """Remove all PII from the file header."""
        self.first_name   = ''
        self.last_name    = ''
        self.id           = ''
        self.sex          = 0
        self.race         = 0
        self.birth_date   = None
        self.proprietary  = ''
        self.copyright    = ''
        self.reserved     = ''
        self.var_block = None
        # We don't redo the checksum because it will be fixed on re-write anyway.

    def compute_checksum(self, header_block=None):
        """Compute checksum of header block.  If header_block is None, it operates on
        the file on disk (pointed to by self.filename).

        Keyword arguments:
        header_block -- a bytes object containing the ISHNE header (typically bytes 10-522 of the file)
        """
        if header_block == None:
            with open(self.filename, 'rb') as f:
                f.seek(10, os.SEEK_SET)
                header_block = np.fromfile(f, dtype=np.uint8, count=self.ecg_block_offset-10)
                header_block = header_block.tostring()  # to make it a bytes object
        return np.uint16(Crc16CcittFalse.calc(header_block))

    def is_valid(self, verify_checksum=True):
        """Check for obvious problems with the file: wrong file signature, bad checksum,
        or invalid values for file or header size.
        """
        # Check magic number:
        if self.is_annfile: expected_magic_number = b'ANN  1.0'
        else:               expected_magic_number = b'ISHNE1.0'
        if self.magic_number != expected_magic_number:
            return False
        # Var block should always start at 522:
        if self.var_block_offset != 522:
            return False
        # Check file size.  We have no way to predict this for annotations,
        # because it depends on heart rate and annotation quality:
        if not self.is_annfile:
            filesize = os.path.getsize(self.filename)
            expected = 522 + self.var_block_size + 2*self.ecg_size
            if filesize!=expected:
                # ecg_size may have been reported as samples per lead instead of
                # total number of samples
                expected += 2*self.ecg_size*(self.nleads-1)
                if filesize!=expected:
                    return False
        # Verify CRC:
        if verify_checksum and (self.checksum != self.compute_checksum()):
                return False
        # TODO?: check SR > 0
        return True  # didn't find any problems above
        # TODO?: make this function work with in-memory Holter, i.e. not just
        # one that we loaded from disk.

    def get_length(self):
        """Return the duration of the Holter as a timedelta object.  If data has already
        been loaded, duration will be computed as the length of the first lead
        in memory.  Otherwise, it will be computed from the size of the original
        file on disk.
        """
        try:
            duration = datetime.timedelta(seconds = 1.0 * len(self.lead[0].data) / self.sr)
        except TypeError:  # self.lead[0] probably doesn't exist
            try:
                filesize = os.path.getsize(self.filename)
                duration = datetime.timedelta(seconds =
                    1.0*(filesize - 522 - self.var_block_size) / 2 / self.nleads / self.sr
                )
            except OSError:  # probably bad path to original file
                duration = None
        return duration

    # TODO?:
    # pm_codes = {
    #     0: 'none',
    #     1: 'unknown type',
    #     2: 'single chamber unipolar',
    #     3: 'dual chamber unipolar',
    #     4: 'single chamber bipolar',
    #     5: 'dual chamber bipolar',
    # }

    # TODO: dictionaries for gender and race?

    def get_header_bytes(self):
        """Create the ISHNE header from the various instance variables.  The
        variable-length block is included, but the 10 'pre-header' bytes are
        not.

        This is the only function in the class that requires python3, for
        to_bytes().
        """
        header = bytearray()

        header += (self.var_block_size       ).to_bytes(4, sys.byteorder)
        header += (self.ecg_size             ).to_bytes(4, sys.byteorder)
        header += (self.var_block_offset     ).to_bytes(4, sys.byteorder)
        header += (self.ecg_block_offset     ).to_bytes(4, sys.byteorder)
        header += (self.file_version         ).to_bytes(2, sys.byteorder, signed=True)
        header += bytes(self.first_name,'UTF-8')     [:40].ljust(40, b'\x00')
        header += bytes(self.last_name,'UTF-8')      [:40].ljust(40, b'\x00')
        header += bytes(self.id,'UTF-8')             [:20].ljust(20, b'\x00')
        header += (self.sex                  ).to_bytes(2, sys.byteorder)
        header += (self.race                 ).to_bytes(2, sys.byteorder)
        if self.birth_date:
            header += (self.birth_date.day   ).to_bytes(2, sys.byteorder)
            header += (self.birth_date.month ).to_bytes(2, sys.byteorder)
            header += (self.birth_date.year  ).to_bytes(2, sys.byteorder)
        else:
            header += (0                     ).to_bytes(6, sys.byteorder)  # TODO?: -9s
        if self.record_date:
            header += (self.record_date.day  ).to_bytes(2, sys.byteorder)
            header += (self.record_date.month).to_bytes(2, sys.byteorder)
            header += (self.record_date.year ).to_bytes(2, sys.byteorder)
        else:
            header += (0                     ).to_bytes(6, sys.byteorder)  # TODO?: -9s
        if self.file_date:
            header += (self.file_date.day    ).to_bytes(2, sys.byteorder)
            header += (self.file_date.month  ).to_bytes(2, sys.byteorder)
            header += (self.file_date.year   ).to_bytes(2, sys.byteorder)
        else:
            header += (0                     ).to_bytes(6, sys.byteorder)  # TODO?: -9s
        if self.start_time:
            header += (self.start_time.hour  ).to_bytes(2, sys.byteorder)
            header += (self.start_time.minute).to_bytes(2, sys.byteorder)
            header += (self.start_time.second).to_bytes(2, sys.byteorder)
        else:
            header += (0                     ).to_bytes(6, sys.byteorder)  # TODO?: -9s
        header += (self.nleads               ).to_bytes(2, sys.byteorder)
        for i in range(self.nleads):
            header += (self.lead[i].spec     ).to_bytes(2, sys.byteorder, signed=True)
        for i in range(12-self.nleads):
            header += (-9                    ).to_bytes(2, sys.byteorder, signed=True)
        for i in range(self.nleads):
            header += (self.lead[i].qual     ).to_bytes(2, sys.byteorder, signed=True)
        for i in range(12-self.nleads):
            header += (-9                    ).to_bytes(2, sys.byteorder, signed=True)
        for i in range(self.nleads):
            header += (self.lead[i].res      ).to_bytes(2, sys.byteorder, signed=True)
        for i in range(12-self.nleads):
            header += (-9                    ).to_bytes(2, sys.byteorder, signed=True)
        header += (self.pm                   ).to_bytes(2, sys.byteorder, signed=True)
        header += self.recorder_type       [:40].ljust(40, b'\x00')
        header += (self.sr                   ).to_bytes(2, sys.byteorder)
        header += bytes(self.proprietary,'UTF-8')    [:80].ljust(80, b'\x00')
        header += bytes(self.copyright,'UTF-8')      [:80].ljust(80, b'\x00')
        header += bytes(self.reserved,'UTF-8')       [:88].ljust(88, b'\x00')
        if self.var_block_size > 0:
            header += self.var_block

        return bytes( header )

    def autofill_header(self):
        """Automatically update several header variables for consistency.  For example,
        ecg_size will be set to the current length of the data array, and
        var_block_size will be set to the current length of the variable block
        string.
        """
        self.magic_number = b'ISHNE1.0'
        try:
            self.var_block_size = len( self.var_block )
        except TypeError:
            self.var_block_size = 0
        try:
            self.ecg_size = len( self.lead[0].data )
            # it's not clear if we should report the total number of samples
            # for *one* lead, or for *all* leads.  we do the former.
        except TypeError:
            self.ecg_size = 0
        self.var_block_offset = 522
        self.ecg_block_offset = 522+self.var_block_size
        self.file_date = datetime.datetime.now().date()
        try:
            self.nleads = len( self.lead )
        except TypeError:
            self.nleads = 0
        # TODO?: checksum.  may break is_valid().

        # TODO: enforce proper values (or -9 or whatever) for all fields.  in
        # particular, lead spec, qual, and res need to be -9 for non-present
        # leads.  sex and race should be zeroed if they're invalid.  sr >
        # 0... we can't fix that without knowing it.  set pm to -9 if it's not a
        # value in pm_codes?

    def write_file(self, overwrite=False, convert_data=True):
        """This function will write the object to disk as an ISHNE Holter file.  You do
        *not* need to pre-set the following variables: magic_number, checksum,
        var_block_size, ecg_size, var_block_offset, ecg_block_offset, file_date, and
        nleads.  They will be updated automatically when this function is called.

        Keyword arguments:
        overwrite -- whether we should overwrite an existing file
        convert_data -- whether data needs to be converted back to int16 from float (mV)
        """
        data_counts = [len(lead.data) for lead in self.lead]
        assert len(set(data_counts)) == 1, "Every lead must have the same number of samples."

        if os.path.exists(self.filename):
            assert overwrite, "File with that name already exists."
            os.remove(self.filename)  # overwrite is enabled; rm the existing
                                      # file before we start (note: may fail if
                                      # it's a directory not a file)

        # Prepare known/computable values such as variable block offset:
        self.autofill_header()

        # Write file:
        with open(self.filename, 'ab') as f:
            header = self.get_header_bytes()
            # Preheader:
            f.write( b'ISHNE1.0' )
            f.write( self.compute_checksum(header_block=header) )
            # Header:
            f.write( header )
            # Data block:
            data = []
            for i in range(self.nleads):
                data += [ self.lead[i].data_int16(convert=convert_data) ]
            data = np.reshape( data, self.nleads*len(self.lead[0].data), 'F' )
            f.write( data )
        # TODO?: remove partial file if it fails

class Lead:
    def __init__(self, spec, qual, res):
        """Store a lead's parameters (name, quality, and amplitude resolution).  Data
        (samples) from the lead will be loaded separately.

        Keyword arguments:
        spec -- numeric code from Table 1 of ISHNE Holter spec
        qual -- numeric code from Table 2 of ISHNE Holter spec
        res -- this lead's resolution in nV
        """
        self.spec = spec
        self.qual = qual
        self.res  = res
        self.data = None

    def __str__(self):
        return self.spec_str()

    def save_data(self, data, convert=True):
        """Replace the data array for this lead with a new one, optionally converting
        from ISHNE format (int16 samples) to floats (units = mV).

        Keyword arguments:
        data -- 1d numpy array of samples for this lead
        convert -- whether sample values should be converted to mV
        """
        if convert:
            data = data.astype(float)
            data *= self.res/1e6
        self.data = data

    def data_int16(self, convert=True):
        """Returns data in the format for saving to disk.  Pointless to use if convert==False."""
        data = self.data
        if convert:
            data *= 1e6/self.res
            data = data.astype(np.int16)
        return data
        # TODO?: maybe do this the other way around, save data unaltered as
        # int16 and make converted available as e.g. self.data_mV().  That may
        # reduce possibility of rounding errors during conversions.

    def spec_str(self):
        """Return this lead's human-readable name (e.g. 'V1')."""
        lead_specs = {
            -9: 'absent', 0: 'unknown', 1: 'generic',
            2: 'X',    3: 'Y',    4: 'Z',
            5: 'I',    6: 'II',   7: 'III',
            8: 'aVR',  9: 'aVL', 10: 'aVF',
            11: 'V1', 12: 'V2',  13: 'V3',
            14: 'V4', 15: 'V5',  16: 'V6',
            17: 'ES', 18: 'AS',  19: 'AI'
        }
        return lead_specs[self.spec]

    def qual_str(self):
        """Return a description of this lead's quality (e.g. 'intermittent noise')."""
        lead_quals = {
            -9: 'absent',
            0: 'unknown',
            1: 'good',
            2: 'intermittent noise',
            3: 'frequent noise',
            4: 'intermittent disconnect',
            5: 'frequent disconnect'
        }
        return lead_quals[self.qual]

def mkdir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

def print_msg(msg):
    print(msg)

def get_current_file_directory(file_name):
    '''获取当前文件的目录
    @param file_name 文件名
    :return 目录路径
    '''
    index = 0
    for i in range(0, len(file_name)):
        if file_name[i] == '/' or file_name[i] == '\\':
            index = i
    dir_name = file_name[0:index + 1]
    return dir_name


if __name__ == "__main__":

    file_name = '/Users/weixu/Desktop/ishne demo/VVDeviceDataLog 2021-06-15 20-35.log'
    read_file = ReadFile(ReadFile_log=print_msg)
    all_data,miss_data,type = read_file.read_batch_files_data([file_name],compensatory_value=8700)

    start_time = all_data[0]['recordTime']
    dir_name = get_current_file_directory(file_name=file_name)
    mkdir(dir_name + 'ishne')
    ishne_dir_file_name = dir_name + 'ishne/' + str(start_time) + '.ecg'

    all_ecg_data = []
    for json_dict in all_data:
        ecg_array = json_dict['ecg']
        for ecg_value in ecg_array:
            ecg_float_value = ecg_value / 1000.0
            all_ecg_data.append(ecg_float_value)

    if type == 'ecg':
        process_ishne = ProcessISHNE(ishne_log=print_msg)
        process_ishne.generate_ishne_format_file(ecg_data_list=all_ecg_data, first_time=start_time,
                                                 output_file_path=ishne_dir_file_name)


