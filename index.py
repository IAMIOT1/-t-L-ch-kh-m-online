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
import requests
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import pytz
from datetime import datetime, time 

def send_real_email(receiver_email, clinic_name, doctor_name, experience, phone, time, date):
    sender_email = "toinguyen7126@gmail.com"
    sender_password = "japg eyvh ontl dliw"
    
    message = MIMEMultipart("mixed") # Đổi sang mixed để đính kèm được file
    message["Subject"] = f"🏥 [ĐẠI HỌC ĐẠI NAM] - XÁC NHẬN LỊCH HẸN KHÁM THÀNH CÔNG"
    message["From"] = sender_email
    message["To"] = receiver_email

    # --- TẠO NỘI DUNG HTML ---
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
            <p style="color: #6c757d; font-style: italic;">👉 Đã đính kèm file lịch bên dưới. Mở file để thêm vào Google Calendar và nhận thông báo nhắc trước 1 tiếng!</p>
        </div>
      </body>
    </html>
    """
    message.attach(MIMEText(html_content, "html", "utf-8"))

    # --- TẠO FILE LỊCH .ICS (NHẮC TRƯỚC 10 GIÂY) ---
    # Chuyển đổi date/time sang định dạng datetime
    dt_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_end = dt_start + timedelta(hours=1)
    
    # Định dạng chuỗi cho iCalendar
    def format_ics(dt): return dt.strftime('%Y%m%dT%H%M00Z')
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Dai Nam University//Appointment//EN
BEGIN:VEVENT
SUMMARY:Lịch khám tại {clinic_name}
DTSTART:{format_ics(dt_start)}
DTEND:{format_ics(dt_end)}
DESCRIPTION:Lịch hẹn với BS. {doctor_name}. Vui lòng đến đúng giờ.
BEGIN:VALARM
TRIGGER:-PT10S
ACTION:DISPLAY
DESCRIPTION:Nhắc nhở: Lịch khám của bạn bắt đầu sau 10 giây nữa!
END:VALARM
END:VEVENT
END:VCALENDAR"""

    # --- ĐÍNH KÈM FILE .ICS VÀO EMAIL ---
    part = MIMEBase('application', 'calendar; name=appointment.ics')
    part.set_payload(ics_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="appointment.ics"')
    message.attach(part)

    # --- GỬI EMAIL ---
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False

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
# LOGIC XỬ LÝ & BẢN ĐỒ THỰC TẾ (YÊU CẦU 2, 3, 5)
# ==============================================================================
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

# Hàm vẽ bản đồ lộ trình tối ưu duy nhất dựa trên tọa độ thực Lat/Lng

def draw_simulation_map(home_lat, home_lng, target_clinic, all_clinics):
    # Khởi tạo bản đồ Folium tập trung tại vị trí người dùng
    m = folium.Map(location=[home_lat, home_lng], zoom_start=14, control_scale=True)
    
    # Cấu hình các layer bản đồ đường phố và vệ tinh
    folium.TileLayer('openstreetmap', name="Bản đồ đường phố").add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Bản đồ Vệ tinh (Google)'
    ).add_to(m)

    # 1. Đánh dấu vị trí Người dùng (Màu đỏ)
    folium.Marker(
        location=[home_lat, home_lng],
        popup=f"<b>Vị trí của bạn</b><br>Tọa độ thực: ({home_lat:.4f}, {home_lng:.4f})",
        tooltip="Bạn ở đây!",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)
    
    # 2. Đánh dấu các phòng khám vệ tinh khác xung quanh (Màu cam)
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        if clinic['id'] != target_clinic['id']:
            folium.Marker(
                location=[cy, cx],
                popup=f"<b>{clinic['name']}</b>",
                tooltip=clinic['name'],
                icon=folium.Icon(color='orange', icon='plus', prefix='fa')
            ).add_to(m)

    # 3. Đánh dấu phòng khám GẦN NHẤT được hệ thống chọn (Màu xanh lá)
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])  # x là Lng, y là Lat
    folium.Marker(
        location=[target_y, target_x],
        popup=f"<div style='width:200px;'><b>🏥 {target_clinic['name']}</b><br>Đây là phòng khám gần bạn nhất!</div>",
        tooltip=f"Đích đến: {target_clinic['name']}",
        icon=folium.Icon(color='green', icon='hospital-o', prefix='fa')
    ).add_to(m)
    
    # 4. 🔥 GOOGLE MAPS ROUTING: Gọi API OSRM để lấy đường đi thực tế chạy theo các tuyến phố
    try:
        # Định dạng URL API OSRM: kinh_độ,vĩ_độ của điểm đi và điểm đến
        url = f"http://router.project-osrm.org/route/v1/driving/{home_lng},{home_lat};{target_x},{target_y}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5).json()
        
        if response.get("code") == "Ok":
            # Trích xuất danh sách các điểm tọa độ thật trên đường phố từ API
            geometry = response["routes"][0]["geometry"]["coordinates"]
            # OSRM trả về [Kinh độ, Vĩ độ], cần đảo ngược lại thành [Vĩ độ, Kinh độ] để Folium hiểu
            street_route_points = [[coord[1], coord[0]] for coord in geometry]
            
            # Lấy thông tin khoảng cách thực tế di chuyển trên đường (quy đổi từ mét sang km)
            real_distance_km = response["routes"][0]["distance"] / 1000
            duration_mins = response["routes"][0]["duration"] / 60
            
            # Vẽ đường lót mờ tạo hiệu ứng đường đi đổ bóng (Shadow Path)
            folium.PolyLine(street_route_points, color="#93c5fd", weight=8, opacity=0.5).add_to(m)
            
            # Vẽ đường lộ trình chính xác màu xanh đậm bám theo đường phố
            folium.PolyLine(
                street_route_points, 
                color="#1a73e8", 
                weight=4, 
                opacity=0.9, 
                tooltip=f"Tuyến đường thực tế: {real_distance_km:.2f} km - Dự kiến đi: {duration_mins:.0f} phút"
            ).add_to(m)
            
        else:
            # Nếu API lỗi, tự động chuyển về vẽ đường thẳng để không làm sập ứng dụng
            folium.PolyLine([[home_lat, home_lng], [target_y, target_x]], color="#ef4444", weight=4, opacity=0.8).add_to(m)
            
    except Exception as e:
        # Xử lý trường hợp mất mạng hoặc API không phản hồi
        folium.PolyLine([[home_lat, home_lng], [target_y, target_x]], color="#ef4444", weight=4, opacity=0.8).add_to(m)
    
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
    
    

    # Khởi tạo giá trị mặc định tạm thời trong Session State nếu chưa nhận được GPS
    if 'gps_lat' not in st.session_state: 
        st.session_state['gps_lat'] = 21.0285 
    if 'gps_lng' not in st.session_state: 
        st.session_state['gps_lng'] = 105.8542

    # --- SỬ DỤNG THƯ VIỆN ĐỂ XIN QUYỀN VÀ TRÍCH XUẤT GPS THỰC TẾ ---
    from streamlit_js_eval import get_geolocation
    
    st.markdown("### 🛰️ Đang đồng bộ định vị GPS từ trình duyệt...")
    location = get_geolocation()

    # Nếu trình duyệt trả về tọa độ thành công, cập nhật ngay vào hệ thống
    if location and 'coords' in location:
        st.session_state['gps_lat'] = float(location['coords']['latitude'])
        st.session_state['gps_lng'] = float(location['coords']['longitude'])

    home_lat = st.session_state['gps_lat']
    home_lng = st.session_state['gps_lng']
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn ", placeholder="đau bụng , ho")

    # Bước 1: Tìm phòng khám gần nhất dựa trên tọa độ đã xác định để làm gợi ý mặc định
    nearest_clinic, dist = find_nearest_clinic(home_lat, home_lng, clinics)

