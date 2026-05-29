import csv
import math
import random
import streamlit as st
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# HÀM GỬI EMAIL THẬT QUA SMTP GMAIL DIRECTLY
# ==============================================================================
def send_real_email(receiver_email, clinic_name, doctor_name, experience, phone, time, date):
    # 🔴 BẠN CẦN THAY THẾ 2 THÔNG TIN DƯỚI ĐÂY ĐỂ KÍCH HOẠT GỬI MAIL THẬT:
    sender_email = "toinguyen7126@gmail.com"
    sender_password = "japg eyvh ontl dliw"  # Mật khẩu ứng dụng 16 ký tự của Google
    
    # Tạo bố cục nội dung Email dạng HTML
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🏥 [ĐẠI HỌC ĐẠI NAM] - XÁC NHẬN LỊCH HẸN KHÁM THÀNH CÔNG"
    message["From"] = sender_email
    message["To"] = receiver_email

    html_content = f"""
    <html>
      <body>
        <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; border-radius: 5px; font-family: sans-serif;">
            <h3 style="color: #007bff; margin-top: 0;">📧 XÁC NHẬN ĐẶT LỊCH KHÁM THÀNH CÔNG</h3>
            <p>Xin chào <b>{receiver_email}</b>,</p>
            <p>Lịch hẹn khám bệnh của bạn đã được phê duyệt thành công trên hệ thống Đại học Đại Nam. Chi tiết như sau:</p>
            <hr style="border: none; border-top: 1px solid #dee2e6;">
            <p>🏥 <b>Địa điểm:</b> {clinic_name}</p>
            <p>👨‍⚕️ <b>Bác sĩ phụ trách:</b> BS. {doctor_name} ({experience})</p>
            <p>📞 <b>Hotline bác sĩ:</b> {phone}</p>
            <p>📅 <b>Thời gian:</b> <span style="color: #dc3545; font-weight: bold;">{time} ngày {date}</span></p>
            <hr style="border: none; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d; font-style: italic; font-size: 0.95em;">Vui lòng đến đúng giờ để tiến hành kiểm tra sức khỏe tốt nhất!</p>
        </div>
      </body>
    </html>
    """
    message.attach(MIMEText(html_content, "html", "utf-8"))

    # Kết nối trực tiếp đến Server SMTP của Gmail để gửi đi
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Bảo mật kết nối mã hóa TLS
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        # Nếu cấu hình sai tài khoản, lỗi sẽ hiển thị ở terminal để bạn kiểm tra
        print(f"Lỗi gửi email thực tế: {e}")
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
def find_nearest_clinic(home_x, home_y, clinics):
    nearest_clinic = None
    min_distance = float('inf')
    for clinic in clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        distance = math.sqrt((cx - home_x)**2 + (cy - home_y)**2)
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
            return False  # Trùng lịch
    return True  # Trống lịch

def suggest_alternative_slots(doctor_id, date_str, appointments):
    working_slots = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    return [slot for slot in working_slots if check_and_schedule(doctor_id, date_str, slot, appointments)]

def draw_simulation_map(home_x, home_y, target_clinic, all_clinics):
    fig, ax = plt.subplots(figsize=(10, 7))
    all_x = [float(clinic['x']) for clinic in all_clinics] + [home_x]
    all_y = [float(clinic['y']) for clinic in all_clinics] + [home_y]
    min_x, max_x = min(all_x) - 2, max(all_x) + 2
    min_y, max_y = min(all_y) - 2, max(all_y) + 2
    
    ax.set_facecolor('#e8f5e9')
    
    for i in range(int(min_x), int(max_x) + 1):
        ax.axvline(x=i, color='#bdbdbd', linestyle='-', linewidth=0.5, alpha=0.5)
    for i in range(int(min_y), int(max_y) + 1):
        ax.axhline(y=i, color='#bdbdbd', linestyle='-', linewidth=0.5, alpha=0.5)
    
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        if clinic['id'] != target_clinic['id']:
            ax.scatter(cx, cy, color='#ff9800', s=120, zorder=3, edgecolors='black', linewidth=1)
            short_name = clinic['name'].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
            ax.text(cx, cy + 0.4, short_name, fontsize=7, ha='center', color='#e65100', fontweight='bold')
            
    ax.scatter(home_x, home_y, color='#f44336', s=200, marker='*', label='Nha cua ban', zorder=6, edgecolors='darkred', linewidth=2)
    ax.text(home_x, home_y - 0.7, 'Ban o day', fontsize=9, fontweight='bold', color='#b71c1c', ha='center')
    
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])
    ax.scatter(target_x, target_y, color='#4caf50', s=200, marker='P', label='Phong kham gan nhat', zorder=6, edgecolors='darkgreen', linewidth=2)
    target_short = target_clinic["name"].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
    ax.text(target_x, target_y + 0.6, target_short, fontsize=8, fontweight='bold', color='#1b5e20', ha='center')
    
    mid_points = []
    num_points = 3
    for i in range(1, num_points):
        ratio = i / num_points
        mid_x = home_x + (target_x - home_x) * ratio
        mid_y = home_y + (target_y - home_y) * ratio
        mid_x += random.uniform(-0.15, 0.15)
        mid_y += random.uniform(-0.15, 0.15)
        mid_points.append((mid_x, mid_y))
    
    route_x = [home_x] + [p[0] for p in mid_points] + [target_x]
    route_y = [home_y] + [p[1] for p in mid_points] + [target_y]
    ax.plot(route_x, route_y, color='#2196f3', linestyle='-', linewidth=3, label='Tuyen duong toi uu', zorder=4, alpha=0.8)
    
    for mx, my in mid_points:
        ax.scatter(mx, my, color='#2196f3', s=30, zorder=5, marker='o')
    
    distance = math.sqrt((target_x - home_x)**2 + (target_y - home_y)**2)
    ax.text((home_x + target_x)/2, (home_y + target_y)/2 + 0.3, 
            f'{distance:.2f} km', fontsize=9, fontweight='bold', 
            color='#1976d2', ha='center', 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.set_title("BAN DO GIA LAP LO TRINH DI CHUYEN", fontsize=12, fontweight='bold', pad=15, color='#1b5e20')
    ax.set_xlabel("Toa do X (km)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Toa do Y (km)", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.3, color='#666')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9, facecolor='white', edgecolor='#333')
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    
    plt.tight_layout()
    return fig

