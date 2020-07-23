import acc
import sys


#input is
#python debug.py 1e0C0005 1e0C0000 <1/0>
#no leading 0x. 
if __name__ == "__main__":

	#arg parsing
	#only take the first argument
	usage = "Usage: python set_led.py <on/off or 1/0>"
	if(len(sys.argv) < 2):
		print(usage)
		sys.exit()
	tog = sys.argv[1]
	#trim whitespace and lowercase.
	tog = ''.join(c.lower() for c in tog if not c.isspace()) 
	led_state = None
	if(tog == "on" or tog == "1"):
		led_state = 1
	elif(tog == "off" or tog == "0"):
		led_state = 0
	else:
		print(usage)
		sys.exit()



	a = acc.ACC() #opens serial port. 
	a.set_leds_all(led_state)
	a.close()


