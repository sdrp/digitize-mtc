import unittest
from pyzbar import pyzbar
import random
import tempfile
import barcode as bc
from barcode.writer import ImageWriter
import cv2

IMAGE_NO_BARCODE   = "tests/admission_pg_1.jpeg"
IMAGE_WITH_BARCODE = "tests/admission_pg_with_barcode.jpeg"
IMAGE_WITH_PIH_BARCODE = "tests/Sample-PIH-Barcode.JPG"


class BarcodeTests(unittest.TestCase):

    def test_barcode_reader_no_barcodes(self):
        """
        Test that an image with no barcodes returns no barcodes.
        :return:
        """
        image = cv2.imread(IMAGE_NO_BARCODE)

        barcodes = pyzbar.decode(image)
        self.assertTrue(len(barcodes) == 0, "There are no barcodes in this image")

    def test_barcode_reader_one_barcode(self):
        """
        Test that an image with a single barcode returns the barcode; test
        the value of the returned barcode.
        :return:
        """
        image = cv2.imread(IMAGE_WITH_BARCODE)
        # find the barcode in the image and decode each of the barcode
        barcodes = pyzbar.decode(image)
        self.assertEqual(len(barcodes), 1, "There is one barcode in this image")
        barcode = barcodes[0]
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        self.assertEqual(barcodeType, "CODE128")
        self.assertEqual(barcodeData, "1234567890ABC")

    def test_pih_barcode(self):
        """
        Test a picture of a PIH barcode from PIH.

        Note that there are two barcodes on the picture; only one
        is picked up. Looks like it's selecting both codes?
        :return:
        """
        image = cv2.imread(IMAGE_WITH_PIH_BARCODE)
        # find the barcode in the image and decode each of the barcode
        barcodes = pyzbar.decode(image)
        self.assertEqual(len(barcodes), 1, "There is one barcode in this image")
        barcode = barcodes[0]
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        self.assertEqual(barcodeType, "CODE128")
        self.assertEqual(barcodeData, "2AC179")


    def test_barcode_writer(self):
        """
        Tests round trip:
        1. random string value is created
        2. a barcode is made from the random string
        3. the barcode is written to a temp file
        4. the temp file barcode is read
        5. the value of the parsed barcode is compared to the original.
        :return:
        """
        temp = tempfile.NamedTemporaryFile()
        code128 = bc.get_barcode_class('Code128')
        random_barcode_value = "RandomValue_" + \
                               str(random.randint(1000, 5000)) + \
                               ".jpeg"
        print(f'random_barcode_value {random_barcode_value}')
        new_barcode = code128(random_barcode_value, writer=ImageWriter())
        fullname = new_barcode.save(temp.name)
        print(f'fullname {fullname}')
        image = cv2.imread(fullname)
        barcodes = pyzbar.decode(image)
        self.assertEqual(len(barcodes), 1, "There is one barcode in this image")
        barcode = barcodes[0]
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        self.assertEqual(barcodeType, "CODE128")
        self.assertEqual(barcodeData, random_barcode_value)


if __name__ == '__main__':
    unittest.main()