# ==============================================================================
# GIAO DIỆN ỨNG DỤNG WEB (STREAMLIT UI)
# ==============================================================================
st.title("🏥 HỆ THỐNG ĐẶT LỊCH KHÁM ONLINE")
st.subheader("Khoa Công nghệ thông tin - Đại học Đại Nam")
st.markdown("---")

clinics = read_csv('clinics.csv')
doctors = read_csv('doctors.csv')
appointments = read_csv('appointments.csv')

if clinics and doctors:
    st.header("1. Nhập thông tin bệnh nhân")
    patient_email = st.text_input("📩 Email nhận nhắc lịch (Yêu cầu 6):", "nguyenvandan@gmail.com")
    
    col1, col2 = st.columns(2)
    with col1:
        home_x = st.number_input("📍 Tọa độ X của nhà:", value=4.0, step=0.1)
    with col2:
        home_y = st.number_input("📍 Tọa độ Y của nhà:", value=4.0, step=0.1)
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn (Ví dụ: ho, sot, dau bung):", "dau bung")

    nearest_clinic, dist = find_nearest_clinic(home_x, home_y, clinics)
    matched_doctors = find_doctors_by_symptom(symptom_input, nearest_clinic['id'], doctors)

    st.markdown("---")
    st.header("2. Kết quả tìm kiếm & Bản đồ lộ trình")
    st.info(f"📍 **Phòng khám gần nhất:** {nearest_clinic['name']} (Khoảng cách tính toán: {dist:.2f} km)")
    
    with st.spinner("Đang dựng bản đồ lộ trình..."):
        map_fig = draw_simulation_map(home_x, home_y, nearest_clinic, clinics)
        st.pyplot(map_fig)

    if not matched_doctors:
        st.warning(f"❌ Không tìm thấy bác sĩ phù hợp với triệu chứng '{symptom_input}' tại phòng khám gần nhất.")
    else:
        selected_doctor = matched_doctors[0]
        phone_num = selected_doctor.get('phone', 'Chưa cập nhật')
        exp_year = selected_doctor.get('experience', 'Chưa rõ')
        
        st.success(f"👨‍⚕️ **Bác sĩ được chỉ định:** {selected_doctor['name']} | **Chuyên khoa:** {selected_doctor['specialty']} | **Kinh nghiệm:** {exp_year}")

        st.markdown("---")
        st.header("3. Chọn thời gian & Đặt lịch")
        
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
        
        desired_date = st.date_input("📅 Chọn ngày khám:").strftime("%Y-%m-%d")
        desired_time = st.selectbox("⏰ Chọn khung giờ mong muốn:", ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"], index=1)

        # Kiểm tra frontend bằng JS trước khi Submit
        validation_js = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => {{
                if (button.textContent.includes('TIẾN HÀNH ĐẶT LỊCH')) {{
                    button.addEventListener('click', function(e) {{
                        const selectedDate = '{desired_date}';
                        const selectedTime = '{desired_time}';
                        const selectedDateTime = new Date(selectedDate + 'T' + selectedTime + ':00');
                        const now = new Date();
                        if (selectedDateTime < now) {{
                            e.preventDefault();
                            alert('❌ Khung giờ ' + selectedTime + ' ngày ' + selectedDate + ' đã qua!\\nVui lòng chọn thời gian trong tương lai.');
                        }}
                    }});
                }
            }});
        }});
        </script>
        """
        components.html(validation_js, height=0)

        # NÚT BẤM TIẾN HÀNH ĐẶT LỊCH KHÁM
        if st.button("🏥 TIẾN HÀNH ĐẶT LỊCH"):
            from datetime import datetime
            import pytz
            
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            current_datetime = datetime.now(vietnam_tz).replace(tzinfo=None)
            selected_datetime = datetime.strptime(f"{desired_date} {desired_time}", "%Y-%m-%d %H:%M")
            
            if selected_datetime < current_datetime:
                st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} đã qua so với thời gian thực! Vui lòng chọn thời gian trong tương lai.")
            else:
                is_free = check_and_schedule(selected_doctor['id'], desired_date, desired_time, appointments)
                
                if is_free:
                    # 1. Lưu thông tin lịch hẹn vào database file CSV
                    new_app_id = len(appointments) + 1
                    write_appointment_to_csv('appointments.csv', [new_app_id, patient_email, selected_doctor['id'], desired_date, desired_time])
                    
                    # 2. Thực hiện kích hoạt gửi EMAIL THẬT chạy ngầm đến địa chỉ người dùng
                    send_real_email(
                        patient_email, 
                        nearest_clinic['name'], 
                        selected_doctor['name'], 
                        exp_year, 
                        phone_num, 
                        desired_time, 
                        desired_date
                    )
                    
                    # 3. Đồng bộ giao diện lưu vào session_state để hiển thị bản copy trên Web
                    st.session_state['booking_success_email'] = f"""
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 5px solid #007bff; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); font-family: sans-serif;">
                        <h5 style="color: #007bff; margin-top: 0;">📧 HỆ THỐNG EMAIL TỰ ĐỘNG — GỬI TỚI: {patient_email}</h5>
                        <p>Xin chào! Lịch hẹn khám bệnh của bạn đã được phê duyệt thành công trên hệ thống và một bản sao thư điện tử gốc đã được gửi trực tiếp tới hòm thư của bạn:</p>
                        <hr style="border: none; border-top: 1px solid #dee2e6;">
                        <p>🏥 <b>Địa điểm:</b> {nearest_clinic['name']}</p>
                        <p>👨‍⚕️ <b>Bác sĩ phụ trách:</b> BS. {selected_doctor['name']} ({exp_year})</p>
                        <p>📞 <b>Hotline liên hệ bác sĩ:</b> {phone_num}</p>
                        <p>📅 <b>Thời gian:</b> <span style="color: #dc3545; font-weight: bold;">{desired_time} ngày {desired_date}</span></p>
                        <hr style="border: none; border-top: 1px solid #dee2e6;">
                        <p style="font-size: 0.9em; color: #6c757d; font-style: italic;">👉 Vui lòng mở hòm thư điện tử cá nhân của bạn để kiểm tra hộp thư đến!</p>
                    </div>
                    <br>
                    """
                    st.session_state['show_balloons'] = True
                    st.rerun()
                else:
                    st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} của Bác sĩ {selected_doctor['name']} đã bị trùng lịch!")
                    suggestions = suggest_alternative_slots(selected_doctor['id'], desired_date, appointments)
                    if suggestions:
                        st.warning(f"💡 Đề xuất các khung giờ thay thế còn trống trong ngày: {', '.join(suggestions)}")
                    else:
                        st.error("Rất tiếc, bác sĩ này đã kín lịch hoàn toàn trong ngày hôm nay. Vui lòng chọn ngày khác.")

    # ==============================================================================
    # KHU VỰC HIỂN THỊ EMAIL VÀ BẢNG DANH SÁCH SAU KHI RERUN
    # ==============================================================================
    st.markdown("---")
    
    # Hiển thị card thông báo và hiệu ứng bong bóng khi đặt xong
    if 'booking_success_email' in st.session_state:
        if st.session_state.get('show_balloons', False):
            st.balloons()
            st.success("✔️ Đặt lịch thành công! Chi tiết lịch hẹn đã được đồng bộ vào hệ thống dữ liệu.")
            st.session_state['show_balloons'] = False
        st.markdown(st.session_state['booking_success_email'], unsafe_allow_html=True)
        
    # HIỂN THỊ BẢNG DANH SÁCH ĐỌC TỪ FILE CSV ĐỂ KIỂM CHỨNG
    st.subheader("📋 Danh sách lịch hẹn đã đăng ký trên hệ thống")
    latest_appointments = read_csv('appointments.csv')
    if latest_appointments:
        st.dataframe(latest_appointments, use_container_width=True)
    else:
        st.info("Hiện chưa có lịch hẹn nào được đăng ký.")
else:
    st.error("❌ Không thể tải dữ liệu đầu vào. Vui lòng kiểm tra lại các file CSV!")