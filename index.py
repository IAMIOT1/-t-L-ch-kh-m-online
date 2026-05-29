import csv
import math
import random
import streamlit as st
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
def send_real_email(receiver_email, clinic_name, doctor_name, experience, phone, time, date):
    # 1. Cấu hình thông tin tài khoản gửi (Sử dụng một Gmail của bạn làm Server gửi)
    sender_email = "toinguyen7126@gmail.com"
    sender_password = "japg eyvh ontl dliw"  # Mật khẩu ứng dụng 16 ký tự của Google
    
    # 2. Tạo bố cục Email dạng HTML cho đẹp mắt
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🏥 [ĐẠI HỌC ĐẠI NAM] - XÁC NHẬN LỊCH HẸN KHÁM THÀNH CÔNG"
    message["From"] = sender_email
    message["To"] = receiver_email

    html_content = f"""
    <html>
      <body>
        <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; border-radius: 5px;">
            <h3 style="color: #007bff;">📧 XÁC NHẬN ĐẶT LỊCH KHÁM THÀNH CÔNG</h3>
            <p>Xin chào <b>{receiver_email}</b>, lịch hẹn khám bệnh của bạn đã được phê duyệt:</p>
            <hr>
            <p>🏥 <b>Địa điểm:</b> {clinic_name}</p>
            <p>👨‍⚕️ <b>Bác sĩ phụ trách:</b> BS. {doctor_name} ({experience})</p>
            <p>📞 <b>Hotline bác sĩ:</b> {phone}</p>
            <p>📅 <b>Thời gian:</b> <span style="color: #dc3545; font-weight: bold;">{time} ngày {date}</span></p>
            <hr>
            <p style="color: #6c757d; font-style: italic;">Vui lòng đến đúng giờ để tiến hành kiểm tra sức khỏe tốt nhất!</p>
        </div>
      </body>
    </html>
    """
    message.attach(MIMEText(html_content, "html", "utf-8"))

    # 3. Tiến hành kết nối Server SMTP Gmail và gửi đi
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Bảo mật kết nối
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False

# Cấu hình trang web Streamlit
st.set_page_config(page_title="Đại Học Đại Nam - Đặt Lịch Khám", page_icon="🏥", layout="centered")

