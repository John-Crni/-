// IndexedDB 初期化
const dbName = "ImageDB";
const storeName = "images";
let ServerResponse = null;

// DB初期化
function initDB() {
    return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);
    request.onupgradeneeded = function(event) {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: "id", autoIncrement: true });
        }
    };
    request.onsuccess = function(event) {
        resolve(event.target.result);
    };
    request.onerror = function(event) {
        reject("DBオープンエラー: " + event.target.errorCode);
    };
    });
}

export async function saveImagesToIndexedDB(blob,btmname) {
    let comimgs = [];
    for(let img of blob){
      comimgs.push(await compressToPNG(img));
    }
    const db = await initDB();
    const tx = db.transaction(storeName, "readwrite");
    const store = tx.objectStore(storeName);
    for(let image of comimgs){
      await store.add({ selectedMD: btmname , lastMd: image.lastModified, fileName: image.name ,imageBlob: image });
    }
    await tx.complete;
    db.close();
}

  // 🔶 browser-image-compression を使ってPNG形式で保存
async function compressToPNG(file) {
  const options = {
    maxWidthOrHeight: 700,   // サイズ縮小（オプション）
    fileType: "image/png",    // PNG形式に変換（可逆）
    initialQuality: 1.0       // PNGなので無視される（指定可）
  };
  return imageCompression(file, options);
}

export async function clearIndexedDB(){
  const db = await initDB();
  const tx = db.transaction(storeName, "readwrite");
  const store = tx.objectStore(storeName);
  store.clear();
  db.close();
}

export async function deleteImageByFileName(targetFileName) {
  const db = await initDB();
  const tx = db.transaction(storeName, "readwrite");
  const store = tx.objectStore(storeName);
  const getAllRequest = store.getAll();

  getAllRequest.onsuccess = function() {
    const results = getAllRequest.result;
    let match;
    let deleted = false;
    for(let imageData of results){
      match = (imageData.selectedMD === targetFileName);
      if(match){
        store.delete(imageData.id);
        deleted = true;
      }
    }
    if (deleted) {
      alert(`"${targetFileName}" を削除しました`);

    } else {
      alert(`"${targetFileName}" は見つかりませんでした`);
    }
  };
}

async function getImagesFromIndexedDB() {
  const db = await initDB();
  const tx = db.transaction(storeName, "readonly");
  const store = tx.objectStore(storeName);
  const request = store.getAll();

  return new Promise((resolve, reject) => {
    //  request.onsuccess = () => resolve(request.result.map(item => item));imageBlob
     request.onsuccess = () => resolve(request.result);
     request.onerror = () => reject(request.error);
   });
}

export async function uploadImages() {
  const files = await getImagesFromIndexedDB();
  const formData = new FormData();
  let Areanum = 0;
  let daylist = [];
  for (let i = 0; (i < localStorage.length); i++) {
    const key = localStorage.key(i);
    if(key.includes("SnippingArea")){
        Areanum += 1;
        formData.append("SnippingArea[]" , localStorage.getItem(key));
        console.log(`KEY_NAME${Areanum} : ${key}`);
    }
  }// button
  let imageIndex = 0;
  files.forEach((file) => {
    if(daylist.indexOf(file.selectedMD)==-1){
      daylist.push(file.selectedMD);
      imageIndex += 1;
    }
    // const img_num = (files.filter(msd => msd.selectedMD===file.selectedMD)).length;
    // console.log(`img_num(${file.selectedMD}) : ${img_num}`);
    const md = file.selectedMD.replace("button","");
    formData.append(`img[fName]`,file.fileName);
    formData.append(`img[${file.fileName}][serialNum]`,md);
    formData.append(`img[${file.fileName}][lastMd]`,file.lastMd);
    formData.append(`img[${file.fileName}][image]`,file.imageBlob);
  });
  console.log(`DAY${imageIndex}`);
  formData.append('DAY_NUM' , imageIndex);

  // 実際のエンドポイントに書き換えてください
  ServerResponse =  await fetch("http://192.168.0.14:5000/upload", {
    method: "POST",
    body: formData
  })
  // .then(res => res.text())
  // .then(text => {
  //   console.log("アップロード成功:", text);
  // })
  // .catch(err => {
  //   console.error("アップロード失敗:", err);
  // });
}

export async function downloadImages() {
  if(ServerResponse!=null){
    if (!ServerResponse.ok) {
      const txt = await ServerResponse.text();
      alert('サーバーエラー: ' + txt);
      return;
    }

    const blob = await ServerResponse.blob();
    let url = URL.createObjectURL(blob);

    // 元ファイル名ベースでダウンロード名を付ける（拡張子はサーバの返却に合わせPNG想定）
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gray.png';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

      // return new Promise((resolve) => {
      //   const img = new Image();
      //   img.onload = () => resolve(img);
      //   img.src = URL.createObjectURL(file);
      // });
  }
}