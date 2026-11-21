"""
Optional OpenCV + YOLO camera demo.
Install: pip install opencv-python ultralytics
Run: python camera_detect.py
This detects general COCO objects (e.g. bottle, cup, person), NOT exact retail
SKUs. Train a custom model on your own product images for product-level matching.
"""
import cv2
try:
    from ultralytics import YOLO
except ImportError:
    raise SystemExit("Install dependencies first: pip install opencv-python ultralytics")

model = YOLO("yolov8n.pt")  # downloads a small pretrained model on first run
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Could not open webcam. Check camera permissions/index.")

print("Press Q to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        break
    results = model.predict(frame, conf=0.45, verbose=False)
    annotated = results[0].plot()
    cv2.imshow("SmartCart - Camera Object Detection", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
