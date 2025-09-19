from flask import Flask, render_template,request,send_file
from flask_cors import CORS  # 追加
from PIL import Image
from werkzeug.utils import secure_filename
import io
import json
import datetime
import asyncio
from operator import itemgetter
from operator import attrgetter
import copy
import numpy as np
from matplotlib.colors import to_rgb
import os
from collections import defaultdict
import Image_create


app = Flask(__name__)
PROCESSED_FOLDER = 'processed'
TEST = 0
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs("TEST", exist_ok=True)

# ★ まずは全許可で動作確認（開発用）:
# CORS(
#     app,
#     resources={r"/upload": {"origins": "*"}},  # 動的に絞る前の確認用
#     supports_credentials=False,                 # Cookie使うなら True にし、origins は * ではなく限定必須
#     methods=["GET", "POST", "OPTIONS"],
#     allow_headers=["Content-Type", "Authorization"],
#     expose_headers=[],
#     max_age=86400
# )

# ---------- Helpers ----------

def _to_px(v, total):
    """Accept normalized (0-1) or absolute pixel; clamp into [0,total]."""
    try:
        f = float(v)
    except Exception:
        return 0
    if 0.0 <= f <= 1.0:
        return int(round(f * total))
    return max(0, min(int(round(f)), total))

def _now_ts():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

# ---------- Core classes (state kept per-request only) ----------

class SnippedPiece:
    """A cropped image + small bit of metadata used for sorting."""
    def __init__(self, name, area_index, img, last_md=None, serial_num=None):
        # Always hold an owned copy so parent close() won't affect us
        self.image = img.copy()
        self.name = name
        self.area_index = int(area_index)
        # Optional values: used only to stabilize sort if present
        self.last_md = int(last_md) if last_md is not None and str(last_md).isdigit() else 0
        try:
            self.serial_num = int(serial_num) if serial_num is not None else 0
        except Exception:
            self.serial_num = 0

class SerialComposer:
    def __init__(self, req):
        self.req = req
        self.pieces = []

        # Parse snipping areas from request
        raw_areas = req.form.getlist("SnippingArea[]") or req.form.getlist("SnippingArea")
        areas = []
        for s in raw_areas:
            try:
                d = json.loads(s)
                areas.append(d)
            except Exception:
                continue
        # sort by 'rangeCount' if present, otherwise keep order
        if areas and 'rangeCount' in areas[0]:
            areas.sort(key=itemgetter('rangeCount'))
        self.areas = areas

        # iterate files
        for key in list(req.files.keys()):
            file = req.files.get(key)
            if not file:
                continue

            # optional metadata naming convention:
            #   img[<name>][lastMd], img[<name>][serialNum]
            # or generic fields lastMd/name/serialNum alongside the file
            base = key
            if base.endswith('][image]'):
                name = base.split('[')[1].split(']')[0]
                last_md = req.form.get(f"img[{name}][lastMd]")
                serial_num = req.form.get(f"img[{name}][serialNum]")
                file_name_alias = name
            else:
                file_name_alias = getattr(file, 'filename', base)
                last_md = req.form.get('lastMd') or '0'
                serial_num = req.form.get('serialNum') or '0'

            # open once and crop all areas
            with Image.open(file.stream) as im:
                im = im.convert("RGBA")
                if self.areas:
                    for j, area in enumerate(self.areas):
                        x1 = _to_px(area.get('x1', 0), im.width)
                        y1 = _to_px(area.get('y1', 0), im.height)
                        x2 = _to_px(area.get('x2', im.width), im.width)
                        y2 = _to_px(area.get('y2', im.height), im.height)
                        x1, y1 = max(0, min(x1, x2)), max(0, min(y1, y2))
                        x2, y2 = min(im.width, max(x1+1, x2)), min(im.height, max(y1+1, y2))
                        crop = im.crop((x1, y1, x2, y2)).copy()
                        self.pieces.append(SnippedPiece(file_name_alias, j, crop, last_md, serial_num))
                else:
                    # If no areas provided, take the whole image as area 0
                    self.pieces.append(SnippedPiece(file_name_alias, 0, im, last_md, serial_num))

        # Stable sort: by last_md -> area_index -> serial_num -> name
        self.pieces.sort(key=lambda p: (p.last_md, p.area_index, p.serial_num, p.name))

    def compose(self, margin=6, bg=(24,24,24,255)):
        """Arrange pieces by columns = areas, rows = chronological order."""
        if not self.pieces:
            # return a 1x1 transparent pixel
            return Image.new("RGBA", (1,1), (0,0,0,0))

        # bucket by area_index preserving order
        buckets = defaultdict(list)
        for p in self.pieces:
            buckets[p.area_index].append(p)

        # sort columns by area index
        col_indices = sorted(buckets.keys())

        # compute sizes
        col_widths = []
        col_heights = []
        for idx in col_indices:
            pieces = buckets[idx]
            w = max((p.image.width for p in pieces), default=1)
            h = sum((p.image.height for p in pieces), 0) + margin*(len(pieces)-1 if len(pieces)>0 else 0)
            col_widths.append(w)
            col_heights.append(h)

        total_w = sum(col_widths) + margin*(len(col_indices)-1 if len(col_indices)>0 else 0)
        total_h = max(col_heights) if col_heights else 1

        canvas = Image.new("RGBA", (total_w, total_h), bg)

        # paste
        x = 0
        for w, idx in zip(col_widths, col_indices):
            y = 0
            for p in buckets[idx]:
                canvas.alpha_composite(p.image, (x, y))
                y += p.image.height + margin
            x += w + margin

        return canvas

