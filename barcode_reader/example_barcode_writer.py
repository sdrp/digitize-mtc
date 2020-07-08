import argparse
import barcode
from barcode.writer import ImageWriter
"""
Simple program to save output to a barcode. 
Very fragile - it creates a *.png file with the same
name as the coded value - so if you include characters
that aren't valid filename characters it might break :-)

"""
ap = argparse.ArgumentParser()
ap.add_argument("-c",
				"--code",
				required=True,
				help="Value to encode in barcode")

args = vars(ap.parse_args())

code = args["code"]


def write_barcode(coded_value):
    code128 = barcode.get_barcode_class('Code128')
    bc = code128(coded_value, writer=ImageWriter())
    fullname = bc.save('code_128_' + coded_value)
    print(f'Barcode saved to {fullname} ')

write_barcode(code)

