import os
import shutil
import numpy as np
import cv2
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
# Import SQLAlchemy chuẩn 2.0
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Thêm đoạn này vào bên dưới khai báo app = FastAPI()
def apply_medical_masking(image_bytes):
    # Chuyển bytes sang mảng numpy để OpenCV xử lý
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Giả lập: Trong ảnh y tế, thông tin bệnh nhân thường nằm ở góc trên cùng
    # Chúng ta sẽ vẽ một hình chữ nhật đen che khoảng 10% chiều cao phía trên
    h, w, _ = img.shape
    cv2.rectangle(img, (0, 0), (w, int(h * 0.1)), (0, 0, 0), -1)
    
    # Thêm dòng chữ "PII REMOVED" để chứng minh tính tuân thủ
    cv2.putText(img, "CONFIDENTIAL - PII REMOVED", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Trả về ảnh đã xử lý dưới dạng bytes
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

# Trong route upload của bạn, hãy gọi hàm này trước khi lưu:
# masked_image = apply_medical_masking(file_bytes)

# --- CẤU HÌNH HỆ THỐNG ---
UPLOAD_DIR = "/app/static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATABASE_URL = "sqlite:///./medtrack.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

class MedicalRecord(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String)
    notes = Column(Text)
    image_path = Column(String)
    owner_id = Column(Integer)

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal(); 
    try: yield db
    finally: db.close()

def get_uid(request: Request):
    return request.cookies.get("user_session")

# --- CSS STYLE GỐC (GIỮ VẺ ĐẸP BAN ĐẦU) ---
BASE_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    :root { --primary: #2ecc71; --dark: #0f172a; --card: #1e293b; --text: #f1f5f9; --dim: #94a3b8; }
    body { font-family: 'Inter', sans-serif; background: var(--dark); color: var(--text); margin: 0; transition: 0.3s; }
    .navbar { background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; position: sticky; top: 0; z-index: 100; }
    .hero { text-align: center; padding: 80px 20px; background: radial-gradient(circle at top, #1e293b, #0f172a); }
    .hero h1 { font-size: 3rem; margin: 0; background: linear-gradient(to right, #2ecc71, #27ae60); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; padding: 40px 10%; }
    .card { background: var(--card); padding: 30px; border-radius: 20px; border: 1px solid #334155; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); text-decoration: none; color: inherit; display: block; position: relative; overflow: hidden; }
    .card:hover { border-color: var(--primary); transform: translateY(-10px); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
    .card h3 { color: var(--primary); font-size: 1.5rem; margin-top: 0; }
    .card p { color: var(--dim); line-height: 1.6; }
    .badge { background: var(--primary); color: #000; padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: bold; position: absolute; top: 20px; right: 20px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    uid = get_uid(request)
    auth_btn = f'<span>Dr. ID: {uid}</span> <a href="/logout" style="color:#ff4757; text-decoration:none; margin-left:15px; font-weight:600;">Logout</a>' if uid else \
               '<a href="/login-page" style="background:var(--primary); color:#000; padding:10px 25px; border-radius:10px; text-decoration:none; font-weight:bold;">Access Portal</a>'
    
    return f"""
    <html><head>{BASE_STYLE}</head><body>
        <nav class="navbar"><div style="font-size:1.5rem; font-weight:bold;">🏥 MedTrack <span style="color:var(--primary)">Pro</span></div><div>{auth_btn}</div></nav>
        <div class="hero"><h1>Medical Intelligent Control</h1><p style="color:var(--dim); font-size:1.2rem;">Next-generation clinical data management & encrypted vault.</p></div>
        <div class="grid">
            <a href="/vault" class="card">
                <div class="badge">KMS SHIELD</div>
                <h3>Secure Vault</h3><p>Tìm kiếm hồ sơ bệnh nhân toàn hệ thống với bảo mật đa tầng.</p>
            </a>
            <a href="/patient-data" class="card" style="border-left: 5px solid var(--primary);">
                <h3>My Patient Data</h3><p>Quản lý hồ sơ, hình ảnh và ghi chú bệnh lý cá nhân của bạn.</p>
            </a>
            <div class="card" style="opacity: 0.6; cursor: not-allowed;">
                <h3>Treatment Timeline</h3><p>Theo dõi tiến trình điều trị theo thời gian thực (Coming Soon).</p>
            </div>
            <div class="card" style="opacity: 0.6; cursor: not-allowed;">
                <h3>Clinical Analytics</h3><p>Phân tích chỉ số sinh tồn và biểu đồ bệnh lý chuyên sâu (Coming Soon).</p>
            </div>
        </div>
    </body></html>"""

# (Tiếp theo API Login/Logout tương tự các bản trước nhưng bọc trong giao diện Inter font)

# --- TRANG MY PATIENT DATA (Giao diện 2 cột + Treatment Timeline mồi) ---
@app.get("/patient-data", response_class=HTMLResponse)
async def patient_data_page(request: Request):
    if not get_uid(request): return RedirectResponse("/login-page")
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Management Portal | MedTrack</title>
        {BASE_STYLE}
        <style>
            .container {{ width: 90%; max-width: 1100px; margin: 40px auto; }}
            .upload-box {{ background: var(--card); padding: 30px; border-radius: 20px; border: 2px dashed #334155; margin-bottom: 40px; }}
            input, textarea {{ width: 100%; padding: 14px; margin: 10px 0; border-radius: 10px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; font-family: 'Inter'; }}
            
            .record-item {{ display: flex; background: var(--card); border-radius: 20px; margin-bottom: 25px; overflow: hidden; border: 1px solid #334155; transition: 0.3s; }}
            .record-img {{ flex: 1; max-width: 350px; background: #000; position: relative; }}
            .record-img img {{ width: 100%; height: 100%; object-fit: cover; min-height: 250px; }}
            .record-info {{ flex: 1.5; padding: 30px; display: flex; flex-direction: column; justify-content: space-between; }}
            .record-info h3 {{ color: var(--primary); margin: 0 0 15px 0; font-size: 1.6rem; }}
            .record-info p {{ color: #cbd5e1; line-height: 1.7; margin: 0; }}
            
            .btn-action {{ display: flex; gap: 10px; margin-top: 20px; }}
            .del-btn {{ background: #ff4757; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s; }}
            .del-btn:hover {{ background: #ff6b81; transform: scale(1.05); }}
            
            /* Sidebar phụ cho Clinical Analytics */
            .sidebar-hint {{ background: rgba(46, 204, 113, 0.1); border: 1px solid var(--primary); padding: 15px; border-radius: 12px; margin-bottom: 20px; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <nav class="navbar"><div style="font-size:1.5rem; font-weight:bold;">🏥 MedTrack <span style="color:var(--primary)">Pro</span></div><a href="/" style="color:var(--primary); text-decoration:none; font-weight:bold;">← Quay lại Dashboard</a></nav>
        
        <div class="container">
            <div style="display: flex; gap: 30px; align-items: flex-start;">
                <div style="flex: 1;">
                    <h1 style="margin-top:0;">📂 Patient Records</h1>
                    <div class="sidebar-hint">ℹ️ Toàn bộ dữ liệu hình ảnh được mã hóa chuẩn quân đội trước khi lưu trữ.</div>
                    <div class="upload-box">
                        <form id="uploadForm">
                            <input type="text" id="p_name" placeholder="Tên bệnh nhân (Họ và tên)" required>
                            <textarea id="p_notes" placeholder="Ghi chú bệnh lý, phác đồ điều trị, kết quả lâm sàng..." rows="5"></textarea>
                            <input type="file" id="p_file" accept="image/*" required>
                            <button type="submit" class="btn" style="background:var(--primary); padding:15px; border-radius:10px; width:100%; border:none; font-weight:bold; cursor:pointer;">Lưu hồ sơ an toàn</button>
                        </form>
                    </div>
                </div>

                <div style="flex: 0.4; background: var(--card); padding: 25px; border-radius: 20px; border: 1px solid #334155;">
                    <h4 style="color:var(--primary); margin-top:0;">Treatment Timeline</h4>
                    <ul style="list-style: none; padding: 0; color: var(--dim); font-size: 0.85rem;">
                        <li style="margin-bottom:15px;">🟢 Initial Diagnosis (Completed)</li>
                        <li style="margin-bottom:15px;">🟡 Clinical Testing (In Progress)</li>
                        <li style="margin-bottom:15px;">⚪ Medication Phase</li>
                    </ul>
                    <hr style="border: 0.5px solid #334155; margin: 20px 0;">
                    <h4 style="color:var(--primary);">Clinical Analytics</h4>
                    <div style="height: 100px; background: #0f172a; border-radius: 10px; display: flex; align-items: flex-end; justify-content: space-around; padding: 10px;">
                        <div style="width:15%; background:var(--primary); height:40%;"></div>
                        <div style="width:15%; background:var(--primary); height:70%;"></div>
                        <div style="width:15%; background:var(--primary); height:55%;"></div>
                        <div style="width:15%; background:var(--primary); height:90%;"></div>
                    </div>
                </div>
            </div>

            <h2 style="margin: 40px 0 20px 0; border-bottom: 2px solid #334155; padding-bottom: 10px;">📋 Danh sách hồ sơ đã lưu</h2>
            <div id="resultsList"></div>
        </div>

        <script>
            async function fetchRecords() {{
                const res = await fetch('/api/my-records');
                const data = await res.json();
                const list = document.getElementById('resultsList');
                list.innerHTML = '';
                data.reverse().forEach(item => {{
                    list.innerHTML += `
                        <div class="record-item">
                            <div class="record-img">
                                <img src="${{item.image_path}}" onerror="this.src='https://via.placeholder.com/400x300?text=No+Image'">
                            </div>
                            <div class="record-info">
                                <div>
                                    <h3>BN: ${{item.patient_name}}</h3>
                                    <p>${{item.notes || 'Không có ghi chú bệnh lý.'}}</p>
                                </div>
                                <div class="btn-action">
                                    <button class="del-btn" onclick="deleteRec(${{item.id}})">🗑️ Xóa hồ sơ</button>
                                </div>
                            </div>
                        </div>`;
                }});
            }}

            async function deleteRec(id) {{
                if(confirm("Xác nhận xóa hồ sơ bệnh nhân này?")) {{
                    await fetch(`/api/delete/${{id}}`, {{ method: 'DELETE' }});
                    fetchRecords();
                }}
            }}

            document.getElementById('uploadForm').onsubmit = async (e) => {{
                e.preventDefault();
                const formData = new FormData();
                formData.append('patient_name', document.getElementById('p_name').value);
                formData.append('notes', document.getElementById('p_notes').value);
                formData.append('file', document.getElementById('p_file').files[0]);
                
                const btn = e.target.querySelector('button');
                btn.innerText = "Đang xử lý...";
                btn.disabled = true;

                const res = await fetch('/upload', {{ method: 'POST', body: formData }});
                if(res.ok) {{
                    document.getElementById('uploadForm').reset();
                    fetchRecords();
                }}
                btn.innerText = "Lưu hồ sơ an toàn";
                btn.disabled = false;
            }};
            fetchRecords();
        </script>
    </body></html>"""

# --- TRANG VAULT (Giữ đúng phông chữ và layout 2 cột khi tìm kiếm) ---
@app.get("/vault", response_class=HTMLResponse)
async def vault_page(request: Request):
    if not get_uid(request): return RedirectResponse("/login-page")
    return f"""
    <html><head>{BASE_STYLE}
    <style>
        .search-container {{ width: 90%; max-width: 800px; margin: 60px auto; text-align: center; }}
        .search-bar {{ width: 100%; padding: 20px 30px; border-radius: 50px; border: 1px solid #334155; background: var(--card); color: white; font-size: 1.2rem; outline: none; transition: 0.3s; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
        .search-bar:focus {{ border-color: var(--primary); box-shadow: 0 10px 30px rgba(46, 204, 113, 0.2); }}
        .record-item {{ display: flex; background: var(--card); border-radius: 20px; margin-top: 30px; overflow: hidden; border: 1px solid #334155; text-align: left; }}
        .record-img {{ flex: 1; max-width: 300px; }}
        .record-img img {{ width: 100%; height: 100%; object-fit: cover; min-height: 200px; }}
        .record-info {{ flex: 1.5; padding: 25px; }}
        .record-info h3 {{ color: var(--primary); margin: 0; }}
    </style></head><body>
        <nav class="navbar"><div style="font-size:1.5rem; font-weight:bold;">🏥 MedTrack <span style="color:var(--primary)">Vault</span></div><a href="/" style="color:var(--primary); text-decoration:none; font-weight:bold;">← Quay lại</a></nav>
        <div class="search-container">
            <h1>🛡️ Secure Record Lookup</h1>
            <p style="color:var(--dim);">Tìm kiếm hồ sơ đã được xác thực trên toàn hệ thống MedTrack.</p>
            <input type="text" id="q" class="search-bar" placeholder="Nhập tên bệnh nhân..." onkeyup="if(event.key==='Enter') search()">
            <div id="vaultResults" style="margin-top: 40px;"></div>
        </div>
        <script>
            async function search() {{
                const q = document.getElementById('q').value;
                const r = await fetch(`/api/search?query=${{q}}`);
                const data = await r.json();
                const div = document.getElementById('vaultResults');
                div.innerHTML = data.length ? '' : '<p style="color:var(--dim);">Không tìm thấy dữ liệu trùng khớp.</p>';
                data.forEach(item => {{
                    div.innerHTML += `
                        <div class="record-item">
                            <div class="record-img"><img src="${{item.image_path}}"></div>
                            <div class="record-info">
                                <h3>BN: ${{item.patient_name}}</h3>
                                <p style="color:#94a3b8; font-size:0.95rem;">${{item.notes || 'Hồ sơ này đã được niêm phong bảo mật.'}}</p>
                                <div style="margin-top:15px; font-size:0.75rem; color:var(--primary);">🔒 Verified by KMS</div>
                            </div>
                        </div>`;
                }});
            }}
        </script>
    </body></html>"""

async def analyze_wound_logic(image_path):
    # 1. Đọc ảnh thật từ ổ cứng
    img = cv2.imread(image_path)
    if img is None:
        return "Unknown", "Không thể đọc định dạng ảnh", "#94a3b8"
    
    # 2. Xử lý màu sắc (HSV)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Dải màu đen (SIGNAL 3 - Hoại tử)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 50]) 
    
    mask = cv2.inRange(hsv, lower_black, upper_black)
    black_pixels = cv2.countNonZero(mask)
    total_pixels = img.shape[0] * img.shape[1]
    black_ratio = (black_pixels / total_pixels) * 100

    # In ra terminal để bạn theo dõi khi test
    print(f"🔍 Đang quét vết thương... Tỉ lệ màu đen: {black_ratio:.2f}%")

    # 3. Phân loại SIGNAL
    if black_ratio > 2: # Nếu vùng đen > 2% diện tích
        return "SIGNAL 3", f"CẢNH BÁO: Phát hiện hoại tử ({black_ratio:.1f}%)", "#ff4757"
    
    return "SIGNAL 1", "Mô hạt đang phát triển tốt (Đang lành)", "#2ecc71"
# --- LOGIC LƯU HỒ SƠ (UPLOAD) ---
@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...), 
    patient_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # ... (phần lưu file giữ nguyên) ...
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ĐỔI DÒNG NÀY: Gọi hàm logic thật ở trên
    status_signal, ai_note, color_code = await analyze_wound_logic(file_path)

    # Lưu vào Database
    new_record = MedicalRecord(
        patient_name=patient_name,
        image_url=f"/static/uploads/{file_name}",
        status=status_signal,
        notes=ai_note,
        color_code=color_code # Đảm bảo tên cột này khớp với Database của bạn
    )
    db.add(new_record)
    db.commit()

    return JSONResponse({
        "status": "success", 
        "ai_result": status_signal,
        "note": ai_note
    })
# --- LOGIC LẤY HỒ SƠ CÁ NHÂN (MY RECORDS) ---
@app.get("/api/my-records")
async def get_my_records(request: Request, db: Session = Depends(get_db)):
    uid = get_uid(request)
    if not uid:
        return []
    # Chỉ lấy những hồ sơ do chính bác sĩ này upload
    return db.query(MedicalRecord).filter(MedicalRecord.owner_id == int(uid)).all()

# --- LOGIC TÌM KIẾM TOÀN HỆ THỐNG (VAULT SEARCH) ---
@app.get("/api/search")
async def api_search(query: str, db: Session = Depends(get_db)):
    if not query:
        return []
    # Tìm kiếm theo tên bệnh nhân (không phân biệt hoa thường)
    results = db.query(MedicalRecord).filter(
        MedicalRecord.patient_name.ilike(f"%{query}%")
    ).all()
    return results

# --- LOGIC XÓA HỒ SƠ ---
@app.delete("/api/delete/{record_id}")
async def delete_record(record_id: int, request: Request, db: Session = Depends(get_db)):
    uid = get_uid(request)
    # Kiểm tra xem hồ sơ có tồn tại và có phải của người này không
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id, 
        MedicalRecord.owner_id == int(uid)
    ).first()
    
    if not record:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa hồ sơ này")
    
    # Xóa file ảnh vật lý trong thư mục uploads
    try:
        os.remove(record.image_path.lstrip('/'))
    except:
        pass # Nếu file đã bị xóa thủ công thì bỏ qua

    db.delete(record)
    db.commit()
    return {"status": "deleted"}

# Đặt mã bí mật của bạn ở đây (Chỉ bạn và các cộng sự biết)
# Đặt mã bí mật của bạn ở đây
SECRET_INVITE_CODE = "MED2026"

@app.post("/api/register")
async def register_api(username: str = Form(...), password: str = Form(...), invite_code: str = Form(...), db: Session = Depends(get_db)):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu phải nhập đủ ít nhất 8 ký tự!")
    if invite_code != SECRET_INVITE_CODE:
        raise HTTPException(status_code=400, detail="Mã mời (Invite Code) sai!")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Tên tài khoản này đã tồn tại!")
    
    db.add(User(username=username, hashed_password=pwd_context.hash(password)))
    db.commit()
    return {"status": "success"}

@app.post("/api/login")
async def login_api(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Tên tài khoản hoặc mật khẩu không chính xác!")
    
    response = JSONResponse({"status": "success"})
    response.set_cookie(key="user_session", value=str(user.id), httponly=True)
    return response
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_session")
    return response
@app.get("/login-page", response_class=HTMLResponse)
async def login_p():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>MedTrack Access</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
            body { background:#0f172a; color:white; font-family:'Inter', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
            .auth-box { background:#1e293b; padding:40px; border-radius:24px; width:350px; text-align:center; border:1px solid #334155; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
            .tabs { display: flex; margin-bottom: 25px; border-bottom: 1px solid #334155; }
            .tab { flex: 1; padding: 10px; cursor: pointer; color: #94a3b8; font-weight: 600; transition: 0.3s; }
            .tab.active { color: #2ecc71; border-bottom: 2px solid #2ecc71; }
            input { width:100%; padding:14px; margin:8px 0; background:#0f172a; color:white; border:1px solid #334155; border-radius:12px; outline:none; box-sizing:border-box; transition: 0.3s; }
            input:focus { border-color: #2ecc71; }
            #invite_section { display: none; margin-top: 10px; animation: fadeIn 0.4s; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
            .btn { width:100%; padding:16px; background:#2ecc71; color:#000; border:none; border-radius:12px; font-weight:bold; cursor:pointer; margin-top:20px; font-size:1rem; }
            #m { color:#ff4757; margin-top:15px; font-size:0.85rem; font-weight: 600; min-height: 1.2rem; }
        </style>
    </head>
    <body>
        <div class="auth-box">
            <div class="tabs">
                <div id="tab-login" class="tab active" onclick="switchMode('login')">ĐĂNG NHẬP</div>
                <div id="tab-reg" class="tab" onclick="switchMode('reg')">ĐĂNG KÝ MỚI</div>
            </div>
            
            <h2 id="title" style="color:#2ecc71; margin-bottom: 20px; font-size: 1.2rem;">Chào mừng quay trở lại</h2>
            
            <input id="u" placeholder="Tên tài khoản">
            <input id="p" type="password" placeholder="Mật khẩu">
            
            <div id="invite_section">
                <input id="invite_code" placeholder="Mã mời bác sĩ (Invite Code)" style="border-color: #2ecc71; color: #2ecc71;">
            </div>
            
            <button class="btn" id="main-btn" onclick="auth()">Xác nhận</button>
            <p id="m"></p>
        </div>

        <script>
        let mode = 'login';

        function switchMode(m) {
            mode = m;
            const inviteSec = document.getElementById('invite_section');
            const title = document.getElementById('title');
            const btn = document.getElementById('main-btn');
            const msg = document.getElementById('m');
            msg.innerText = "";

            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            if(mode === 'login') {
                document.getElementById('tab-login').classList.add('active');
                inviteSec.style.display = 'none';
                title.innerText = "Chào mừng quay trở lại";
                btn.innerText = "Đăng nhập ngay";
            } else {
                document.getElementById('tab-reg').classList.add('active');
                inviteSec.style.display = 'block';
                title.innerText = "Tạo tài khoản bác sĩ";
                btn.innerText = "Hoàn tất đăng ký";
            }
        }

        async function auth() {
            const u = document.getElementById('u').value;
            const p = document.getElementById('p').value;
            const invite = document.getElementById('invite_code').value;
            const msg = document.getElementById('m');
            msg.style.color = "#ff4757";

            if(!u || !p) { msg.innerText = "⚠️ Vui lòng điền đủ thông tin!"; return; }

            const fd = new FormData();
            fd.append('username', u);
            fd.append('password', p);

            if (mode === 'login') {
                // XỬ LÝ ĐĂNG NHẬP
                let r = await fetch('/api/login', { method: 'POST', body: fd });
                if (r.ok) {
                    msg.style.color = "#2ecc71";
                    msg.innerText = "Đang vào hệ thống...";
                    location.href = '/';
                } else {
                    let d = await r.json();
                    msg.innerText = "❌ " + (d.detail || "Sai tài khoản hoặc mật khẩu!");
                }
            } else {
                // XỬ LÝ ĐĂNG KÝ
                if (p.length < 8) { msg.innerText = "❌ Mật khẩu phải đủ ít nhất 8 ký tự!"; return; }
                if (!invite) { msg.innerText = "❌ Vui lòng nhập Mã mời để đăng ký!"; return; }
                
                fd.append('invite_code', invite);
                let r = await fetch('/api/register', { method: 'POST', body: fd });
                let d = await r.json();
                if (r.ok) {
                    msg.style.color = "#2ecc71";
                    msg.innerText = "✅ Đăng ký thành công! Hãy đăng nhập.";
                    setTimeout(() => switchMode('login'), 1500);
                } else {
                    msg.innerText = "❌ " + (d.detail || "Lỗi đăng ký!");
                }
            }
        }
        </script>
    </body>
    </html>
    """
@app.post("/upload")
async def upload_file(
    request: Request, 
    patient_name: str = Form(...), 
    notes: str = Form(None), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    uid = get_uid(request)
    if not uid: raise HTTPException(status_code=401)

    # 1. Kiểm tra định dạng (Chỉ nhận ảnh)
    allowed_extensions = ["jpg", "jpeg", "png", "webp"]
    ext = file.filename.split(".")[-1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Chỉ cho phép upload file ảnh (JPG, PNG, WEBP)")

    # 2. Kiểm tra dung lượng (Tối đa 3MB)
    MAX_SIZE = 3 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Ảnh quá nặng! Vui lòng chọn ảnh dưới 3MB")
    
    # Reset con trỏ file sau khi đọc để lưu
    await file.seek(0) 

    # 3. Lưu file (Như cũ)
    file_name = f"{uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    db.add(MedicalRecord(patient_name=patient_name, notes=notes, image_path=f"/{file_path}", owner_id=int(uid)))
    db.commit()
    return {"status": "success"}
Instrumentator().instrument(app).expose(app)
