import torch
import matplotlib
matplotlib.use("Agg")

from pytorch_grad_cam import EigenCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

from disease_knowledge import get_disease_details, DISEASE_KNOWLEDGE
from scan_history import save_scan, get_dashboard_data
from uuid import uuid4
import cv2
import supervision as sv
from ultralytics import YOLO
import numpy as np
from flask import Flask, request, render_template, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
import logging
import time
import csv
import io
from flask import Response, abort
from scan_history import connect

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the YOLO model
try:
    model = YOLO("best.pt")  # Ensure this model is trained on the 9 classes
    logger.info("YOLO model loaded successfully")
    logger.info(f"Model class names: {model.names}")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    raise

# Define color map for the 9 classes using RGB values, matching the model's class names
COLOR_MAP = {
    "Blight": sv.Color(255, 0, 0),      # Red
    "Brown Spot": sv.Color(0, 0, 255),  # Blue
    "False Smut": sv.Color(0, 255, 0),  # Green
    "Healthy": sv.Color(255, 255, 0),   # Yellow
    "Leaf Smut": sv.Color(128, 0, 128), # Purple
    "Rice blast": sv.Color(255, 165, 0),# Orange
    "Stem Rot": sv.Color(255, 0, 255),  # Magenta
    "Tungro": sv.Color(0, 255, 255),    # Cyan
    "Background": sv.Color(255, 255, 255)# White
}