# Cấu hình matplotlib để tránh lỗi font tiếng Việt hiển thị thành ô vuông
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# ==============================================================================
# HÀM ĐỌC / GHI DỮ LIỆU CSV (YÊU CẦU 1)
# ==============================================================================
def read_csv(file_name):
    data = []
    try:
        with open(file_name, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        st.error(f"Không tìm thấy file dữ liệu: {file_name}")
    return data

def write_appointment_to_csv(file_name, appointment):
    with open(file_name, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(appointment)

# ==============================================================================
# LOGIC XỬ LÝ & GIẢ LẬP BẢN ĐỒ (YÊU CẦU 2, 3, 5)
# ==============================================================================
# Thay thế hàm find_nearest_clinic cũ bằng 2 hàm xử lý tọa độ GPS thực tế này:
def haversine_distance(lat1, lon1, lat2, lon2):
    # Bán kính Trái Đất tính bằng km
    R = 6371.0
    
    rad_lat1 = math.radians(lat1)
    rad_lon1 = math.radians(lon1)
    rad_lat2 = math.radians(lat2)
    rad_lon2 = math.radians(lon2)
    
    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def find_nearest_clinic(home_lat, home_lng, clinics):
    nearest_clinic = None
    min_distance = float('inf')
    for clinic in clinics:
        # Trong file clinics.csv: x đóng vai trò Kinh độ (Lng), y đóng vai trò Vĩ độ (Lat)
        cx, cy = float(clinic['x']), float(clinic['y'])
        distance = haversine_distance(home_lat, home_lng, cy, cx)
        if distance < min_distance:
            min_distance = distance
            nearest_clinic = clinic
    return nearest_clinic, min_distance

def find_doctors_by_symptom(symptom, clinic_id, doctors):
    symptom_list = symptom.lower().split(',')
    matched_doctors = []
    for doc in doctors:
        if doc['clinic_id'] == clinic_id:
            # Xử lý trường hợp symptoms có dấu ngoặc kép
            symptoms_str = doc['symptoms'].strip('"')
            doc_symptoms = [s.strip().lower() for s in symptoms_str.split(',')]
            for s in symptom_list:
                s = s.strip()
                if any(s in ds or ds in s for ds in doc_symptoms):
                    matched_doctors.append(doc)
                    break
    return matched_doctors

def check_and_schedule(doctor_id, date_str, time_str, appointments):
    for app in appointments:
        if app['doctor_id'] == str(doctor_id) and app['date'] == date_str and app['time_slot'] == time_str:
            return False # Trùng lịch
    return True # Trống lịch

def suggest_alternative_slots(doctor_id, date_str, appointments):
    working_slots = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    return [slot for slot in working_slots if check_and_schedule(doctor_id, date_str, slot, appointments)]

# Hàm vẽ bản đồ giả lập đường đi
def draw_simulation_map(home_x, home_y, target_clinic, all_clinics):
    # Tạo một điểm gốc thực tế (Ví dụ: khu vực Hà Nội) để làm tâm chuyển đổi tọa độ phẳng sang Lat/Lng
    BASE_LAT = 21.0285
    BASE_LNG = 105.8542
    SCALE = 0.01 # 1 đơn vị X, Y trong file của bạn tương đương khoảng 1.1km trên bản đồ thực
    
    # Chuyển đổi tọa độ nhà của bạn
    home_lat = BASE_LAT + (home_y * SCALE)
    home_lng = BASE_LNG + (home_x * SCALE)
    
    # Khởi tạo bản đồ Folium tại vị trí nhà bạn
    m = folium.Map(
        location=[home_lat, home_lng], 
        zoom_start=14, 
        control_scale=True
    )
    
    # Thêm các lớp bản đồ (Giao diện Bản đồ đường phố và Bản đồ vệ tinh giống Google Map)
    folium.TileLayer('openstreetmap', name="Bản đồ đường phố").add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Bản đồ Vệ tinh (Google)'
    ).add_to(m)

    # 1. Đánh dấu vị trí "Nhà của bạn" (Marker màu Đỏ, icon ngôi nhà)
    folium.Marker(
        location=[home_lat, home_lng],
        popup=f"<b>Vị trí của bạn</b><br>Tọa độ gốc: ({home_x}, {home_y})",
        tooltip="Bạn ở đây!",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)
    
    # 2. Đánh dấu tất cả các phòng khám khác (Marker màu cam, icon bệnh viện nhỏ)
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        c_lat = BASE_LAT + (cy * SCALE)
        c_lng = BASE_LNG + (cx * SCALE)
        
        # Nếu không phải phòng khám được chọn gần nhất
        if clinic['id'] != target_clinic['id']:
            folium.Marker(
                location=[c_lat, c_lng],
                popup=f"<b>{clinic['name']}</b>",
                tooltip=clinic['name'],
                icon=folium.Icon(color='orange', icon='plus', prefix='fa')
            ).add_to(m)

    # 3. Đánh dấu phòng khám GẦN NHẤT ĐƯỢC CHỌN (Marker màu xanh lá, icon bệnh viện lớn)
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])
    target_lat = BASE_LAT + (target_y * SCALE)
    target_lng = BASE_LNG + (target_x * SCALE)
    
    distance = math.sqrt((target_x - home_x)**2 + (target_y - home_y)**2)
    
    folium.Marker(
        location=[target_lat, target_lng],
        popup=f"<div style='width:200px;'><b>🏥 {target_clinic['name']}</b><br>Đây là phòng khám gần bạn nhất!</div>",
        tooltip=f"Đích đến: {target_clinic['name']}",
        icon=folium.Icon(color='green', icon='hospital-o', prefix='fa')
    ).add_to(m)
    
    # 4. Vẽ đường nối lộ trình di chuyển (Đường Polyline màu xanh dương đậm nét đứt như Google Maps)
    points = [[home_lat, home_lng], [target_lat, target_lng]]
    
    folium.PolyLine(
        points,
        color="#1a73e8",       # Màu xanh đặc trưng của Google Maps
        weight=5,              # Độ dày đường vẽ
        opacity=0.8,
        tooltip=f"Lộ trình tối ưu: {distance:.2f} km"
    ).add_to(m)
    
    # Thêm công cụ chọn hiển thị loại bản đồ (Layer Control) ở góc trên bên phải
    folium.LayerControl(position='topright').add_to(m)
    
    return m

