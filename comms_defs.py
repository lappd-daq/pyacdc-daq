startword = 0x1234
endword = 0x4321
acc_frame_start = 0xDEAD
acc_frame_end = 0xBEEF
psec_frame_start = 0xF005
psec_postamble_start = 0xBA11
metadata_end_word = 0xFACE

acdc_expected_length = 16002 #16 bit words, 8001 32 bit words
acc_expected_length = 64 #16 bit words
usb_read_padding = 30 #30 extra 16 bit words in case of overflow. 