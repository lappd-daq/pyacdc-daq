import acc
import sys


#input is
#python debug.py 1e0C0005 1e0C0000 <1/0>
#no leading 0x. 
if __name__ == "__main__":

	a = acc.ACC() #opens serial port. 
	testboards = [0]
	a.send_soft_trigger(testboards)
	a.read_acdc()
	a.close()