# ==============================================================================
# GIAO DIỆN ỨNG DỤNG WEB (STREAMLIT UI)
# ==============================================================================
st.title("🏥 HỆ THỐNG ĐẶT LỊCH KHÁM ONLINE")
st.subheader("Khoa CNTT - Trường Đại học Đại Nam")
st.markdown("---")

# Tải dữ liệu đầu vào
clinics = read_csv('clinics.csv')
doctors = read_csv('doctors.csv')
appointments = read_csv('appointments.csv')

if clinics and doctors:
    # ------------------ KHU VỰC NHẬP THÔNG TIN BỆNH NHÂN ------------------
    st.header("1. Nhập thông tin bệnh nhân")
    
    patient_email = st.text_input("📩 Email nhận nhắc lịch ", placeholder="nguyenvandan@gmail.com")
    
    # --------------------------------------------------------------------------
    # NÂNG CẤP VỊ TRÍ SỐ 2: TỰ ĐỘNG ĐỊNH VỊ GPS THỜI GIAN THỰC QUA TRÌNH DUYỆT
    # --------------------------------------------------------------------------

    st.write("📍 **Xác định vị trí hiện tại của bạn:**")
    
    # Khởi tạo giá trị mặc định trong Session State nếu chưa từng quét GPS (Mặc định ở Hà Nội)
    if 'gps_lat' not in st.session_state: 
        st.session_state['gps_lat'] = 21.0285 
    if 'gps_lng' not in st.session_state: 
        st.session_state['gps_lng'] = 105.8542

    # Thành phần trung gian nhận chuỗi dữ liệu "Lat,Lng" từ Javascript
    geo_data = st.text_input("Tọa độ thiết bị nhận diện (Lat,Lng):", value=f"{st.session_state['gps_lat']},{st.session_state['gps_lng']}", key="geo_location")
    
    # Tách chuỗi dữ liệu tọa độ ra thành 2 biến số thực để truyền xuống thuật toán xử lý phía dưới
    try:
        home_lat, home_lng = map(float, geo_data.split(','))
        st.session_state['gps_lat'] = home_lat
        st.session_state['gps_lng'] = home_lng
    except:
        home_lat, home_lng = st.session_state['gps_lat'], st.session_state['gps_lng']
        
    st.success(f"🗺️ Hệ thống đang định vị tại: **Vĩ độ (Lat):** {home_lat} | **Kinh độ (Lng):** {home_lng}")
    # --------------------------------------------------------------------------
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn ", placeholder="đau bụng , ho")

    # Bước 1: Tìm phòng khám gần nhất dựa trên tọa độ nhà
    nearest_clinic, dist = find_nearest_clinic(home_lat, home_lng, clinics)
    
    # Bước 2: Tìm bác sĩ phù hợp với triệu chứng TẠI phòng khám gần nhất đó
    matched_doctors = find_doctors_by_symptom(symptom_input, nearest_clinic['id'], doctors)

    st.markdown("---")
    st.header("2. Kết quả tìm kiếm & Bản đồ lộ trình")
    
    # Hiển thị phòng khám gần nhất (Yêu cầu 2)
    st.info(f"📍 **Phòng khám gần nhất:** {nearest_clinic['name']} (Khoảng cách tính toán: {dist:.2f} km)")
    
    # --------------------------------------------------------------------------
    # NÂNG CẤP VỊ TRÍ SỐ 2: TỰ ĐỘNG ĐỊNH VỊ GPS THỜI GIAN THỰC QUA TRÌNH DUYỆT
    # --------------------------------------------------------------------------
    st.write("📍 **Xác định vị trí hiện tại của bạn:**")
    st.caption("💡 Mẹo: Bạn có thể click chuột trực tiếp vào vị trí của mình trên bản đồ dưới đây để hệ thống tự lấy tọa độ thực tế!")

    # Nhúng một cụm HTML/JavaScript để kích hoạt API định vị của thiết bị
    loc_button_html = """
    <div style="text-align: center; margin-bottom: 10px;">
        <button onclick="getLocation()" style="background-color: #2196f3; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            🎯 Nhấp để tự động lấy vị trí GPS từ thiết bị của bạn
        </button>
        <p id="status" style="color: #666; font-size: 13px; margin-top: 8px; font-style: italic;"></p>
    </div>
    <script>
        function getLocation() {
            const status = document.getElementById('status');
            if (!navigator.geolocation) {
                status.textContent = 'Trình duyệt này không hỗ trợ định vị GPS.';
            } else {
                status.textContent = 'Đang quét tìm tọa độ vệ tinh...';
                navigator.geolocation.getCurrentPosition(success, error);
            }
        }
        function success(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            document.getElementById('status').innerHTML = '<span style="color: #4caf50; font-weight: bold;">✔️ Đã cập nhật tọa độ thực thành công!</span>';
            // Đẩy ngược dữ liệu Lat,Lng từ JavaScript về widget text_input của Streamlit
            window.parent.postMessage({
                type: 'streamlit:set_widget_value',
                from: 'geo_location',
                value: lat + ',' + lng
            }, '*');
        }
        function error() {
            document.getElementById('status').innerHTML = '<span style="color: #f44336;">❌ Không lấy được GPS. Hãy chắc chắn bạn đã nhấn "Cho phép" (Allow) quyền vị trí trên trình duyệt.</span>';
        }
    </script>
    """
    # Render nút bấm lên giao diện web
    components.html(loc_button_html, height=80)
    
    # Tạo một bản đồ mini để người dùng tự chấm vị trí của mình
    m_select = folium.Map(location=[home_lat, home_lng], zoom_start=13)
    folium.Marker(
        [home_lat, home_lng], 
        tooltip="Vị trí đã chọn", 
        icon=folium.Icon(color='red', icon='user', prefix='fa')
    ).add_to(m_select)
    
    # Hiển thị bản đồ chọn và bắt sự kiện click chuột
    st_data = st_folium(m_select, width=700, height=250, key="map_picker")
    
    # Nếu người dùng click vào bản đồ, cập nhật ngay tọa độ đó vào hệ thống
    if st_data and st_data.get("last_clicked"):
        st.session_state['gps_lat'] = st_data["last_clicked"]["lat"]
        st.session_state['gps_lng'] = st_data["last_clicked"]["lng"]
        home_lat = st.session_state['gps_lat']
        home_lng = st.session_state['gps_lng']
        
    st.success(f"🗺️ Đã xác định vị trí của bạn tại: **Lat:** {home_lat:.4f} | **Lng:** {home_lng:.4f}")
    # --------------------------------------------------------------------------

    if not matched_doctors:
        st.warning(f"❌ Không tìm thấy bác sĩ phù hợp với triệu chứng '{symptom_input}' tại phòng khám gần nhất.")
    else:
        # Chọn bác sĩ đáp ứng triệu chứng (Yêu cầu 3)
        selected_doctor = matched_doctors[0]
        
        # Đọc thêm thông tin mở rộng (phone, experience) nếu có, tránh crash nếu file cũ thiếu cột
        phone_num = selected_doctor.get('phone', 'Chưa cập nhật')
        exp_year = selected_doctor.get('experience', 'Chưa rõ')
        
        st.success(f"👨‍⚕️ **Bác sĩ được chỉ định:** {selected_doctor['name']} | **Chuyên khoa:** {selected_doctor['specialty']} | **Kinh nghiệm:** {exp_year}")

        st.markdown("---")
        st.header("3. Chọn thời gian & Đặt lịch")
        
        # Hiển thị đồng hồ thời gian thực chạy giây, phút, giờ (dùng thời gian client)
        import streamlit.components.v1 as components
        clock_html = """
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; border: 2px solid #2196f3; text-align: center;">
            <h3 style="margin: 0; color: #1565c0;">🕐 Đồng hồ thời gian thực (Client)</h3>
            <div id="clock" style="font-size: 32px; font-weight: bold; color: #0d47a1; margin-top: 10px;">--:--:--</div>
            <div id="date" style="font-size: 18px; color: #1976d2; margin-top: 5px;">--/--/----</div>
        </div>
        <script>
            function updateClock() {
                const now = new Date();
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const year = now.getFullYear();
                
                document.getElementById('clock').textContent = hours + ':' + minutes + ':' + seconds;
                document.getElementById('date').textContent = day + '/' + month + '/' + year;
            }
            updateClock();
            setInterval(updateClock, 1000);
        </script>
        """
        components.html(clock_html, height=150)
        
        # Chọn thời gian mong muốn (Yêu cầu 4)
        desired_date = st.date_input("📅 Chọn ngày khám:").strftime("%Y-%m-%d")
        desired_time = st.selectbox("⏰ Chọn khung giờ mong muốn:", ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"], index=1)

        # Thêm JavaScript để kiểm tra thời gian client-side trước khi submit
        validation_js = f"""
        <script>
        // Tìm nút đặt lịch và thêm validation
        document.addEventListener('DOMContentLoaded', function() {{
            const buttons = document.querySelectorAll('button[kind="primary"]');
            buttons.forEach(button => {{
                if (button.textContent.includes('TIẾN HÀNH ĐẶT LỊCH')) {{
                    button.addEventListener('click', function(e) {{
                        const selectedDate = '{desired_date}';
                        const selectedTime = '{desired_time}';
                        const selectedDateTime = new Date(selectedDate + 'T' + selectedTime + ':00');
                        const now = new Date();
                        
                        if (selectedDateTime < now) {{
                            e.preventDefault();
                            e.stopPropagation();
                            alert('❌ Khung giờ ' + selectedTime + ' ngày ' + selectedDate + ' đã qua!\\nVui lòng chọn thời gian trong tương lai.');
                        }}
                    }});
                }}
            }});
        }});
        </script>
        """
        components.html(validation_js, height=0)
# Nút bấm tiến hành đặt lịch
        if st.button("🏥 TIẾN HÀNH ĐẶT LỊCH"):
            # Kiểm tra xem khung giờ đã qua chưa bằng thời gian thực Việt Nam (GMT+7)
            from datetime import datetime
            import pytz
            
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            current_datetime = datetime.now(vietnam_tz).replace(tzinfo=None)
            
            selected_datetime = datetime.strptime(f"{desired_date} {desired_time}", "%Y-%m-%d %H:%M")
            
            if selected_datetime < current_datetime:
                st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} đã qua so với thời gian thực! Vui lòng chọn thời gian trong tương lai.")
                st.info("👉 Vui lòng chọn lại ngày và khung giờ phù hợp.")
            else:
                is_free = check_and_schedule(selected_doctor['id'], desired_date, desired_time, appointments)
                
                if is_free:
                    # 1. Lưu dữ liệu vào file CSV
                    new_app_id = len(appointments) + 1
                    write_appointment_to_csv('appointments.csv', [new_app_id, patient_email, selected_doctor['id'], desired_date, desired_time])
                    
                    # 2. Gọi hàm gửi thư thật (Hệ thống chạy ngầm gửi tới hòm thư người dùng)
                    # Lưu ý: Đảm bảo bạn đã định nghĩa hàm send_real_email ở phía trên đầu file index.py
                    send_real_email(
                        patient_email, 
                        nearest_clinic['name'], 
                        selected_doctor['name'], 
                        selected_doctor['experience'], 
                        selected_doctor['phone'], 
                        desired_time, 
                        desired_date
                    )
                    
                    # 3. Lưu nội dung HTML Email vào session_state để giữ lại giao diện sau khi rerun
                    st.session_state['booking_success_email'] = f"""
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <h5 style="color: #007bff; margin-top: 0;">📧 HỆ THỐNG EMAIL TỰ ĐỘNG — GỬI TỚI: {patient_email}</h5>
                        <p>Xin chào! Lịch hẹn khám bệnh của bạn đã được phê duyệt thành công trên hệ thống và một bản sao đã được gửi tới hòm thư của bạn:</p>
                        <hr style="border-top: 1px solid #dee2e6;">
                        <p>🏥 <b>Địa điểm:</b> {nearest_clinic['name']}</p>
                        <p>👨‍⚕️ <b>Bác sĩ phụ trách:</b> BS. {selected_doctor['name']} ({selected_doctor['experience']})</p>
                        <p>📞 <b>Hotline liên hệ bác sĩ:</b> {selected_doctor['phone']}</p>
                        <p>📅 <b>Thời gian:</b> <span style="color: #dc3545; font-weight: bold;">{desired_time} ngày {desired_date}</span></p>
                        <hr style="border-top: 1px solid #dee2e6;">
                        <p style="font-size: 0.9em; color: #6c757d; font-style: italic;">👉 Vui lòng đến đúng giờ để tiến hành kiểm tra sức khỏe tốt nhất!</p>
                    </div>
                    <br>
                    """
                    # Bật cờ kích hoạt hiệu ứng bóng bay sau khi reload
                    st.session_state['show_balloons'] = True
                    
                    # 4. Khởi động lại app để nạp lại bảng dữ liệu lịch hẹn mới lập tức
                    st.rerun()
                
                else:
                    st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} của Bác sĩ {selected_doctor['name']} đã bị trùng lịch!")
                    suggestions = suggest_alternative_slots(selected_doctor['id'], desired_date, appointments)
                    if suggestions:
                        st.warning(f"💡 Đề xuất các khung giờ thay thế còn trống trong ngày: {', '.join(suggestions)}")
                        st.info(f"👉 Vui lòng chọn lại một trong các khung giờ trống phía trên để đặt lịch.")
                    else:
                        st.error("Rất tiếc, bác sĩ này đã kín lịch hoàn toàn trong ngày hôm nay. Vui lòng chọn ngày khác.")

    # ==============================================================================
    # NƠI HIỂN THỊ EMAIL TRÊN WEB SAU KHI RERUN
    # (Đoạn này đặt ngay phía trên subheader "Danh sách lịch hẹn đã đăng ký")
    # ==============================================================================
    if 'booking_success_email' in st.session_state:
        if st.session_state.get('show_balloons', False):
            st.balloons()
            st.success("✔️ Đặt lịch thành công! Chi tiết lịch hẹn đã được đồng bộ vào hệ thống dữ liệu.")
            st.session_state['show_balloons'] = False # Tắt cờ hiệu để tránh lặp lại hiệu ứng
            
        st.markdown(st.session_state['booking_success_email'], unsafe_allow_html=True)