# ==============================================================================
    # 2. KẾT QUẢ TÌM KIẾM & BẢN ĐỒ LỘ TRÌNH (TỐI ƯU TỐC ĐỘ ⚡)
    # ==============================================================================
    st.markdown("---")
    st.header("2. Kết quả tìm kiếm & Bản đồ lộ trình")
    st.write("📍 **Xác định vị trí và chọn cơ sở khám bệnh:**")

    # Hệ số điều chỉnh quãng đường thực tế (Đường phố thường dài hơn đường chim bay ~1.3 lần)
    URBAN_FACTOR = 1.3 

    # Sắp xếp danh sách phòng khám bằng công thức toán học (Tốc độ tức thì, KHÔNG gọi API)
    # Cách này giúp danh sách hiện ra ngay lập tức mà không cần chờ đợi
    sorted_clinics = sorted(
        clinics, 
        key=lambda c: haversine_distance(home_lat, home_lng, float(c['y']), float(c['x'])) * URBAN_FACTOR
    )

    # Tạo danh sách hiển thị cho selectbox
    clinic_options = [
        f"{c['name']} (Ước tính: {(haversine_distance(home_lat, home_lng, float(c['y']), float(c['x'])) * URBAN_FACTOR):.2f} km - Đ/c: {c['address']})" 
        for c in sorted_clinics
    ]

    # Thanh selectbox cho phép người dùng chọn
    selected_option = st.selectbox(
        "🏥 Danh sách phòng khám (Sắp xếp theo quãng đường ước tính từ gần đến xa):",
        options=clinic_options,
        index=0
    )

    # Lấy đối tượng phòng khám được chọn
    chosen_index = clinic_options.index(selected_option)
    current_clinic = sorted_clinics[chosen_index]

    # Hiển thị khoảng cách ước tính
    st.info(f"🏥 **Cơ sở đang được chọn:** {current_clinic['name']} (Khoảng cách ước tính: {(haversine_distance(home_lat, home_lng, float(current_clinic['y']), float(current_clinic['x'])) * URBAN_FACTOR):.2f} km)")

    # 🔥 HIỂN THỊ BẢN ĐỒ: Chỉ khi này mới gọi API OSRM để vẽ vệt chỉ đường chính xác
    # Vì chỉ gọi cho 1 phòng khám duy nhất, bản đồ sẽ load rất nhanh
    with st.spinner("Đang đồng bộ bản đồ vệ tinh và vẽ lộ trình thực tế..."):
        map_obj = draw_simulation_map(home_lat, home_lng, current_clinic, sorted_clinics)
        st_data = st_folium(map_obj, width=700, height=450, key="integrated_map_picker")
        
    # Lắng nghe sự kiện click thay đổi vị trí trực tiếp trên bản đồ
    if st_data and st_data.get("last_clicked"):
        click_lat = st_data["last_clicked"]["lat"]
        click_lng = st_data["last_clicked"]["lng"]
        if click_lat != st.session_state['gps_lat'] or click_lng != st.session_state['gps_lng']:
            st.session_state['gps_lat'] = click_lat
            st.session_state['gps_lng'] = click_lng
            st.rerun()

    st.success(f"🗺️ Tọa độ đang chọn: **Vĩ độ:** {home_lat:.4f} | **Kinh độ:** {home_lng:.4f}")
    
    # Bước 2: Tìm bác sĩ phù hợp với triệu chứng TẠI phòng khám được chọn
    matched_doctors = find_doctors_by_symptom(symptom_input, current_clinic['id'], doctors)

    if not matched_doctors:
        st.warning(f"❌ Không tìm thấy bác sĩ phù hợp với triệu chứng '{symptom_input}' tại {current_clinic['name']}. Vui lòng thử nhập triệu chứng khác hoặc chọn cơ sở khác trong danh sách.")
    else:
        selected_doctor = matched_doctors[0]
        phone_num = selected_doctor.get('phone', 'Chưa cập nhật')
        exp_year = selected_doctor.get('experience', 'Chưa rõ')
        
        st.success(f"👨‍⚕️ **Bác sĩ được chỉ định:** {selected_doctor['name']} | **Chuyên khoa:** {selected_doctor['specialty']} | **Kinh nghiệm:** {exp_year}")

        st.markdown("---")
        st.header("3. Chọn thời gian & Đặt lịch")
        
        # Hiển thị đồng hồ thời gian thực chạy giây, phút, giờ
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
        

