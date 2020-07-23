import time
import sys
from comms_defs import * #all word definitions

class ACDC:
   def __init__(self, no):
      self.no = no #board number matching index of acc port. 
      self.raw_data_buffer = [] #from a raw data read

      #lists of 256 length indexed by channel number
      #representing psec waveform data
      self.channel_data = {} 

      #string indexed info dictionary
      #containing metadata. Has board configuration
      #during the data query, which is often an "event".
      #also contains "event" metadata.  
      self.metadata = {} 

      self.nchips = 5 #number of psec chips
      self.nchans = 30
      self.nsamps = 256


   def get_no(self):
      return self.no

   #takes a raw data buffer from USB
   #at ACC class and parses it into dictionary
   #objects.
   #returns codes indicating what kind of
   #failure modes occurred. 
   def set_raw_data(self, usb_buffer):
      self.raw_data_buffer = usb_buffer
      error_codes = [] #can be multiple issues with the buffer. 

      #find indices of 0xF005 words
      t0 = time.time()
      psec_start_indices = [i for i,j in enumerate(usb_buffer) if j == psec_frame_start]
      print("Finding start indices took " + str(time.time() - t0))
      #find indices of 0xBA11 words
      t0 = time.time()
      psec_end_indices = [i for i,j in enumerate(usb_buffer) if j == psec_postamble_start]
      psec_end_indices = [i for i in psec_end_indices if usb_buffer[i-1] != psec_postamble_start]
      print("Finding end indices took " + str(time.time() - t0))
      #find indices of end of metadata
      t0 = time.time()
      metadata_end_indices = [i for i,j in enumerate(usb_buffer) if j == metadata_end_word]
      print("Finding metadata indices took " + str(time.time() - t0))

      #index of end of buffer. defines where self trigger data lives. 
      end_index = [i for i,j in enumerate(usb_buffer[metadata_end_indices[-1]:]) if j == endword]
      if(len(end_index) == 0):
         error_codes.append(10)

      end_index = end_index[0]

      #error checking on flag word sequence. 
      if(len(psec_end_indices) != len(psec_start_indices)):
         print(len(psec_end_indices))
         print(len(psec_start_indices))
         error_codes.append(1)
         return error_codes
      if(len(psec_end_indices) != len(metadata_end_indices)):
         print(len(psec_end_indices))
         print(len(metadata_end_indices))
         error_codes.append(2)
         return error_codes

      datablocks = [[psec_start_indices[i], psec_end_indices[i]] for i in range(len(psec_end_indices))]
      metadata_blocks = [[psec_end_indices[i] + 1, metadata_end_indices[i]] for i in range(len(psec_end_indices))]
      
      if(len(metadata_blocks) != self.nchips):
         error_codes.append(3)
      if(len(datablocks) != self.nchips):
         error_codes.append(4)

      t0 = time.time()
      #put metadata into chipwise blocks
      for psec, block in enumerate(metadata_blocks):
         if(not(psec in self.metadata)):
            self.metadata[psec] = []

         self.metadata[psec] = usb_buffer[block[0]+1:block[-1]]

      print("Storing metadata took " + str(time.time() - t0))

      #put chip data into channel blocks. 
      channel = 1
      t0 = time.time()
      for psec, block in enumerate(datablocks):
         chip_data = usb_buffer[block[0]+1:block[-1]]
         for i in range(int(self.nchans/self.nchips)):
            self.channel_data[channel] = chip_data[i*self.nsamps:(i+1)*self.nsamps]
            channel += 1
      print("Storing waveform data took " + str(time.time() - t0))

      return error_codes



   def write_buffer_to_file(self, buf):
      f = open("example_buffer.txt", "w")
      for k in buf:
         f.write(hex(k) + "\n")
      f.close()


   #checks fidelity of fake data
   #generated at the ACDC firmware level.
   #Expects that ACDCs generate sequential integers
   #as its PSEC data, restarting at 0 at each chip. 
   def check_sum(self):
      lastval = None
      expected_end = 1535
      expected_start = 0

      samplesum = 0
      for ch in self.channel_data:
         if(len(self.channel_data[ch]) != self.nsamps):
            print("Received not enough samples in channel : " + str(ch))
         
         samplesum += len(self.channel_data[ch])

      print(samplesum)

      for ch in self.channel_data:
         d = self.channel_data[ch]
         for i, n in enumerate(d):
            if(lastval is None):
               lastval = n
               if(lastval != expected_start):
                  print("1")
                  print(lastval)
                  print(ch)
                  return 1
               continue

            #standard check for sequentialism
            if(n - lastval > 1):
               print("2")
               print(n)
               print(lastval)
               print("Channel : " + str(ch))
               return 1

            #checking at the roll over of
            #1535 to 0. If it isnt 1535, we have
            #a problem. 
            if(n - lastval < 1):
               if(lastval != expected_end):
                  print("4")
                  print(lastval)
                  return 1
               lastval = None
               continue

            #otherwise, everything passes
            lastval = n


      return 0







