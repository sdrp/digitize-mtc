# Digitiz
an OMR tool that automates data extraction from paper medical records


Dependencies
============
- Python 3
- Python Imaging Library (PIL) (``python3-pil``, distributed as part of ``python3-Pillow``)
- Python lxml (``python3-lxml``)
- NumPy (``python3-numpy``)
- SciPy (``python3-scipy``)
- scikit-image (``scikit-image``)
- opencv (``opencv-contrib-python``)
- onnxruntime (``onnxruntime``)
- pathlib (``pathlib``)
- flask (``flask``)

All of these can be installed used `pip` or `conda`. If you are planning to plug in
an external UVC-enabled USB camera to use the live alignment feature, make sure
to download ``opencv-contrib-python``, since the package hosted under
``opencv-contrib`` does not provide video device support via OpenCV.


Getting Started
===============
Start the server using the following line:

```
python3 backend/server.py
```

Running Tests
=============
To run a test suite, first navigate to `backend/tests` and run the `test_end_to_end.py` script 
on the desired test set. For example, to run PIH Admission test set execute the following commands
from the repository root:

```
cd backend/tests/
python3 test_end_to_end.py --INPUT_FILE test_sets/pih/admission.csv
```

Generating New Tests
====================
To generate new test cases from each scanned record run the server in debug mode, making sure to 
specify your desired camera and output directory. For example:
```
python3 backend/server.py --save-debug --camera_index 1 --upload_folder [upload_folder]
```
...where `[upload_folder]` is the absolute path to the directory into which the server should 
write all new test files. 



Find Out More
=============
Find out more about our project and vision at https://sdrp.github.io/digitize-mtc/.