# --- CẤU HÌNH CHỌN NGÀY VÀ GIỜ ---
desired_date = st.date_input("📅 Chọn ngày khám:")
desired_date_str = desired_date.strftime("%Y-%m-%d")

mode = st.radio("Chế độ chọn giờ:", ["Chọn giờ có sẵn", "Tự nhập giờ"])

desired_time = None 

if mode == "Chọn giờ có sẵn":
    # Danh sách giờ có sẵn
    option = st.selectbox("⏰ Khung giờ:", ["08:00", "09:00", "10:00", "14:00", "15:00"])
    desired_time = option
    st.success(f"Đã chọn: {desired_time}")
else:
    # Người dùng tự chọn giờ, không dùng step để cho phép chọn linh hoạt
    selected_time_obj = st.time_input("⏰ Chọn thời gian (07:00 - 18:00):", value=time(8, 0))
    
    # Kiểm tra ràng buộc giờ hành chính
    if selected_time_obj < time(7, 0) or selected_time_obj > time(18, 0):
        st.error("❌ Vui lòng chọn khung giờ từ 07:00 đến 18:00!")
        desired_time = None # Vô hiệu hóa nút đặt lịch nếu chọn sai giờ
    else:
        desired_time = selected_time_obj.strftime("%H:%M")
        st.success(f"Đã chọn: {desired_time}")

