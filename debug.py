import acc
import sys


#input is
#python debug.py 1e0C0005 1e0C0000 <1/0>
#no leading 0x. 
if __name__ == "__main__":
	msg = sys.argv[1:]
	if(len(msg) == 0):
		#return do nothing
		sys.exit()

	a = acc.ACC() #opens serial port. 

	#if only one command, read option is default
	if(len(msg) == 1):
		a.debug(msg)
	else:
		#otherwise, last argument is integer
		#form of read option. 1 for read every write,
		#anything else is read only after all writing.
		a.debug(msg[:-1], int(msg[-1]))

	a.close()