# ---------- Routes ----------


@app.route('/')
def index():
    return render_template('editor.html')

@app.route('/crop')
def crop_page():
    return render_template('crop.html')

@app.route('/send')
def send_page():
    return render_template('send.html')

@app.route("/upload", methods=["POST"])
def upload():
    print("\033[32m" + "UPLOAD_SUCSSES")
    # imgNames = request.form.getlist('img[fName]')
    # img1 = request.files.get(f'img[{imgNames[0]}][image]')
    # img2 = request.files.get(f'img[{imgNames[1]}][image]')
    # img2 =  Image.open(img2.stream)
    # img1 =  Image.open(img1.stream)
    # serial = get_concat_v(img1,img2)
    # processed_path = os.path.join(PROCESSED_FOLDER, "new.png")
    # serial.save(processed_path)
    raw_areas = request.form.getlist("SnippingArea[]")
    CreateImg = Image_create.createSerialImage(request,raw_areas)
    # CreateImg.setAreaNum()
    serialimage = CreateImg.cserialImage()
    processed_path = os.path.join(PROCESSED_FOLDER, "prossed.png")
    serialimage.save(processed_path)
    # CreateImg = SerialComposer(request)
    # # CreateImg.setAreaNum()
    # serialimage = CreateImg.compose()
    # processed_path = os.path.join(PROCESSED_FOLDER, "prossed.png")
    # serialimage.save(processed_path)
    # serialimage.close()

    # del CreateImg
    # print(request.form.get("SAREA_NUM"))
    # print(request.form.get("DAY_NUM"))
    # areas = request.form.getlist("SnippingArea[]")  # フォーム名が file[]
    # imgNames = request.form.getlist('img[fName]')
    # img_lastMd = request.form.get(f'img[{imgNames[0]}][lastMd]')
    # img = request.files.get(f'img[{imgNames[0]}][image]')
    # #imgld = request.form.getlist("img[lastMd]") 
    # print(areas)
    # #print(imgld)
    # timestamp = int(img_lastMd)
    # # ミリ秒なので1000で割って秒にする
    # dt = datetime.datetime.fromtimestamp(timestamp / 1000)
    # # フォーマット
    # formatted = dt.strftime("%Y%m%d%H%M%S")
    # print(formatted)
    # # files = request.files
    # # sample = None
    # # for file in files:
    # #     sample = file
    # # # f =  request.files.get(files[0])
    # # file2 =  request.files.get(file)
    # processed_path = os.path.join(PROCESSED_FOLDER, "new.png")
    # # # processed_path2 = os.path.join(PROCESSED_FOLDER, "IG2.png")
    # # # processed_path3 = os.path.join(PROCESSED_FOLDER, "IG3.png")

    # img2 =  Image.open(img.stream)
    # img2.save(processed_path)
    
    # snippingArea = request.form.get("SnippingArea")
    # print(snippingArea)

    # jsData = json.loads(snippingArea)

    # img =  Image.open(file.stream)
    # print("IMG1=" , img.width , img.height)
    # img = img.crop((jsData["x1"] * img.width, jsData["y1"] * img.height, jsData["x2"] * img.width, jsData["y2"] * img.height))
    
    # img2 =  Image.open(file2.stream)
    # img2.save(processed_path3)
    # print("IMG2=" , img2.width , img2.height)
    
    # img2 = img2.crop((jsData["x1"] * img2.width, jsData["y1"] * img2.height, jsData["x2"] * img2.width, jsData["y2"] * img2.height))
    # img2.save(processed_path2)
    
    # anchor1 = (1, 0.36)  # img1 上の結合点
    # anchor2 = (0, 0.71)   # img2 上の結合点

    # new_image = merge_by_anchors(img,anchor1,img2,anchor2,bg=(0,0,0,0))

    # new_image.save(processed_path)
    
    print("\033[0m")
    # "TEST"
    #return (request.form.get("SAREA_NUM") + request.form.get("DAY_NUM"))
    return send_file(processed_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

