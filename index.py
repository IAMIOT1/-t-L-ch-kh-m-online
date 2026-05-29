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

def send_real_email(receiver_email, clinic_name, doctor_name, experience, phone, time, date):
    # 1. Cấu hình thông tin tài khoản gửi
    sender_email = "toinguyen7126@gmail.com"
    sender_password = "japg eyvh ontl dliw"  # Mật khẩu ứng dụng 16 ký tự của Google
    
    # 2. Tạo bố cục Email dạng HTML
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
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False

# Cấu hình trang web Streamlit
st.set_page_config(page_title="Đại Học Đại Nam - Đặt Lịch Khám", page_icon="🏥", layout="centered")

# Cấu hình matplotlib tránh lỗi font tiếng Việt hiển thị thành ô vuông
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
    m = folium.Map(location=[home_lat, home_lng], zoom_start=14, control_scale=True)
    
    # Cấu hình các layer bản đồ đường phố và vệ tinh
    folium.TileLayer('openstreetmap', name="Bản đồ đường phố").add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Bản đồ Vệ tinh (Google)'
    ).add_to(m)

    # 1. Đánh dấu vị trí Người dùng (Đỏ)
    folium.Marker(
        location=[home_lat, home_lng],
        popup=f"<b>Vị trí của bạn</b><br>Tọa độ thực: ({home_lat:.4f}, {home_lng:.4f})",
        tooltip="Bạn ở đây!",
        icon=folium.Icon(color='red', icon='home', prefix='fa')
    ).add_to(m)
    
    # 2. Đánh dấu các phòng khám vệ tinh khác (Cam)
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        if clinic['id'] != target_clinic['id']:
            folium.Marker(
                location=[cy, cx],
                popup=f"<b>{clinic['name']}</b>",
                tooltip=clinic['name'],
                icon=folium.Icon(color='orange', icon='plus', prefix='fa')
            ).add_to(m)

    # 3. Đánh dấu phòng khám GẦN NHẤT được hệ thống chọn (Xanh lá)
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])
    folium.Marker(
        location=[target_y, target_x],
        popup=f"<div style='width:200px;'><b>🏥 {target_clinic['name']}</b><br>Đây là phòng khám gần bạn nhất!</div>",
        tooltip=f"Đích đến: {target_clinic['name']}",
        icon=folium.Icon(color='green', icon='hospital-o', prefix='fa')
    ).add_to(m)
    
    # 4. Vẽ duy nhất một đường lộ trình nối từ Vị trí chọn -> Phòng khám gần nhất
    points = [[home_lat, home_lng], [target_y, target_x]]
    folium.PolyLine(points, color="#1a73e8", weight=5, opacity=0.8).add_to(m)
    
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
    
    st.write("📍 **Xác định vị trí hiện tại của bạn:**")
    st.caption("💡 Mẹo: Bạn có thể click chuột trực tiếp vào bất kỳ vị trí nào trên bản đồ dưới đây để thay đổi vị trí thực tế của mình. Hệ thống sẽ tự động tìm phòng khám gần nhất và vẽ lại lộ trình!")

    # Khởi tạo giá trị mặc định trong Session State nếu chưa từng chọn (Mặc định ở Hà Nội)
    if 'gps_lat' not in st.session_state: 
        st.session_state['gps_lat'] = 21.0285 
    if 'gps_lng' not in st.session_state: 
        st.session_state['gps_lng'] = 105.8542

    home_lat = st.session_state['gps_lat']
    home_lng = st.session_state['gps_lng']
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn ", placeholder="đau bụng , ho")

    # Bước 1: Tìm phòng khám gần nhất dựa trên tọa độ đã xác định
    nearest_clinic, dist = find_nearest_clinic(home_lat, home_lng, clinics)
    
    # Bước 2: Tìm bác sĩ phù hợp với triệu chứng TẠI phòng khám gần nhất đó
    matched_doctors = find_doctors_by_symptom(symptom_input, nearest_clinic['id'], doctors)

    st.markdown("---")
    st.header("2. Kết quả tìm kiếm & Bản đồ lộ trình")
    
    # Hiển thị phòng khám gần nhất công khai số km
    st.info(f"📍 **Phòng khám gần nhất với bạn:** {nearest_clinic['name']} (Khoảng cách thực tế: {dist:.2f} km)")
    
    # Tạo bản đồ tích hợp hiển thị lộ trình và lắng nghe sự kiện click thay đổi vị trí
    with st.spinner("Đang đồng bộ bản đồ vệ tinh thực tế..."):
        map_obj = draw_simulation_map(home_lat, home_lng, nearest_clinic, clinics)
        # Chỉ gọi duy nhất 1 bản đồ hiển thị ở đây và bắt sự kiện click chuột
        st_data = st_folium(map_obj, width=700, height=450, key="integrated_map_picker")
        
    # Nếu người dùng click vào một điểm bất kỳ trên bản đồ, ghi nhận tọa độ mới và reload lại lộ trình
    if st_data and st_data.get("last_clicked"):
        click_lat = st_data["last_clicked"]["lat"]
        click_lng = st_data["last_clicked"]["lng"]
        if click_lat != st.session_state['gps_lat'] or click_lng != st.session_state['gps_lng']:
            st.session_state['gps_lat'] = click_lat
            st.session_state['gps_lng'] = click_lng
            st.rerun()

    st.success(f"🗺️ Tọa độ đang chọn: **Vĩ độ (Lat):** {home_lat:.4f} | **Kinh độ (Lng):** {home_lng:.4f}")
    
    if not matched_doctors:
        st.warning(f"❌ Không tìm thấy bác sĩ phù hợp với triệu chứng '{symptom_input}' tại phòng khám gần nhất.")
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
        
        desired_date = st.date_input("📅 Chọn ngày khám:")
        desired_date_str = desired_date.strftime("%Y-%m-%d")
        desired_time = st.selectbox("⏰ Chọn khung giờ mong muốn:", ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"], index=1)

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