import usb.core
import usb.util
import time
import sys
import usb_device as usbdev

class ACC:
   def __init__(self):
      self.max_N = 8 #max number of boards.
      
      #usb device connected to ACC
      self.dev = usb.core.find(idVendor=usbdev.VID, idProduct=usbdev.PID)
      if self.dev is None:
         print("The ACC cannot be reached by USB communications.")
         sys.exit()

      self.dev.set_configuration()
      self.dev.reset()

      self.raw_acc_info = [] #raw info buffer of ACC, no dictionary indexing.
      self.acc_info = {} #info buffer of ACC from 1e0C0005, string dictionary

      

   
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
         print("Sending command: ", end='')
         print([hex(_) for _ in packet])
         self.dev.write(usbdev.EDPNT_WR, packet)
      except:
         print("Error in writing to usb line: ", end='')
         print(packet)

   def print_rx_data(self, ret):
      print("Read back " + str(len(ret)) + " 32-bit words: ")
      for i, word in enumerate(ret):
         print(str(i)+" " + hex(word))


   #a debug function that
   #takes a string msg from input
   #and converts to the necessary format
   #to send down the line and read as we go.
   #if read_option is 1, reads at each command.
   #otherwise, only reads at the end.
   def debug(self, msg, read_option=0):
      num_words = 100 #number of 16 bit words to read on usb line.
      for m in msg:
         self.write_usb(int(m, 16))

         if(read_option == 1):
            ret = self.read_usb(num_words)
            self.print_rx_data(ret)

      ret = self.read_usb(num_words)
      self.print_rx_data(ret)





   def read_acc(self):
      acc_buffer_length = 64 #16 bit words
      msg = "1e0c0005"
      self.write_usb(int(msg, 16))
      packet = self.read_usb(acc_buffer_length)
      self.raw_acc_info = packet
      #check for errors
      if(packet[0] != int("1234", 16) or packet[1] != int("dead", 16)):
         print("ACC returned bad info on itself")
         return


      #form dictionary for each word. 
      self.acc_info["link_status"] = packet[2]



   def read_acdc(self):
      #first get a fresh ACC info buffer to 
      #check which ACDCs look connected.
      self.read_acc()

      connected_acdcs = [] #list of ints correpsonding to acdc addresses
      for i in range(self.max_N):
         if(self.acc_info["link_status"] & (1 << i)):
            connected_acdcs.append(i)


      #send a software trigger signal
      board_mask = 0
      trigbin = 0
      for no in connected_acdcs:
         board_mask += (1 << no)
      cmd = int("000E0000", 16) | board_mask | (trigbin << 4)
      self.write_usb(cmd)

      for no in connected_acdcs:
         print("Link is up for ACDC " + str(no))
         cmd = int("1e0c0000", 16) | (no + 1)
         self.write_usb(cmd)
         time.sleep(0.1) #remove this in actual implementation. 
         packet = self.read_usb(20)
         print("Beginning of the data packet: ", end='')
         print(packet[:20])




   #sets LEDs to state 1 or 0 on all
   #boards.
   def set_leds_all(self, state):
      cmd = ''
      if(state == 1):
         cmd = "1e0A0001"
      else:
         cmd = "1e0A0000"

      cmd = int(cmd, 16)
      self.write_usb(cmd)

   



         





      