let fileInput = document.getElementById('fileInput');
let baseCanvas = document.getElementById('baseCanvas');
let overlayCanvas = document.getElementById('overlayCanvas');
let canbasbase = document.getElementById('canvasbase');
let baseCtx = baseCanvas.getContext('2d');
let overlayCtx = overlayCanvas.getContext('2d');
let img = new Image();
let posWindowList = [];

let startX, startY, endX, endY;
let selecting = false;
let isDragging = false;
let rangeCount = 1;
let imgHeight = 0;
let imgWidth = 0;
let RangeBtn = document.getElementById('rangeBtn');
let cancelBtn = document.getElementById('cancelBtn');
let labeln = document.getElementById('labelN');
let SelectBtn = document.getElementById('areasetting');

RangeBtn.disabled = true;
cancelBtn.disabled = true;
let clickSomething = false;
let clickSomethinsName = "";



SelectBtn.addEventListener('click', (event) => {fileInput.click(); this.value = null;});



window.addEventListener('DOMContentLoaded', function() {
        localStorage.clear();
});

function removeLocalStorageExcept(keysToKeep) {
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!keysToKeep.includes(key)) {
      localStorage.removeItem(key);
    }
  }
}


fileInput.addEventListener('change', function(e) {
  let reader = new FileReader();
  reader.onload = function(evt) {
    img.onload = () => {
      imgHeight = baseCanvas.width = overlayCanvas.width = img.width/(1);
      imgWidth = baseCanvas.height = overlayCanvas.height = img.height/(1);
      baseCtx.drawImage(img, 0, 0, imgHeight , imgWidth);
    };
    img.src = evt.target.result;
  };
  reader.readAsDataURL(e.target.files[0]);
  SelectBtn.disabled = true;
  RangeBtn.disabled = false;
});

function toggleRange() {
  if (selecting) {
    const minX = Math.min(startX, endX);
    const minY = Math.min(startY, endY);
    const maxX = Math.max(startX, endX);
    const maxY = Math.max(startY, endY);
    const x1 = minX / baseCanvas.width;
    const y1 = minY / baseCanvas.height;
    const x2 = maxX / baseCanvas.width;
    const y2 = maxY / baseCanvas.height;

    const absWidth = Math.abs(x2 - x1) * imgHeight * 1;
    const absHeight = Math.abs(y2 - y1) * imgWidth * 1;

    const overlay = posWindowList[posWindowList.length-1];
    const grandParent = overlay.closest(`#cdiv${(posWindowList.length)}`);

    setSelectState(false);

    if((absWidth * absHeight) < 200){
      console.log(absWidth * absHeight);
      grandParent.remove();
      return;
    } 

    if(!x1 || !y1 || !x2 || !y2){
    } else{
      localStorage.setItem('SnippingArea' + rangeCount, JSON.stringify({rangeCount,x1, y1, x2, y2}));
      rangeCount++;
    }
    overlay.width = absWidth;
    overlay.height = absHeight;
    grandParent.style.left = String(minX) + "px";
    grandParent.style.top = String(minY) + "px";
    grandParent.style.width = "";
    grandParent.style.height = "";

    const overlayctx = overlay.getContext('2d');
    const gradient = overlayctx.createLinearGradient(0, 0, 300, 0); // 左から右へ
    gradient.addColorStop(0.0, "red");
    gradient.addColorStop(0.16, "orange");
    gradient.addColorStop(0.33, "yellow");
    gradient.addColorStop(0.5, "green");
    gradient.addColorStop(0.66, "blue");
    gradient.addColorStop(0.83, "indigo");
    gradient.addColorStop(1.0, "violet");
    overlayctx.strokeStyle = gradient;
    overlayctx.lineWidth = 10;
    overlayctx.strokeRect(0,0,absWidth,absHeight);
    // overlayctx.removeEventListener('touchmove', preventScroll, { passive: false });
    // overlayctx.removeEventListener('mousedown');
    // overlayctx.removeEventListener('mousemove');
    // overlayctx.removeEventListener('mouseup');
  } else {
    startX = null;
    startY = null;
    endX = null;
    endY = null; 
    if(clickSomething){
      clickSomething = false;
      const child = document.getElementById(clickSomethinsName);
      child.closest(`#cdiv${(child.id.replace("overlayCanvas",""))}`).remove();
      clickSomethinsName = "";
    }

    const canvasdiv = document.createElement('div');
    canvasdiv.width = imgHeight;
    canvasdiv.height = imgWidth;
    canvasdiv.className = `overlayCanvas`;
    canvasdiv.id = `cdiv${(posWindowList.length + 1)}`;
    canvasdiv.style.left = `0px`;
    canvasdiv.style.top = `0px`;
    canbasbase.appendChild(canvasdiv);
    const canvas = document.createElement('canvas');
    canvas.width = imgHeight;
    canvas.height = imgWidth;
    canvas.id = `overlayCanvas${(posWindowList.length + 1)}`;
    canvas.style.left = `0px`;
    canvas.style.top = `0px`;
    canvasdiv.appendChild(canvas);
    posWindowList.push(canvas);
    setSelectState(true);

    canvas.addEventListener('mousedown', e => {
      if (!selecting) return;
        const pos = getPos(e);
        startX = pos.x;
        startY = pos.y;
        isDragging = true;
    });

  canvas.addEventListener('mousemove', e => {
    if (!selecting || !isDragging) return;
      const pos = getPos(e);
      endX = pos.x;
      endY = pos.y;
      drawPreviewRect();
  });

  canvas.addEventListener('mouseup', e => {
    if (!selecting) return;
      const pos = getPos(e);
      endX = pos.x;
      endY = pos.y;
      isDragging = false;
      drawPreviewRect();
  });

// // touch events
  canvas.addEventListener('touchstart', e => {
    if (!selecting) return;
    const pos = getPos(e);
    startX = pos.x;
    startY = pos.y;
    isDragging = true;
  });

  canvas.addEventListener('touchmove', e => {
    preventScroll(e);
    if (!selecting) return;
    const pos = getPos(e);
    endX = pos.x;
    endY = pos.y;
    drawPreviewRect();
  });

  canvas.addEventListener('touchend', e => {
    if (!selecting) return;
    const pos = getPos(e.changedTouches[0]);
    endX = pos.x;
    endY = pos.y;
    isDragging = false;
    drawPreviewRect();
  });

  canvas.addEventListener('click', function(event) {
    if (selecting || clickSomething) return;
    clickSomethinsName = event.target.id;
    clickSomething = true;
  });
  
  }
}