# --- TIẾN HÀNH ĐẶT LỊCH ---
# Nút chỉ xuất hiện và hoạt động khi desired_time hợp lệ
if desired_time:
    if st.button("🏥 TIẾN HÀNH ĐẶT LỊCH"):
        # Đưa logic xử lý đặt lịch của bạn vào đây
        # Ví dụ: is_free = check_and_schedule(...)
        st.info(f"Đang xử lý đặt lịch: {desired_date_str} lúc {desired_time}...")
        
        # Thêm logic gọi hàm đặt lịch tại đây để đồng bộ với hệ thống của bạn

        # Đã loại bỏ chữ f để tránh lỗi xử lý dấu ngoặc nhọn của JavaScript
        validation_js = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const buttons = document.querySelectorAll('button[kind="primary"]');
            buttons.forEach(button => {
                if (button.textContent.includes('TIẾN HÀNH ĐẶT LỊCH')) {
                    button.addEventListener('click', function(e) {
                        // Kiểm tra trực tiếp tại Client
                    });
                }
            });
        });
        </script>
        """
        components.html(validation_js, height=0)

        if st.button("🏥 TIẾN HÀNH ĐẶT LỊCH"):
            from datetime import datetime
            import pytz
            
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            current_datetime = datetime.now(vietnam_tz).replace(tzinfo=None)
            selected_datetime = datetime.strptime(f"{desired_date_str} {desired_time}", "%Y-%m-%d %H:%M")
            
            if selected_datetime < current_datetime:
                st.error(f"❌ Khung giờ {desired_time} ngày {desired_date_str} đã qua so với thời gian thực! Vui lòng chọn thời gian trong tương lai.")
            else:
                is_free = check_and_schedule(selected_doctor['id'], desired_date_str, desired_time, appointments)
                
                if is_free:
                    new_app_id = len(appointments) + 1
                    write_appointment_to_csv('appointments.csv', [new_app_id, patient_email, selected_doctor['id'], desired_date_str, desired_time])
                    
                    send_real_email(
                        patient_email, 
                        nearest_clinic['name'], 
                        selected_doctor['name'], 
                        selected_doctor['experience'], 
                        selected_doctor['phone'], 
                        desired_time, 
                        desired_date_str
                    )
                    
                    st.session_state['booking_success_email'] = f"""
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <h5 style="color: #007bff; margin-top: 0;">📧 HỆ THỐNG EMAIL TỰ ĐỘNG — GỬI TỚI: {patient_email}</h5>
                        <p>Xin chào! Lịch hẹn khám bệnh của bạn đã được phê duyệt thành công trên hệ thống và một bản sao đã được gửi tới hòm thư của bạn:</p>
                        <hr style="border-top: 1px solid #dee2e6;">
                        <p>🏥 <b>Địa điểm:</b> {nearest_clinic['name']}</p>
                        <p>👨‍⚕️ <b>Bác sĩ phụ trách:</b> BS. {selected_doctor['name']} ({selected_doctor['experience']})</p>
                        <p>📞 <b>Hotline liên hệ bác sĩ:</b> {selected_doctor['phone']}</p>
                        <p>📅 <b>Thời gian:</b> <span style="color: #dc3545; font-weight: bold;">{desired_time} ngày {desired_date_str}</span></p>
                        <hr style="border-top: 1px solid #dee2e6;">
                        <p style="font-size: 0.9em; color: #6c757d; font-style: italic;">👉 Vui lòng đến đúng giờ để tiến hành kiểm tra sức khỏe tốt nhất!</p>
                    </div>
                    <br>
                    """
                    st.session_state['show_balloons'] = True
                    st.rerun()
                else:
                    st.error(f"❌ Khung giờ {desired_time} ngày {desired_date_str} của Bác sĩ {selected_doctor['name']} đã bị trùng lịch!")
                    suggestions = suggest_alternative_slots(selected_doctor['id'], desired_date_str, appointments)
                    if suggestions:
                        st.warning(f"💡 Đề xuất các khung giờ thay thế còn trống trong ngày: {', '.join(suggestions)}")

    if 'booking_success_email' in st.session_state:
        if st.session_state.get('show_balloons', False):
            st.balloons()
            st.success("✔️ Đặt lịch thành công! Chi tiết lịch hẹn đã được đồng bộ vào hệ thống dữ liệu.")
            st.session_state['show_balloons'] = False
            
        st.markdown(st.session_state['booking_success_email'], unsafe_allow_html=True)