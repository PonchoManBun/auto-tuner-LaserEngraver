"""List available cameras using different methods."""
import cv2

print("Testing camera indices with different backends...\n")

backends = [
    ("CAP_DSHOW (DirectShow)", cv2.CAP_DSHOW),
    ("CAP_MSMF (Media Foundation)", cv2.CAP_MSMF),
    ("CAP_ANY (Auto)", cv2.CAP_ANY),
]

for backend_name, backend in backends:
    print(f"=== {backend_name} ===")
    for i in range(3):
        cap = cv2.VideoCapture(i, backend)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ret, frame = cap.read()
            print(f"  Index {i}: OPEN ({w}x{h}) - Frame captured: {ret}")
            cap.release()
        else:
            print(f"  Index {i}: closed")
    print()
