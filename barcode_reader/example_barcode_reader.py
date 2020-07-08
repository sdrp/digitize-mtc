from pyzbar import pyzbar
import argparse
import cv2
"""
Example code loads graphics file containing barcode.
If barcodes are found - the graphic is displayed and a rectangle is
displayed around the bar code. The values are printed to stdout.

If no barcodes are found - a message is written to std out.

To exit the program - hit any key when the graphic window is displayed. 
(otherwise you have to kill it explicitly).
"""
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i",
				"--image",
				required=True,
				help="path to input image")

args = vars(ap.parse_args())

filename = args["image"]
# load the input image
image = cv2.imread(filename)
# find the barcodes in the image and decode each of the barcodes
barcodes = pyzbar.decode(image)

print(f'barcodes {barcodes}')
# loop over the detected barcodes
for barcode in barcodes:
	# extract the bounding box location of the barcode and draw the
	# bounding box surrounding the barcode on the image
	(x, y, w, h) = barcode.rect
	cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
	# the barcode data is a bytes object so if we want to draw it on
	# our output image we need to convert it to a string first
	barcodeData = barcode.data.decode("utf-8")
	barcodeType = barcode.type
	# draw the barcode data and barcode type on the image
	text = "{} ({})".format(barcodeData, barcodeType)
	cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.5, (0, 0, 255), 2)
	# print the barcode type and data to the terminal
	print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
# show the output image
if len(barcodes) > 0:
	print(f'About to display {len(barcodes)} bar codes. Enter \'q\' key to exit.')
	cv2.namedWindow("BarcodeDisplay", cv2.WINDOW_KEEPRATIO)
	cv2.imshow("BarcodeDisplay", image)
	wait_time = 1000
	while cv2.getWindowProperty('BarcodeDisplay', cv2.WND_PROP_VISIBLE) >= 1:
		keyCode = cv2.waitKey(wait_time)
		if (keyCode & 0xFF) == ord("q"):
			cv2.destroyAllWindows()
			break
else:
	print(f'No barcodes found for image {filename}')
