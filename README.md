# Digitize

**Automated digitization of paper medical records in low-resource healthcare settings.**

### 🌐 [Read our story and see the tool in action → sdrp.github.io/digitize-mtc](https://sdrp.github.io/digitize-mtc/)

Digitize is an open-source computer vision tool that turns a photograph of a filled-in
paper medical record into structured data — without redesigning the form, without an
internet connection, and without disrupting the way clinicians already work.

Our goal is to enable high-quality, sustainable medical data acquisition in settings
where electronic medical record systems are not feasible and clinical insight is needed
most. The tool has been piloted with the [Mae Tao Clinic](https://maetaoclinic.org/) on
the Thai–Burma border and with Mbuya Nehanda Maternity Hospital at the
[Parirenyatwa Group of Hospitals](https://parihosp.org/) in Zimbabwe.

![The review screen: checkboxes detected automatically, unresolved fields flagged in red](docs/img/pilot/digitiz-screenshot.png)

---

## Why we built this

Although free and open source medical record software exists, the vast majority of
clinics and hospitals in low-resource healthcare settings still rely on paper. A host of
barriers — from missing network infrastructure to concerns around staff adoption — ensure
that most health data stays trapped on the page. Without a way to digitize it, providers
cannot perform disease surveillance, improve resource allocation, or learn from past
outcomes.

The Mae Tao Clinic makes the problem concrete. Operating for 30 years in the middle of
the world's longest-running civil war, MTC provides essential care to migrants and
refugees along the Thai–Burma border, supporting over 33,000 deliveries and 136,000
antenatal care consultations in the last decade alone. Their Health Information System
holds over 1.1 million unique registrations — but because every row is typed in by hand,
only a small fraction of what is written on each paper record ever makes it into the
system.

Digitize targets exactly that gap: clinics that need health informatics but cannot
support a full EMR deployment.

## How it works

| # | Step | What happens |
|---|---|---|
| 1 | **Document care on paper** | Clinicians fill out the existing paper form exactly as they always have. |
| 2 | **Capture an image** | A webcam, document camera, flatbed scanner, or phone photo of the completed record. The server streams live frames and scores each one for alignment and blur, capturing automatically once the image is good enough. |
| 3 | **Automatic digitization** | The image is aligned against a blank template, then each response region is read. The clinician reviews the result and corrects anything wrong. |
| 4 | **Save** | The record is appended to a CSV in a structured format compatible with the clinic's existing Health Information System. The paper record is filed as usual. |

Under the hood, step 3 is:

- **Alignment** — ORB features (up to 5,000) are matched between the captured image and
  the blank template, and a RANSAC homography warps the capture into template space
  (`backend/scripts/align.py`). A per-region finetuning pass corrects local drift.
- **Quality gating** — a variance-of-Laplacian blur score and an alignment score reject
  bad frames before processing (`backend/scripts/detect_blurriness.py`).
- **Mark recognition** — each checkbox and radio region is scored by ink density against
  tuned thresholds and resolved to checked / empty / unknown (`backend/scripts/omr.py`).
- **Review** — everything the tool could not resolve on its own is surfaced in the web UI
  for the clinician to fill in, rather than silently guessed at.

## What it can do today

This is an honest snapshot of the current implementation, which is more limited than the
vision described on the project website.

| Field type | Status |
|---|---|
| Checkboxes | ✅ Detected automatically |
| Radio buttons / multiple choice | ✅ Detected automatically |
| Handwritten digits | ⚠️ Region located and cropped, but flagged for manual entry |
| Free text | ⚠️ Region located and cropped, but flagged for manual entry |

An MNIST digit classifier (`backend/scripts/model.onnx`, with segmentation in
`digit_segmentation.py`) was built and evaluated, but the inference path in
`backend/scripts/mnist.py` is **currently commented out**, so `digits` questions fall
through to the same manual-entry path as free text. Handwriting recognition with
best-in-class open source models is the main focus of the next major revision — see
[Roadmap](#roadmap).

Four form templates ship with the repo: `antenatal`, `delivery`, `admission`, and
`covid` (`backend/forms/json_annotations/`).

## Getting started

Requires **Python 3**.

```bash
pip3 install Pillow numpy scikit-image opencv-contrib-python flask
```

If you plan to plug in an external UVC USB camera for the live alignment feature, install
`opencv-contrib-python` specifically — the package published as `opencv-contrib` does not
provide video device support through OpenCV.

Then start the server from the repository root:

```bash
python3 backend/server.py
```

It opens a browser at `http://localhost:8000` automatically.

### Options

| Flag | Default | Purpose |
|---|---|---|
| `--port` | `8000` | Port to serve on |
| `--camera_index` | `0` | OpenCV device index — use `1` for an external camera on most machines |
| `--upload_folder` | `backend/uploads` | Where captured images are written |
| `--save-debug` | off | Write diagnostic images and JSON for every capture |

## Adding your own forms

A form template is a JSON file in `backend/forms/json_annotations/` paired with a clean
scan of the blank form in `backend/forms/template_images_v2/`. The JSON describes a
`Form` → `QuestionGroup` → `Question` → `ResponseRegion` hierarchy, where each response
region is a labelled bounding box on the template image, and each question carries a type
(`checkbox`, `radio`, `text`, `digits`). See `backend/scripts/form.py` for the data model.

New templates must currently be added to the list in `upload_all_templates()` in
`backend/server.py` to be picked up.

## Running tests

```bash
cd backend/tests/
python3 test_end_to_end.py --INPUT_FILE test_sets/pih/admission.csv
```

To generate new test cases, run the server in debug mode with your camera and output
directory, then scan records as usual:

```bash
python3 backend/server.py --save-debug --camera_index 1 --upload_folder [upload_folder]
```

## Repository layout

```
backend/
  server.py            Flask routes, live camera feed, alignment loop
  app.py               App config and folder setup
  scripts/
    process.py         The digitization pipeline, end to end
    align.py           ORB + RANSAC homography alignment
    omr.py             Checkbox / radio mark recognition
    form.py            Form / Question / ResponseRegion data model
    encoder.py         JSON serialization of form objects
    webcam.py          Threaded OpenCV capture
    detect_blurriness.py
    digit_segmentation.py, mnist.py, model.onnx   (digit model, currently disabled)
  forms/               Form templates, template images, example records
  templates/           Jinja templates for the web UI
  tests/               End-to-end test harness and test sets
docs/                  Project website (GitHub Pages)
scratch/               Prototypes and abandoned experiments — not part of the app
```

## Roadmap

The project is being revived, with the following priorities:

- **Camera interface** — device enumeration and selection so the tool works with a
  built-in webcam or any plugged-in USB camera, instead of a hardcoded index.
- **Frame streaming** — replace the MJPEG-over-`multipart` loop with a lower-latency
  path to the frontend.
- **Handwriting and mark recognition** — replace the disabled MNIST model with modern
  best-in-class open source OCR/HTR for handwritten fields and more robust checkbox
  detection.

## Publication

Perera S, Maung C, Hla S, Moo Moo H, Than Lwin S, Bruck C, et al.
*Access to community-based reproductive health services and incidence of low birthweight
delivery among refugee and displaced mothers: a retrospective study in the
Thailand-Myanmar border region.*
**BMJ Open**, 31 Jan 2022. [PubMed 35105627](https://pubmed.ncbi.nlm.nih.gov/35105627/)

The digitized data in this study was used to demonstrate the relationship between
antenatal care access and maternal health outcomes, and to advocate for additional
funding amidst the ongoing migrant and refugee crisis in the region.

## Team

| Name | Role | Affiliation |
|---|---|---|
| **Sudheesha Perera** | Resident Physician | Yale School of Medicine |
| **Daniel Kunin** | Postdoctoral Researcher | University of California, Berkeley |
| **Jingru Guo** | UX Designer | Formerly Rhode Island School of Design |
| **Hamish Fraser** | Associate Professor | Brown University; Founder of OpenMRS |
| **Cynthia Maung** | Founder and Director | Mae Tao Clinic |
| **Sophia Hla** | Deputy Director of Medical Services | Mae Tao Clinic |
| **Hsa Moo Moo** | Health Information System Manager | Mae Tao Clinic |
| **Neil Sarkar** | President and CEO | Rhode Island Quality Institute |

## Acknowledgements

Made possible by funding from the [Brown Data Science Initiative](https://dsi.brown.edu/),
the [Brown Global Health Initiative](https://globalhealth.brown.edu/), and private donors.
We are grateful for mentorship and support from
[Harvard Innovation Labs](https://innovationlabs.harvard.edu/), the team at
[OpenMRS](https://openmrs.org/), faculty at the
[Brown Center for Biomedical Informatics](https://bcbi.brown.edu/), the
[African Neonatal Association](https://africanneonatal.org/), and above all our partners
in Thailand and Zimbabwe.