def generate_eigen_cam(image):
    """Generate EigenCAM overlay for a YOLO image."""
    try:
        cam_model = model.model
        cam_model.eval()

        target_layers = [cam_model.model[-2]]

        cam = EigenCAM(
            model=cam_model,
            target_layers=target_layers
        )

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w = rgb_image.shape[:2]

        rgb_image = cv2.resize(
            rgb_image,
            (640, 640),
            interpolation=cv2.INTER_LINEAR
        )

        rgb_image = rgb_image.astype(np.float32) / 255.0

        input_tensor = torch.from_numpy(
            np.transpose(rgb_image, (2, 0, 1))[None, :]
        ).float()

        grayscale_cam = cam(
            input_tensor=input_tensor,
            targets=[None]
        )[0]

        cam_image = show_cam_on_image(
            rgb_image,
            grayscale_cam,
            use_rgb=True
        )

        cam_image = cv2.resize(
            cam_image,
            (w, h),
            interpolation=cv2.INTER_LINEAR
        )

        return cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR)

    except Exception as e:
        logger.error(f"EigenCAM generation failed: {e}")
        return None

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path):
    """Process an image for crop disease detection."""
    try:
        logger.info(f"Processing image: {image_path}")
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error("Failed to load image")
            return None, "Error: Could not load image", {}, None, []

        # Resize image for consistent processing
        target_width, target_height = 1280, 720
        image = cv2.resize(image, (target_width, target_height))
        logger.info("Image resized successfully")

        # Run YOLO detection
        results = model(image)[0]
        detections = sv.Detections.from_ultralytics(results)
        logger.info("YOLO detection completed")

        # Log detections and count diseases
        disease_counts = {}
        if len(detections) > 0:
            for class_id in detections.class_id:
                class_name = results.names[class_id]
                disease_counts[class_name] = disease_counts.get(class_name, 0) + 1
            logger.info(f"Detected diseases: {disease_counts}")
        else:
            logger.info("No diseases detected")

        detection_records = [
            {"class": results.names[int(class_id)], "confidence": round(float(confidence), 4)}
            for class_id, confidence in zip(detections.class_id, detections.confidence)
        ]

        # Assign colors to detections based on class names
        if len(detections) > 0:
            colors = []
            for class_id in detections.class_id:
                class_name = results.names[class_id]
                color = COLOR_MAP.get(class_name, sv.Color(128, 128, 128))  # Default to gray if class not in COLOR_MAP
                colors.append(color)
        else:
            colors = []

        # Annotate image with bounding boxes and labels
        annotated_image = image.copy()
        if len(detections) > 0:
            # Draw bounding boxes and labels for each detection with its corresponding color
            for detection_idx, (xyxy, color) in enumerate(zip(detections.xyxy, colors)):
                # Create a single-detection object for this iteration
                single_detection = sv.Detections(
                    xyxy=np.array([xyxy]),
                    class_id=np.array([detections.class_id[detection_idx]]),
                    confidence=np.array([detections.confidence[detection_idx]])
                )

                # Initialize annotators with the specific color for this detection
                box_annotator = sv.BoxAnnotator(color=color)
                label_annotator = sv.LabelAnnotator(
                    color=color,
                    text_color=sv.Color(255, 255, 255),  # White text for better contrast
                    text_position=sv.Position.TOP_LEFT
                )

                # Annotate bounding box
                annotated_image = box_annotator.annotate(
                    scene=annotated_image,
                    detections=single_detection
                )

                # Annotate label with class name and confidence
                labels = [f"{results.names[single_detection.class_id[0]]}: {single_detection.confidence[0]:.2f}"]
                annotated_image = label_annotator.annotate(
                    scene=annotated_image,
                    detections=single_detection,
                    labels=labels
                )

        # Add disease count overlay on the image
        y_offset = 30
        for disease, count in disease_counts.items():
            text = f"{disease}: {count}"
            cv2.putText(
                annotated_image, text, (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
            y_offset += 30

        # Save annotated detection image
        timestamp = f'{int(time.time())}_{uuid4().hex[:8]}'

        output_filename = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f'output_{timestamp}.jpg'
        )
        cv2.imwrite(output_filename, annotated_image)

        output_path = f'uploads/output_{timestamp}.jpg'

        # Generate EigenCAM image
        # Generate EigenCAM image
        xai_image = generate_eigen_cam(image)

        # Overlay YOLO detection boxes on the EigenCAM image
        if xai_image is not None and len(detections) > 0:
            for detection_idx, (xyxy, color) in enumerate(zip(detections.xyxy, colors)):
                x1, y1, x2, y2 = map(int, xyxy)

                # Convert supervision color to OpenCV BGR
                bgr_color = (0, 255, 255)

                cv2.rectangle(
                    xai_image,
                    (x1, y1),
                    (x2, y2),
                    bgr_color,
                    2
                )

                class_id = detections.class_id[detection_idx]
                class_name = results.names[class_id]
                confidence = detections.confidence[detection_idx]

                label = f"{class_name}: {confidence:.2f}"

                cv2.putText(
                    xai_image,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    bgr_color,
                    2
                )

        xai_path = None

        if xai_image is not None:
            xai_filename = os.path.join(
                app.config['UPLOAD_FOLDER'],
                f'xai_{timestamp}.jpg'
            )

            cv2.imwrite(xai_filename, xai_image)
            xai_path = f'uploads/xai_{timestamp}.jpg'

        logger.info(f"Annotated image saved: {output_path}")
        logger.info(f"EigenCAM image saved: {xai_path}")

        return output_path, None, disease_counts, xai_path, detection_records


    except Exception as e:

        logger.error(f"Error processing image: {e}")

        return None, f"Error: {str(e)}", {}, None, []

@app.route('/dashboard')
def dashboard():
    """Read-only overview of loaded model capabilities."""
    return render_template('dashboard.html', model_classes=list(model.names.values()), analytics=get_dashboard_data())

@app.route('/dashboard/knowledge')
def disease_library():
    return render_template('disease_library.html', diseases=DISEASE_KNOWLEDGE)

@app.route('/dashboard/export.csv')
def export_scans():
    """Export actual locally stored scan records as CSV."""
    analytics = get_dashboard_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp UTC', 'Status', 'Detected labels', 'Average confidence (%)', 'Image path'])
    for scan in analytics['scans']:
        writer.writerow([scan['id'], scan['scanned_at'], scan['health_status'],
                         scan['detected'], scan['avg_confidence'] if scan['avg_confidence'] is not None else '',
                         scan['image_path']])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=agrovision_scans.csv'})

@app.route('/dashboard/report/<int:scan_id>')
def scan_report(scan_id):
    """Printable scan report, with browser Save as PDF support."""
    import json
    with connect() as db:
        row = db.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    if row is None:
        abort(404)
    scan = dict(row)
    scan['counts'] = json.loads(scan['disease_counts'])
    scan['detections_list'] = json.loads(scan['detections'] or '[]')
    return render_template('scan_report.html', scan=scan)

@app.route('/favicon.ico')
def favicon():
    """Serve a favicon to eliminate 404 errors."""
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload and display results."""
    error = None
    output_image = None
    original_image = None
    xai_image = None
    disease_summary = {}
    disease_details = []
    plant_health_status = "inconclusive"

    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            error = 'No file part'
            logger.error(error)
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'No selected file'
                logger.error(error)
            elif file and allowed_file(file.filename):
                filename = f'{uuid4().hex}_{secure_filename(file.filename)}'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logger.info(f"File uploaded: {filepath}")

                # Process the image
                output_path, processing_error, disease_counts, xai_path, detection_records = process_image(filepath)

                if processing_error:
                    error = processing_error
                    logger.error(f"Image processing failed: {processing_error}")

                else:
                    output_image = url_for('static', filename=output_path)
                    original_image = url_for('static', filename=f'uploads/{filename}')

                    if xai_path:
                        xai_image = url_for('static', filename=xai_path)

                    disease_summary = disease_counts

                    # Determine overall plant health status
                    detected_diseases = [
                        name for name, count in disease_summary.items()
                        if count > 0 and name.lower() not in ["healthy", "background"]
                    ]

                    healthy_count = disease_summary.get("Healthy", 0)

                    if detected_diseases:
                        plant_health_status = "disease"

                    elif healthy_count > 0:
                        plant_health_status = "healthy"

                    else:
                        plant_health_status = "inconclusive"

                    # Get information about detected diseases
                    disease_details = get_disease_details(disease_summary)

                    try:
                        save_scan(f'uploads/{filename}', output_path, xai_path,
                                  plant_health_status, disease_summary, detection_records)
                    except Exception:
                        logger.exception('Scan completed, but history could not be saved')

    return render_template(
        "index.html",
        error=error,
        output_image=output_image,
        original_image=original_image,
        xai_image=xai_image,
        disease_summary=disease_summary,
        disease_details=disease_details,
        plant_health_status=plant_health_status
    )
if __name__ == '__main__':
    # Disable Flask auto-reloading to prevent interruptions
    app.run(debug=True, use_reloader=False)