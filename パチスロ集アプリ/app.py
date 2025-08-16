from flask import Flask, render_template,request,send_file
from flask_cors import CORS  # 追加
from PIL import Image
from werkzeug.utils import secure_filename
import io
import json


import os


app = Flask(__name__)
PROCESSED_FOLDER = 'processed'
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

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
    print(request.form.get("SAREA_NUM"))
    print(request.form.get("DAY_NUM"))
    areas = request.form.getlist("SnippingArea[]")  # フォーム名が file[] の場合
    print(areas)
    # files = request.files
    # sample = None
    # for file in files:
    #     sample = file
    
    
    # # f =  request.files.get(files[0])
    # file2 =  request.files.get(file)
    # processed_path = os.path.join(PROCESSED_FOLDER, "new.png")
    # # processed_path2 = os.path.join(PROCESSED_FOLDER, "IG2.png")
    # # processed_path3 = os.path.join(PROCESSED_FOLDER, "IG3.png")

    # img2 =  Image.open(file2.stream)
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
    return (request.form.get("SAREA_NUM") + request.form.get("DAY_NUM"))
    # return send_file(processed_path, as_attachment=True)

def _alpha_mask(im: Image.Image):
    return im.split()[-1] if "A" in im.getbands() else None

def merge_by_anchors(
    img1: Image.Image, anchor1: tuple,
    img2: Image.Image, anchor2: tuple,
    bg=(0,0,0,0)
) -> Image.Image:
    """
    img1 上の anchor1(x1,y1) と img2 上の anchor2(x2,y2) が
    キャンバス上で一致するように結合する。
    画像が左上にはみ出す場合も自動でキャンバスを拡げて収める。
    """

    x1, y1 = anchor1
    x2, y2 = anchor2
    
    x1 *= img1.width
    x2 *= img2.width
    y1 *= img1.height
    y2 *= img2.height

    w1, h1 = img1.width, img1.height
    w2, h2 = img2.width, img2.height

    # img2 の左上がキャンバス上でどこに来るべきか（絶対座標）
    paste_x = x1 - x2
    paste_y = y1 - y2

    # 2画像が収まるキャンバス境界（最小/最大座標）
    min_x = min(0, paste_x)
    min_y = min(0, paste_y)
    max_x = max(w1, paste_x + w2)
    max_y = max(h1, paste_y + h2)

    # キャンバスサイズ
    canvas_w = max_x - min_x
    canvas_h = max_y - min_y

    # 左上が負になる場合のシフト量（全体を右下にずらす）
    shift_x = -min_x
    shift_y = -min_y
    
    shift_x = int(shift_x)
    shift_y = int(shift_y)
    
    paste_x = int(paste_x)
    paste_y = int(paste_y)
    
    # 背景とモード決定
    mode = "RGBA"
    canvas = Image.new(mode, (int(canvas_w), int(canvas_h)))
    
    mask1 = _alpha_mask(img1)
    mask2 = _alpha_mask(img2)

    canvas.paste(img1, (shift_x, shift_y),mask=mask1)
    canvas.paste(img2, (shift_x + paste_x, shift_y + paste_y),mask=mask2)
    
    return canvas

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
