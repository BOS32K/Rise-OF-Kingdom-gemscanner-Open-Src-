import sys
import time
import threading
import numpy as np
import mss
import cv2
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QRect
import win32gui
import win32process
import psutil
from ultralytics import YOLO

# === 設定 ===
PROCESS_NAME = "MASS.exe"
import sys
import time
import threading
import numpy as np
import mss
import cv2
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QRect
import win32gui
import win32process
import psutil
from ultralytics import YOLO
import os

# === 設定 ===
PROCESS_NAME = "MASS.exe"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "gem.pt") #把gem.bt放在 main.py 同一目錄
CONFIDENCE_THRESHOLD = 0.5
IMG_SIZE = 832
BOX_TIMEOUT = 0.5
NAMES = {0: 'gem'}
COLORS = {0: (0, 255, 255)}

# === 尋找視窗 ===
def find_hwnd_by_process_name(process_name):
    target_hwnd = None
    def enum_callback(hwnd, _):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                if psutil.Process(pid).name().lower() == process_name.lower():
                    target_hwnd = hwnd
            except:
                pass
    win32gui.EnumWindows(enum_callback, None)
    return target_hwnd

# === Overlay 視窗 ===
class OverlayWindow(QWidget):
    def __init__(self, hwnd, model):
        super().__init__()
        self.hwnd = hwnd
        self.model = model
        self.boxes = []
        self.boxes_lock = threading.Lock()
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 0
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAutoFillBackground(False)
        self.follow_timer = QTimer()
        self.follow_timer.timeout.connect(self.update_geometry)
        self.follow_timer.start(16)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_fps)
        self.refresh_timer.start(1000 // 60)
        threading.Thread(target=self.run_detection_loop, daemon=True).start()
        self.show()

    def update_geometry(self):
        if not win32gui.IsWindow(self.hwnd):
            print("❌ MASS.exe 視窗已關閉")
            sys.exit()
        rect = win32gui.GetWindowRect(self.hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return
        self.left, self.top, self.right, self.bottom = left, top, right, bottom
        self.setGeometry(self.left, self.top, width, height)

    def update_fps(self):
        self.frame_count += 1
        now = time.time()
        if now - self.last_time >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.last_time = now
        self.update()

    def run_detection_loop(self):
        with mss.mss() as sct:
            while True:
                # === 取得最新的 MASS.exe 視窗座標 ===
                if not win32gui.IsWindow(self.hwnd):
                    print("❌ MASS.exe 視窗已關閉")
                    sys.exit()

                rect = win32gui.GetWindowRect(self.hwnd)
                left, top, right, bottom = rect
                width = right - left
                height = bottom - top

                if width <= 0 or height <= 0:
                    time.sleep(0.1)
                    continue

                # === 強制更新 overlay 的位置 ===
                self.move(left, top)
                self.resize(width, height)
                # === 擷取最新畫面 ===
                monitor = {"top": top, "left": left, "width": width, "height": height}
                try:
                    frame = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                except Exception as e:
                    print(f"⚠️ 擷取畫面失敗: {e}")
                    time.sleep(0.1)
                    continue

                # === YOLO 推論 ===
                results = self.model.predict(frame, imgsz=IMG_SIZE, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
                now = time.time()
                new_boxes = []

                # === 計算縮放比例（根據實際抓圖大小）===
                orig_h, orig_w = frame.shape[:2]
                scale_x = width / orig_w
                scale_y = height / orig_h
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls_id not in COLORS:
                        continue
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)
                    new_boxes.append((x1, y1, x2, y2, cls_id, conf, now))
                with self.boxes_lock:
                    if new_boxes:
                        self.boxes = new_boxes
                time.sleep(0.005)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        now = time.time()
        valid_boxes = []

        with self.boxes_lock:
            for x1, y1, x2, y2, cls_id, conf, last_seen in self.boxes:
                if now - last_seen <= BOX_TIMEOUT:
                    pen = QPen(QColor(255, 0, 0), 4)
                    painter.setPen(pen)
                    painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                    label = "gem"
                    font_size = 20
                    font = QFont()
                    font.setPointSize(font_size)
                    painter.setFont(font)
                    text_width = painter.fontMetrics().width(label) + 10
                    text_height = painter.fontMetrics().height()
                    text_x = x1 + 5
                    text_y = y1 - 10
                    bg_rect = QRect(text_x - 2, text_y - text_height + 2, text_width, text_height)
                    painter.setBrush(QColor(0, 0, 255, 180))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(bg_rect)
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(text_x, text_y, label)
                    valid_boxes.append((x1, y1, x2, y2, cls_id, conf, last_seen))
            self.boxes = valid_boxes
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 20, f"FPS: {self.current_fps}")

# === 主程式 ===
if __name__ == '__main__':
    hwnd = find_hwnd_by_process_name(PROCESS_NAME)
    if not hwnd:
        print(f"❌ 找不到 {PROCESS_NAME} 視窗，請先開啟遊戲")
        sys.exit()

    model = YOLO(MODEL_PATH)

    app = QApplication(sys.argv)
    overlay = OverlayWindow(hwnd, model)
    sys.exit(app.exec_())
