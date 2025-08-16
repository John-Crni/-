import { saveImagesToIndexedDB } from "./saveP2db.js";
import { deleteImageByFileName } from "./saveP2db.js";
import { uploadImages } from "./saveP2db.js";
import { downloadImages } from "./saveP2db.js";
import { clearIndexedDB } from "./saveP2db.js";

window.addEventListener('DOMContentLoaded', function() {
    clearIndexedDB();
});


let clikingBtn = null;
const weeksOriginal = ['日', '月', '火', '水', '木', '金', '土'];
const today = new Date();
const todayDay = today.getDay(); // 今日の曜日（0=日〜6=土）
let saveDays = 0;

clearIndexedDB();

// 今日を右下（6列目の土曜）に合わせる：曜日配列をローテート
const weeks = [...weeksOriginal.slice(todayDay + 1), ...weeksOriginal.slice(0, todayDay + 1)];

// 30日前から今日までを昇順で取得
const dates = [];
for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    dates.push(d);
}

// カレンダー配置行列（6行7列）
const calendarMatrix = Array.from({ length: 5 }, () => Array(7).fill(null));

// 日付を後ろから順に埋める（今日を右下に）
let row = 4;
let col = 6; // 土曜固定
dates.reverse().forEach(date => {
    calendarMatrix[row][col] = {
        day: date.getDate(),
        month: date.getMonth() + 1,
        isToday: date.toDateString() === today.toDateString()
    };
    col--;
    if (col < 0) {
        col = 6;
        row--;
    }
});

// HTML生成
let calendarHtml = '<table><tr>';
const DAYS = [];
weeks.forEach(w => calendarHtml += `<td>${w}</td>`);
calendarHtml += '</tr>';

calendarMatrix.forEach(week => {
    calendarHtml += '<tr>';
    week.forEach(cell => {
        if (cell) {  
            const todayClass = cell.isToday ? ' today' : '';
            const delbtn = cell.isToday? '<button id="deleteBtn" class="del">画像削除</button>' : '';
            const sendbtn = cell.isToday? '<button id="sendBtn" class="sen">画像送信</button>' : '';
            calendarHtml += `<td><div class="day-container${todayClass}"><span class="month-label">${cell.month}/</span><button id="button${cell.month.toString().padStart(2, '0')}${(cell.day.toString()).padStart(2, '0')}">${cell.day}</button>${delbtn}${sendbtn}</div></td>`;
            DAYS.push(`button${cell.month.toString().padStart(2, '0')}${(cell.day.toString()).padStart(2, '0')}`);
        } else {
            calendarHtml += '<td></td>';
        }
    });
    calendarHtml += '</tr>';
});
calendarHtml += '</table>';

document.querySelector('#calendar').innerHTML = calendarHtml;

const deleteBtn = document.getElementById("deleteBtn");

const sendBtn = document.getElementById("sendBtn");

deleteBtn.style.width = "7vw";

deleteBtn.addEventListener('click', async(event) => {    
    await deleteImageByFileName(clikingBtn.getAttribute("id"));
    button_unselected(clikingBtn);
    saveDays -= 1;
    savebtnEnable();    
    deleteBtn.disabled = true;
});

sendBtn.addEventListener('click', async(event) => {    
    await uploadImages();
    await downloadImages();
    sendBtn.disabled = true;        
});

deleteBtn.disabled = true;

sendBtn.disabled = true;

DAYS.forEach(day => {
    const button = document.getElementById(day);
    button.addEventListener('click', (event) => {
        clikingBtn = event.currentTarget;
        if(!clikingBtn.classList.contains('selecting')) {
            fileInput.click();
            deleteBtn.disabled = true;
        } else {
            deleteBtn.disabled = false;
        }
    });
});

const ifile = document.getElementById("fileInput");

const selectImage = async(event) =>{
    const file = event.target.files;
    console.log(`ファイル数：${file.length}`);
    if (file) {
        if(file.length > 0) {
            await saveImagesToIndexedDB(file , clikingBtn.getAttribute("id"));
            saveDays +=1;
            savebtnEnable();    
            button_selected(clikingBtn);
        } else {
            alert("ファイルが選択されませんでした。");
        }
    }
};

ifile.addEventListener('change', selectImage);
ifile.addEventListener('click', clearFilePath);

function button_unselected(button){
    button.classList.remove('selecting');
}

function button_selected(button){
    button.classList.add('selecting');
}

function savebtnEnable(){
    if(saveDays>1){
        sendBtn.disabled = false;        
    } else {
        sendBtn.disabled = true;        
    }
}


// 保持しているファイル名を消す
function clearFilePath(e) {
    this.value = null;
}

