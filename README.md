# ROKBOT-Open-Src

## 自述
**Rise of Kingdoms Open Source Project (ROKBOT-Open-Src) 是一個用 Python+yolo8輔助開發的遊戲程式，專門用於偵測遊戲中的寶石。**
**請將 `gem.pt` 放在 `main.py` 同層資料夾。**
**工作原理是利用電腦視窗截圖進行判別，非侵入式獲取座標判別寶石位置**
**請勿加上自動點擊(可能會觸發機器人檢測)**


[![觀看教學影片](https://img.youtube.com/vi/gDa1ipJrP68/0.jpg)](https://youtu.be/gDa1ipJrP68)
---
## 功能項目
1. **寶石自動檢測**
2. **自動辨識 Rise of Kingdoms 遊戲視窗**
3. **即時追蹤視窗大小與位置變化**（Unity 視窗相容性尚未完全穩定）
4. **自動標框**


---

## 本腳本使用工具and視窗大小如下:
- **Python 3.10.11**
- **遊戲內部畫面設定1600x900準確度最高**
---

## 需要的 pip 套件 (執行前請先安裝)

請在命令列中執行以下指令：

```bash
pip install numpy
pip install opencv-python
pip install mss
pip install pyqt5
pip install ultralytics
pip install psutil
pip install pywin32
