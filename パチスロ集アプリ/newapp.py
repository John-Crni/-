from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import io, os, json, datetime
from operator import itemgetter
from collections import defaultdict

app = Flask(__name__)
CORS(app)

PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), "processed")
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

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

@app.route("/", methods=["GET"])
def index():
    return jsonify({"ok": True, "message": "POST images to /upload with SnippingArea[] JSON array"})

@app.route("/upload", methods=["POST"])
def upload():
    composer = SerialComposer(request)
    out = composer.compose()

    # Save + stream back
    ts = _now_ts()
    out_path = os.path.join(PROCESSED_FOLDER, f"processed_{ts}.png")
    out.save(out_path, format="PNG")
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    out.close()
    buf.seek(0)

    resp = send_file(buf, mimetype="image/png", as_attachment=True, download_name=f"processed_{ts}.png")
    # Avoid cache mixing on the browser side
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
