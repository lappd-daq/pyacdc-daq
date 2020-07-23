import usb.core
import usb.util
import time
import sys
import usb_device as usbdev
from comms_defs import * #all word definitions
import acdc

class ACC:
	def __init__(self):
		self.max_N = 4 #max number of boards.

		#usb device connected to ACC
		self.dev = usb.core.find(idVendor=usbdev.VID, idProduct=usbdev.PID)
		if self.dev is None:
			print("The ACC cannot be reached by USB communications.")
			sys.exit()

		self.dev.set_configuration()
		self.dev.reset()

		self.raw_acc_info = [] #raw info buffer of ACC, no dictionary indexing.
		self.acc_info = {} #info buffer of ACC from 1e0C0005, string dictionary

		self.acdcs = {} #acdc objects, indexed by number. 


   
	def close(self):
		usb.util.dispose_resources(self.dev) 


	#num_bytes is number of 16 bit words
	def read_usb(self, num_words):
		try:
			ret = self.dev.read(usbdev.EDPNT_RD, num_words)
		except:
			print("Usb either had a time-out on read operation or some other error")
			return []


		#combine to make 32 bit words.
		#transmits LS word first.
		packet = []
		for i in range(0, len(ret), 2):
			packet.append((ret[i+1] << 8) | ret[i])

		#print("Got " + str(len(packet)) + " 32 bit words on usb read")
		return packet


	#msg is an int representing the hex code.
	#i.e. int("1e0C0005", 16)
	def write_usb(self, msg):
		packet = [msg & int("FF", 16), msg & int("FF00", 16), \
				msg & int("FF0000", 16), msg & int("FF000000", 16)] 

		#shift by the byte index
		packet = [(packet[i] >> 8*i) for i in range(len(packet))]
		#write to usb
		try:
			#print("Sending command: ", end='')
			#print([hex(_) for _ in packet])
			self.dev.write(usbdev.EDPNT_WR, packet)
		except:
			print("Error in writing to usb line: ", end='')
			print(packet)

	def print_rx_data(self, ret):
		print("Read back " + str(len(ret)) + " 32-bit words: ")
		for i, word in enumerate(ret):
			print(str(i)+" " + hex(word))

	#takes a list of board numbers
	#and turns it into a 16 bit word
	def nos_to_bits(self, nos):
		word = 0
		for n in nos:
			word += (1 << n)
		return word

	#takes a 16 bit word representing
	#a board mask and returns a list of nos
	def bits_to_nos(self, bits):
		nos = []
		for i in range(self.max_N):
			if(bits & (1 << i)):
				nos.append(i)
		return nos




	#a debug function that
	#takes a string msg from input
	#and converts to the necessary format
	#to send down the line and read as we go.
	#if read_option is 1, reads at each command.
	#otherwise, only reads at the end.
	def debug(self, msg, read_option=0):
		num_words = acdc_expected_length + usb_read_padding
		for m in msg:
			self.write_usb(int(m, 16))

			if(read_option == 1):
				ret = self.read_usb(num_words)
				self.print_rx_data(ret)

		ret = self.read_usb(num_words)
		self.print_rx_data(ret)



	#send software trigger to board numbers in list "nos"
	def send_soft_trigger(self, nos):
		boardmask = self.nos_to_bits(nos)
		cmd = 0x000A0007 | (boardmask << 25)
		self.write_usb(cmd)


	#read acc local info buffer
	def read_acc(self): 
		msg = 0x1E0C0005
		self.write_usb(msg)
		packet = self.read_usb(acc_expected_length + usb_read_padding)
		self.raw_acc_info = packet
		#check for errors
		if(packet[0] != startword or packet[1] != acc_frame_start):
			print("ACC returned bad info on itself")
			return


		#form dictionary for each word. 
		self.acc_info["link_status"] = packet[2] & 0xF #only looking at first half for now. 
		self.acc_info["accrx_packet_started"] = (packet[4] >> 4) & 0xF 
		self.acc_info["accrx_packet_complete"] = packet[4] & 0xF


	#read any and all acdcs that have data in ACC ram 
	def read_acdc(self):
		#first get a fresh ACC info buffer to 
		#check which ACDCs look connected.
		self.read_acc()

		connected_acdcs = [] #list of ints correpsonding to acdc addresses
		for i in range(self.max_N):
			if(self.acc_info["link_status"] & (1 << i)):
				connected_acdcs.append(i)


		#send a software trigger signal
		"""
		board_mask = 0
		trigbin = 0
		for no in connected_acdcs:
			board_mask += (1 << no)
			cmd = int("000E0000", 16) | board_mask | (trigbin << 4)
			self.write_usb(cmd)
		"""
		started = False
		complete = False
		error_codes = {}
		for no in connected_acdcs:
			error_codes[no] = []
			#print("Link is up for ACDC " + str(no))
			started = self.acc_info["accrx_packet_started"] & (1 << no)
			complete = self.acc_info["accrx_packet_complete"] & (1 << no)
			#if no data started, don't query
			if(started == False):
				print(", but no data is being or has been transmitted to the acc")
				continue

			#if started and complete, read the data
			elif(started and complete):
				cmd = 0x000C0000 | (no + 1)
				self.write_usb(cmd)
				usb_buffer = self.read_usb(acdc_expected_length + usb_read_padding)
				#fill this buffer into the acdc object.
				#if it doesnt exist yet, create it!
				if(not(no in self.acdcs)):
					self.acdcs[no] = acdc.ACDC(no)
				error_codes[no] += self.acdcs[no].set_raw_data(usb_buffer)
				#print("Finished reading and parsing ACDC " + str(no) + " data")

			#if started but not yet completed transmission to the ACC
			elif(started and complete == False):
				timeout = 1 #one second timeout on this loop
				timedout = False
				t0 = time.time()
				while True:
					self.read_acc()
					complete = self.acc_info["accrx_packet_complete"] & (1 << no)
					if(complete):
						#print("Broke out of loop at " + str(time.time() - t0) + "s")
						break
					if(time.time() - t0 > timeout):
						timedout = True
						break
				if(timedout):
					print("ACC never finished receiving data on " + str(timeout) + "s timeout")
					continue
				else:
					cmd = 0x000C0000 | (no + 1)
					self.write_usb(cmd)
					usb_buffer = self.read_usb(acdc_expected_length + usb_read_padding)
					#fill this buffer into the acdc object.
					#if it doesnt exist yet, create it!
					if(not(no in self.acdcs)):
						self.acdcs[no] = acdc.ACDC(no)
					error_codes[no] += self.acdcs[no].set_raw_data(usb_buffer)
					#print("Finished reading and parsing ACDC " + str(no) + " data")

		retval = self.print_error_codes(error_codes)

		return retval


	#sets LEDs to state 1 or 0 on all
	#boards.
	def set_leds_all(self, state):
		cmd = ''
		if(state == 1):
			cmd = 0x1eA0001
		else:
			cmd = 0x1eA0000

		self.write_usb(cmd)



	#looks at user defined error codes from a dictionary
	#indexed by board number. Prints what they mean. 
	def print_error_codes(self, error_codes):
		retval = 0 #a count of number of codes overall
		for no in error_codes:
			ids = error_codes[no]
			if(len(ids) == 0):
				continue

			print("Errors on board " + str(no) + " : ")
			ids = sorted(ids)
			for code in ids:
				retval += 1
				print("---- ", end='')
				if(code == 1):
					print("Did not receive the same number of psec-data start words as metadata start words. See acdc::set_raw_data")
				elif(code == 10):
					print("Did not find end word in ACDC psec buffer following the last metadata end word. See acdc::set_raw_data")
				elif(code == 2):
					print("Did not receive the same number of metadata startwords as metadata end words. See acdc::set_raw_data")
				elif(code == 3):
					print("Did not get the number of expected chips worth of metadata")
				elif(code == 4):
					print("Did not get the number of expected chips worth of waveform data")

		return retval

         
    #checks fidelity of fake data
    #generated at the ACDC firmware level.
    #Expects that ACDCs generate sequential integers
    #as its PSEC data, restarting at 0 at each chip. 
	def check_sum(self):
		bad_buffers = 0 #a count of how many bad buffers arrived. 
		for no in self.acdcs:
			bad_buffers += self.acdcs[no].check_sum()

		return bad_buffers





      