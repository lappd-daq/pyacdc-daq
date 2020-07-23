import acc
import sys
import time
import timeit
import numpy as np 
import matplotlib.pyplot as plt 
import pickle

	
#this function tries to just send
#a data query, and then pull data as 
#soon as it is ready. You need to 
#disable print statements and 
#data parsing for this to be accurate.
#Furthermore, it may have innacuracies
#that can be resolved by the timeit library. 
def time_transfer_only():
	a = acc.ACC() #opens serial port. 

	times = []
	testboards = [0]
	for i in range(2000):
		t0 = time.time()
		a.send_soft_trigger(testboards)
		a.read_acdc()
		times.append(time.time() - t0)


	a.close()
	pickle.dump(times, open("times_7-22.p", "wb"))

	#start plotting functionals
	"""
	times = pickle.load(open("times_7-22.p", "rb"))
	fig, ax = plt.subplots(ncols = 2)
	rates = [1.0/_ for _ in times]
	binwidth = 0.04
	bins = np.arange(min(rates), max(rates), binwidth)
	ax[0].hist(rates, bins, histtype='step', fill = False, color='black', linewidth=2, label="std: " + str(round(np.std(rates), 3)) + "\nmean : " + str(round(np.mean(rates), 2)))
	ax[0].legend(fontsize=17)
	ax[0].set_xlabel("Inverse of comms delay (Hz)", fontsize=18)
	ax[0].set_ylabel("Triggers per " + str(binwidth) + " Hz binwidth", fontsize=18)

	binwidth = 0.00004
	bins = np.arange(min(times), max(times), binwidth)
	ax[1].hist(times, bins, histtype='step', fill = False, color='black', linewidth=2, label="std: " + str(round(np.std(times)*1000, 2)) + "\nmean : " + str(round(np.mean(times)*1000, 2)))
	ax[1].legend(fontsize=17)
	ax[1].set_xlabel("Comms delay (sec)", fontsize=18)
	ax[1].set_ylabel("Triggers per " + str(binwidth) + " sec binwidth", fontsize=18)

	for x in ax:
		x.get_xaxis().set_tick_params(labelsize=15, length=14, width=2, which='major')
		x.get_xaxis().set_tick_params(labelsize=15,length=7, width=2, which='minor')
		x.get_yaxis().set_tick_params(labelsize=15,length=14, width=2, which='major')
		x.get_yaxis().set_tick_params(labelsize=15,length=7, width=2, which='minor')

	plt.show()
	"""




#looks at error codes from the 
#ACDC buffers and counts errors. 
def check_buffer_correctness():
	a = acc.ACC() #opens serial port. 
	testboards = [0]
	a.send_soft_trigger(testboards)
	num_errors = a.read_acdc()

	#if none of the coarse errors exit,
	#check for errors in the sequential arrival
	#of data words. 
	if(num_errors == 0):
		bad_buffers = a.check_sum()
		if(bad_buffers != 0):
			print("Got " + str(bad_buffers) + " bad buffers")




if __name__ == "__main__":
	check_buffer_correctness()




	

