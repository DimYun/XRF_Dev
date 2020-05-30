availableCOM = []
device_com = ''
filename = ''
voltage_kv = 0
current_mk_a = 0
exposition_s = 0

panda = False #parameter for type of spectrometr
is_dp5 = True

#Numbers of all sample
num_all_sample = 0
#Numbers of measure one sample
num_meas_sample = 0
#Number of measure one sample to rewrite
num_meas_sample_const = 0
#Number of measure of all sample
num_all_sample = 0
#Time interval for measure one sample
int_meas_sample = 0
#Time interval for measure betwin samples
int_meas_all = 0

#How math spec we hawe
spec_all = 0

#Index for filename
index_file = 0

#Filename for log file
filenameLOG = ''

#Counter for measures
count_measure = 1

# Temperature of detector, K
tempr = 0

#Constant for starting COM in thread
running_const = True

live_time = 0
dead_time = 0

#List for I 
y_list_all = []