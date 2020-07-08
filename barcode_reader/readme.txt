
Barcode reader
https://www.pyimagesearch.com/2018/05/21/an-opencv-barcode-and-qr-code-scanner-with-zbar/
Barcode writer library:
https://pypi.org/project/python-barcode/

To Install:

1. brew install zbar
2. pip install -r requirements.txt

(you might need to use pip3 - on my machine pip uses python3).

Test installation:

python test_barcode.py
(runs four trivial unit tests)

Parse barcodes (a small testing app)
Example of a form with a pasted-in barcode
python example_barcode_reader.py -i tests/admission_pg_with_barcode.jpeg

Example of a form with no barcode
python example_barcode_reader.py -i tests/admission_pg_1.jpeg

Example using PIH photo of barcode
python example_barcode_reader.py -i tests/Sample-PIH-Barcode.JPG
[Need to look at this more - there are multiple barcodes here]

Example creating a barcode file
python example_barcode_writer.py -c "blah"
(will create file 'code_128_blah.png').








