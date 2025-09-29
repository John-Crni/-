from PIL import Image
from werkzeug.utils import secure_filename
from operator import itemgetter
from operator import attrgetter
import copy
import inspect
from PIL import Image,ImageDraw, ImageFont
import gc
import asyncio

import io
import json
import datetime
import os
import numpy as np
from matplotlib.colors import to_rgb

class SniptedImageInfo:
    
    isEnable = True
    
    nAreaNum = 0
    
    nSerialNum =  0 # in
    
    nLedgeX = 0 # in
    
    nLedgeY = 0 # in
    
    nRedgeX = 0 # in
    
    nRedgeY = 0 # in
        
    fSnippedImage = None #in
    
    _sFileName = "" #in
    
    nLastMd = 0 #in
    
    nSnippingAreaNum = 0 #in
    
    nImgNum = 0
    
    nGroup = 0

    def __init__(self,imgName,serialNum,lstmd,imgblob,snippingAreanum,imgnum):
        self.nImgNum = int(imgnum)
        self.nSnippingAreaNum = snippingAreanum
        self._sFileName = imgName
        timestamp = int(lstmd)
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        formatted = dt.strftime("%Y%m%d%H%M%S")
        self.nLastMd = int(formatted)
        self.fSnippedImage = imgblob
        self.nSerialNum = int(serialNum)
        self.fSnippedImage = self._fSnipedend(self.fSnippedImage)
        if self.isEnable:
            self.nLedgeX,self.nLedgeY = self._find_most_endpoint(IMG = self.fSnippedImage , direct= 0)
            self.nRedgeX,self.nRedgeY = self._find_most_endpoint(IMG = self.fSnippedImage , direct= 1)
    
    def _fSnipedend(self,img):
        print("[SniptedImageInfo][_fSnipedend]",(img == None))
        
        left = self._find_most_endpoint(IMG = img, direct = 0)
        if left == None:
            self.isEnable = False
            return
        
        right = self._find_most_endpoint(IMG = img, direct = 1)
        if right == None:
            self.isEnable = False
            return
        
        upper = self._find_most_endpoint(IMG = img, direct = 2)
        if upper == None:
            self.isEnable = False
            return
        
        down = self._find_most_endpoint(IMG = img, direct = 3)
        if down == None:
            self.isEnable = False
            return
        lx,ly = left
        rx,ry = right
        ux,uy = upper
        dx,dy = down
        lux = lx
        luy = uy
        rdx = rx
        rdy = dy
        niw = img.width
        nih = img.height
        with img as cimg:
            imgcopy = cimg.crop((lux, luy, rdx, rdy))

        return imgcopy
    
    def _find_most_endpoint(self, IMG = None , target_color = "red" , direct = 1, tolerance=150):
        tgt = self._get_rgb_from_name_or_tuple(target_color)                     # (3,)
        tol2 = tolerance * tolerance

        img = IMG.convert("RGB")
        arr = np.asarray(img, dtype=np.int16)          # (H,W,3)

        # 各画素とターゲット色の二乗距離（√なし）
        diff = arr - tgt                               # (H,W,3)
        dist2 = np.sum(diff*diff, axis=2)              # (H,W)

        # しきい値以内 = 線の画素のマスク
        mask = dist2 <= tol2                           # (H,W) bool
        if not mask.any():
            return None

        # True の座標を一括取得
        ys, xs = np.where(mask)

        # direct = 0(左)、direct > 1(右)　グラフの端の座標を取得する
        k = np.argmax(xs) #右
        if direct == 0:   #左
            k = np.argmin(xs)
        elif direct == 2: #上
            k = np.argmin(ys)
        elif direct == 3: #下
            k = np.argmax(ys)
        # k = np.argmin(xs)
        print(int(xs[k]),int(ys[k]))
        return int(xs[k]),int(ys[k])
    
    def _get_rgb_from_name_or_tuple(self,color):
        if isinstance(color, str):
            rgb = to_rgb(color)
            return tuple(int(c * 255) for c in rgb)
        return color