function setSelectState(flag){
  selecting = flag;
  if(selecting){
      RangeBtn.innerText = "範囲登録";
      cancelBtn.disabled = false;
  } else {
      RangeBtn.innerText = "範囲設定";
      cancelBtn.disabled = true;
  }
}

function cancel(){
  if(selecting){
    const child = document.getElementById(`overlayCanvas${(posWindowList.length)}`);
    child.closest(`#cdiv${(child.id.replace("overlayCanvas",""))}`).remove();
    setSelectState(false);
  }

}

function getPos(e) {
  const rect = overlayCanvas.getBoundingClientRect();
  let x, y;
  if (e.touches && e.touches.length > 0) {
    x = e.touches[0].clientX - rect.left;
    y = e.touches[0].clientY - rect.top;
  } else {
    x = e.clientX - rect.left;
    y = e.clientY - rect.top;
  }
  return { x, y };
}

function drawPreviewRect() {
  if (!selecting || !isDragging) return;
  const overlay = posWindowList[posWindowList.length-1].getContext('2d');
  overlay.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
  overlay.strokeStyle = "red";
  overlay.lineWidth = 4;
  overlay.strokeRect(Math.min(startX, endX), Math.min(startY, endY),
                        Math.abs(endX - startX), Math.abs(endY - startY));
}

function preventScroll(e) {
  if (selecting) {
    e.preventDefault();
  }
}

// // mouse events
// overlayCanvas.addEventListener('mousedown', e => {
//   if (!selecting) return;
//   const pos = getPos(e);
//   startX = pos.x;
//   startY = pos.y;
//   isDragging = true;
// });

// overlayCanvas.addEventListener('mousemove', e => {
//   if (!selecting || !isDragging) return;
//   const pos = getPos(e);
//   endX = pos.x;
//   endY = pos.y;
//   drawPreviewRect();
// });

// overlayCanvas.addEventListener('mouseup', e => {
//   if (!selecting) return;
//   const pos = getPos(e);
//   endX = pos.x;
//   endY = pos.y;
//   isDragging = false;
//   drawPreviewRect();
// });

// // touch events
// overlayCanvas.addEventListener('touchstart', e => {
//   if (!selecting) return;
//   const pos = getPos(e);
//   startX = pos.x;
//   startY = pos.y;
//   isDragging = true;
// }, { passive: false });

// overlayCanvas.addEventListener('touchmove', e => {
//   preventScroll(e);
//   if (!selecting) return;
//   const pos = getPos(e);
//   endX = pos.x;
//   endY = pos.y;
//   drawPreviewRect();
// }, { passive: false });

// overlayCanvas.addEventListener('touchend', e => {
//   if (!selecting) return;
//   const pos = getPos(e.changedTouches[0]);
//   endX = pos.x;
//   endY = pos.y;
//   isDragging = false;
//   drawPreviewRect();
// }, { passive: false });

function finish() {
  const hasSelection = rangeCount > 1;
  localStorage.setItem('cropDone', hasSelection.toString());
  window.location.href = "/";
}