class createSerialImage:
    
    processed_path = 'none'
    
    _PROCESSED_FOLDER = 'processed'
    
    FONT_PATH = '7barPBd.TTF'
    
    _reqData = None #in
        
    _jslSnippingArea = [] # in

    _nDayCont = 0 # in
    
    _fSnipptedImages = []
    
    _siAreaArray = [] #another
    
    _sTableNumbers = []
    
    _paste_x = 0 #another
    
    _paste_y = 0 #another

    _shift_x = 0 #another
    
    _shift_y = 0 #another

    _aSpecifyTable = []

    def __init__(self,reqData,nlSA):
        self._fSnipptedImages.clear()
        self._reqData = reqData
        jslSAs = []
        for jslSA in nlSA:
            jslSAs.append(json.loads(jslSA))
        self._jslSnippingArea = sorted(jslSAs,key=itemgetter('rangeCount'))
        # self._nDayCont = nDAY
        imgNames = self._reqData.form.getlist('img[fName]')
        self._aSpecifyTable = self._reqData.form.getlist('SpecifyTable[]')
        tablenames = self._reqData.form.get('TableNumbers')
        if tablenames is not None:
            self._sTableNumbers = tablenames.split(',')
        
        for i in range(len(imgNames)):
            print("[createSerialImage]",i ,"回目")
            img_lastMd = self._reqData.form.get(f'img[{imgNames[i]}][lastMd]')
            nserialNum = self._reqData.form.get(f'img[{imgNames[i]}][serialNum]')
            nimgNum = self._reqData.form.get(f'img[{imgNames[i]}][imgNumber]')
            img = self._reqData.files.get(f'img[{imgNames[i]}][image]')
            # open once and crop all areas
            with Image.open(img.stream) as cimg:
                for j in range(len(self._jslSnippingArea)):
                    print("[createSerialImage]",j ,"枚目")
                    print("[createSerialImage]", self._jslSnippingArea[j])
                    print("[createSerialImage]" , cimg.width,cimg.height)
                    splitedimg = cimg.crop((self._jslSnippingArea[j]["x1"] * cimg.width, self._jslSnippingArea[j]["y1"] * cimg.height, self._jslSnippingArea[j]["x2"] * cimg.width, self._jslSnippingArea[j]["y2"] * cimg.height)).copy()
                    SII = SniptedImageInfo(imgNames[0] , nserialNum , img_lastMd , splitedimg , j , nimgNum)
                    if SII.isEnable:
                        self._fSnipptedImages.append(SII)
        self.setAreaNum()
        
    def cserialImage(self):
        nLenSAA = len(self._fSnipptedImages)
        merged = []
        mergedSNA = []
        mergedTBN = []
        counter = 0
        for i in range(len(self._fSnipptedImages)):
            if counter >= nLenSAA:
                break
            # IF 指定台番号条件挿入する
            
            FI = self._fSnipptedImages[counter]
            for j in range(1,FI.nGroup):
                nextFI = self._fSnipptedImages[counter + j]
                FI.fSnippedImage = self._merge_by_anchors(FI.fSnippedImage ,(FI.nRedgeX,FI.nRedgeY) ,
                                                           nextFI.fSnippedImage , (nextFI.nLedgeX,nextFI.nLedgeY))
                FI.nRedgeX = nextFI.nRedgeX + self._paste_x + self._shift_x
                FI.nRedgeY = nextFI.nRedgeY + self._paste_y + self._shift_y
            counter += FI.nGroup
            merged.append(FI.fSnippedImage)
        # for i in range(nLenSAA):
        #     aAA = self._siAreaArray[i]
        #     col = aAA[0]
        #     for j in range(1 , len(aAA)):
        #         col.fSnippedImage = self._merge_by_anchors(col.fSnippedImage ,(col.nRedgeX,col.nRedgeY) ,
        #                                                    aAA[j].fSnippedImage , (aAA[j].nLedgeX,aAA[j].nLedgeY)).copy()
        #         col.nRedgeX += self._paste_x
        #         col.nRedgeY += self._paste_y
        #     merged.append(col.fSnippedImage)
        
        for i in range(len(merged)):
            if i < len(self._sTableNumbers):
                merged[i] = self.get_setTableNumber(merged[i] , self._sTableNumbers[i])
                
        reMerged = merged[0]

        print("[createSerialImage][_cserialImage]merged:" , len(merged))

        for i in range(1,len(merged)):
            reMerged = self._get_concat_v(reMerged , merged[i])
        return reMerged
    
    def get_setTableNumber(self,im2,text2):
        font = ImageFont.truetype(self.FONT_PATH, size=int(im2.width/3))
        sample = Image.new("RGB", (200, 100))
        sampledraw = ImageDraw.Draw(sample)
        bbox = sampledraw.textbbox((0, 0), text=text2, font=font)
        texWidth = bbox[2] - bbox[0]  # x2 - x1
        texHeight= bbox[3] - bbox[1]  # y2 - y1
        Number = Image.new("RGB", (int(texWidth), int(texHeight)), (47 , 79 , 79))
        draw = ImageDraw.Draw(Number)
        draw.text((0,0),text=text2,fill=(255, 255, 255),font=font)
        dst = Image.new('RGB', (im2.width, Number.height + im2.height) , (47 , 79 , 79))
        dst.paste(Number, (0, 0))
        dst.paste(im2, (0, Number.height))
        return dst
    
    def _get_concat_v(self,im1, im2):
        maxWidth = im1.width if im1.width > im2.width else im2.width
        dst = Image.new('RGB', (maxWidth, im1.height + im2.height) , (47 , 79 , 79))
        dst.paste(im1, (0, 0))
        dst.paste(im2, (0, im1.height))
        return dst
    
    def _printfSnippedImage(self):
        for i in range(len(self._fSnipptedImages)):
            processed_path = os.path.join("TEST", f'TEST{i}.png')
            self._fSnipptedImages[i].fSnippedImage.save(processed_path)

    def getLIKey(self):
        re = "nLastMd"
        now_Sni = None
        before_Sni = None
        for fSni in self._fSnipptedImages:
            now_Sni = fSni
            if before_Sni is not None:
                if now_Sni.nLastMd == before_Sni.nLastMd and now_Sni.nImgNum != before_Sni.nImgNum:
                    re = 'nImgNum'
                    break
            before_Sni = now_Sni
        return re
    
    def fixImgNum(self):
        now_Sni = None
        before_Sni = None
        nImgNum = 1
        for fSni in self._fSnipptedImages:
            now_Sni = fSni
            if before_Sni is not None:
                if now_Sni.nSerialNum == before_Sni.nSerialNum:
                    if now_Sni.nLastMd != before_Sni.nLastMd:
                        nImgNum += 1
                else:
                    nImgNum = 1
            now_Sni.nImgNum = nImgNum
            before_Sni = now_Sni

    def setAreaNum(self):
        self._fSnipptedImages.sort(key = attrgetter('nLastMd','nImgNum','nSnippingAreaNum','nSerialNum'))
        LIKey = self.getLIKey()
        if LIKey == 'nLastMd':
            self.fixImgNum()
        self._fSnipptedImages.sort(key = attrgetter('nImgNum'))
        self._fSnipptedImages.sort(key = attrgetter('nSnippingAreaNum','nSerialNum'))
        self._fSnipptedImages.sort(key = attrgetter('nImgNum'))

        #self._fSnipptedImages.sort(key = attrgetter('nLastMd','nImgNum','nSnippingAreaNum','nSerialNum'))
        # self._fSnipptedImages.sort(key = attrgetter('nImgNum'))
        #AreaImageArray,nSnippingAreaNum
            # a = []
            # beforeSA = -1
            # for img in self._fSnipptedImages:
            #     if beforeSA != img.nSnippingAreaNum and beforeSA != -1:
            #         b = copy.deepcopy(a)
            #         self._siAreaArray.append(b)
            #         a.clear()
            #     beforeSA = img.nSnippingAreaNum
            #     a.append(img)
        counter = 0
        imgArray = []
        beforeLast = -1
        beforeImg = -1
        beforeLIroupe = 0
        beforeSA = -1
        beforeSAroupe = 0
        beforenum = 0
        beforenum2 = 0
        isChange = False
        nArrayNum = len(self._fSnipptedImages)

        print("[createSerialImage][setAreaNum]Start")
        for fsni in self._fSnipptedImages:
            print("nLastMd:",fsni.nLastMd , ", nImgNum:" , fsni.nImgNum , ", nSnippingAreaNum:" , fsni.nSnippingAreaNum, ", nSerialNum:" , fsni.nSerialNum)
        print("[createSerialImage][setAreaNum]End")

        for i in range(nArrayNum):
            now_imgNum = self._fSnipptedImages[i].nSnippingAreaNum
            if (self._ischange(now_imgNum , beforeSA)):
                for j in range(beforenum , i):
                    self._fSnipptedImages[j].nGroup = i - beforeSAroupe
                    beforeSAroupe = i
                beforenum = i
            if (i >= (nArrayNum-1)):
                for j in range(beforenum , i + 1):
                    self._fSnipptedImages[j].nGroup = (nArrayNum - beforenum)
            beforeSA = now_imgNum

        # for i in range(nArrayNum):
        #     now_imgNum = self._fSnipptedImages[i].nSnippingAreaNum
        #     now_Last = self._fSnipptedImages[i].nLastMd
        #     now_Img = self._fSnipptedImages[i].nImgNum
        #     if (self._ischange(now_Last , beforeLast)):
        #         for j in range(beforenum2 , i):
        #             self._fSnipptedImages[j].nGroup = i - beforeLIroupe
        #             beforeLIroupe = i
        #         beforenum2 = i
        #     elif (self._ischange(now_Img , beforeImg)):
        #         for j in range(beforenum2 , i):
        #             self._fSnipptedImages[j].nGroup = i - beforeLIroupe
        #             beforeLIroupe = i
        #         beforenum2 = i
        #         isChange = True
        #     elif (self._ischange(now_imgNum , beforeSA)):
        #         for j in range(beforenum , i):
        #             self._fSnipptedImages[j].nGroup = i - beforeSAroupe
        #             beforeSAroupe = i
        #         beforenum = i
        #         isChange = True
        #     if (i >= (nArrayNum-1) and not isChange):
        #         for j in range(beforenum , i + 1):
        #             self._fSnipptedImages[j].nGroup = (nArrayNum - beforenum)
        #     elif (i >= (nArrayNum-1)):
        #         for j in range(beforenum2 , i + 1):
        #             self._fSnipptedImages[j].nGroup = (nArrayNum - beforenum2)
        #     beforeSA = now_imgNum
        #     beforeLast = now_Last
        #     beforeImg = now_Img
            
    def _ischange(self , before , now):
        re = False
        if (now != before and before != -1):
            re = True
        return re        

    def _merge_by_anchors(
        self,
        img1, anchor1,
        img2, anchor2,
        bg=(0,0,0,0)
    ):
        """
        img1 上の anchor1(x1,y1) と img2 上の anchor2(x2,y2) が
        キャンバス上で一致するように結合する。
        画像が左上にはみ出す場合も自動でキャンバスを拡げて収める。
        """

        x1, y1 = anchor1
        x2, y2 = anchor2
        
        # x1 *= img1.width
        # x2 *= img2.width
        # y1 *= img1.height
        # y2 *= img2.height

        w1, h1 = img1.width, img1.height
        w2, h2 = img2.width, img2.height

        # img2 の左上がキャンバス上でどこに来るべきか（絶対座標）
        self._paste_x = x1 - x2
        self._paste_y = y1 - y2

        # 2画像が収まるキャンバス境界（最小/最大座標）
        min_x = min(0, self._paste_x)
        min_y = min(0, self._paste_y)
        max_x = max(w1, self._paste_x + w2)
        max_y = max(h1, self._paste_y + h2)
        
        # キャンバスサイズ
        canvas_w = max_x - min_x
        canvas_h = max_y - min_y

        # 左上が負になる場合のシフト量（全体を右下にずらす）
        shift_x = -min_x
        shift_y = -min_y
        
        self._shift_x = int(shift_x)
        self._shift_y = int(shift_y)
        
        self._paste_x = int(self._paste_x)
        self._paste_y = int(self._paste_y)
        
        # 背景とモード決定
        mode = "RGBA"
        canvas = Image.new(mode, (int(canvas_w), int(canvas_h)))
        
        # mask1 = self._alpha_mask(img1)
        # mask2 = self._alpha_mask(img2)
        with img1 as cimg:
            canvas.paste(cimg, (self._shift_x, self._shift_y))
        with img2 as cimg:
            canvas.paste(cimg, (self._shift_x + self._paste_x, self._shift_y + self._paste_y))
            
        return canvas