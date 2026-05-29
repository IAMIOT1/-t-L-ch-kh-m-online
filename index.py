import csv
import math
import random
import streamlit as st
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
# Hàm vẽ bản đồ giả lập lộ trình đô thị chuyên nghiệp
def draw_simulation_map(home_x, home_y, target_clinic, all_clinics):
    # Tạo khung hình với tỷ lệ chuẩn và độ nét cao (DPI 120)
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=120)
    
    # Tính toán ranh giới bản đồ tự động
    all_x = [float(clinic['x']) for clinic in all_clinics] + [home_x]
    all_y = [float(clinic['y']) for clinic in all_clinics] + [home_y]
    min_x, max_x = min(all_x) - 1.5, max(all_x) + 1.5
    min_y, max_y = min(all_y) - 1.5, max(all_y) + 1.5
    
    # 1. Nền bản đồ xám trắng sáng sang trọng (Chuẩn giao diện Map hiện đại)
    ax.set_facecolor('#f8f9fa')
    
    # 2. Tạo hệ thống các khối phố và đại lộ (Grid đường sá mô phỏng thực tế)
    grid_intervals = [x * 0.5 for x in range(int(min_x)*2, int(max_x)*2 + 2)]
    for vx in grid_intervals:
        ax.axvline(x=vx, color='#cbd5e1', linestyle='-', linewidth=4, alpha=0.25, zorder=1)
    for vy in grid_intervals:
        ax.axhline(y=vy, color='#cbd5e1', linestyle='-', linewidth=4, alpha=0.25, zorder=1)
        
    # Lưới định vị phụ mỏng mảnh phía dưới
    ax.grid(True, which='both', color='#e2e8f0', linestyle='--', linewidth=0.5, alpha=0.5, zorder=0)
    
    # 3. Vẽ các Cơ sở y tế khác xung quanh (Các điểm vệ tinh màu xám/cam nhẹ)
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        if clinic['id'] != target_clinic['id']:
            # Điểm đổ bóng nhẹ phía dưới icon
            ax.scatter(cx, cy - 0.04, color='#cbd5e1', s=110, zorder=2, alpha=0.5)
            # Icon phòng khám vệ tinh
            ax.scatter(cx, cy, color='#94a3b8', s=90, zorder=3, edgecolors='#475569', linewidth=1, alpha=0.85)
            short_name = clinic['name'].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
            ax.text(cx, cy + 0.22, short_name, fontsize=7.5, ha='center', color='#64748b', weight='medium')
            
    # 4. Vẽ thuật toán đường đi mô phỏng GPS thực tế (Di chuyển vuông góc theo các tuyến phố)
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])
    
    # Tạo lộ trình rẽ khúc dạng xương cá/bàn cờ (Manhattan Path) tạo cảm giác đi trên đường thật
    route_x = [home_x, target_x, target_x]
    route_y = [home_y, home_y, target_y]
    
    # Vẽ đường dập bóng mờ phía dưới đường đi chính để tạo hiệu ứng 3D
    ax.plot(route_x, route_y, color='#93c5fd', linestyle='-', linewidth=6, alpha=0.4, zorder=4)
    # Đường line định vị động chuẩn GPS màu xanh Cyan nổi bật
    ax.plot(route_x, route_y, color='#3b82f6', linestyle='-', linewidth=3.5, label='Lộ trình tối ưu (GPS)', zorder=5)
    
    # Thêm các mũi tên chỉ hướng di chuyển nhỏ trên cung đường
    mid_idx_x = (home_x + target_x) / 2
    mid_idx_y = (home_y + target_y) / 2
    ax.annotate('', xy=(mid_idx_x, home_y), xytext=(home_x, home_y), arrowprops=dict(arrowstyle="->", color='#ffffff', lw=1.5, shrinkA=0, shrinkB=0), zorder=6)
    ax.annotate('', xy=(target_x, mid_idx_y), xytext=(target_x, home_y), arrowprops=dict(arrowstyle="->", color='#ffffff', lw=1.5, shrinkA=0, shrinkB=0), zorder=6)

    # 5. Thiết kế ghim vị trí "Nhà của bạn" (Vị trí xuất phát)
    ax.scatter(home_x, home_y, color='#ef4444', s=220, marker='*', zorder=8, edgecolors='#b91c1c', linewidth=1.5, label='Vị trí của bạn')
    ax.text(home_x, home_y - 0.35, 'BẠN Ở ĐÂY', fontsize=8, fontweight='bold', color='#ef4444', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#fef2f2', edgecolor='#fca5a5', alpha=0.9))
    
    # 6. Thiết kế ghim vị trí "Cơ sở khám được chỉ định" (Điểm đích đến)
    ax.scatter(target_x, target_y, color='#10b981', s=250, marker='P', zorder=8, edgecolors='#047857', linewidth=1.5, label='Điểm đến chỉ định')
    target_short = target_clinic["name"].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
    ax.text(target_x, target_y + 0.35, target_short.upper(), fontsize=8.5, fontweight='bold', color='#065f46', ha='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ecfdf5', edgecolor='#a7f3d0', alpha=0.95))
    
    # 7. Khối hiển thị khoảng cách di chuyển thực tế (Floating HUD Card)
    distance = math.sqrt((target_x - home_x)**2 + (target_y - home_y)**2)
    ax.text((home_x + target_x)/2, (home_y + target_y)/2, 
            f'📊 Khoảng cách: {distance:.2f} km ', fontsize=9, fontweight='bold', 
            color='#ffffff', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#1e293b', edgecolor='none', alpha=0.9, boxstyle_factory=None))
    
    # Định dạng tinh chỉnh ẩn các trục tọa độ thô, chỉ giữ lại tiêu đề sạch sẽ
    ax.set_title("🗺️ BẢN ĐỒ ĐIỀU PHỐI TUYẾN ĐƯỜNG DI CHUYỂN REAL-TIME", fontsize=11, fontweight='bold', pad=15, color='#1e293b')
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    
    # Phong cách hóa hộp chú thích (Legend)
    ax.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', shadow=False)
    
    # Ẩn bớt các gai gạch viền ngoài (Ticks) cho giao diện tối giản
    ax.tick_params(colors='#94a3b8', labelsize=8)
    for spine in ax.spines.values():
        spine.set_color('#e2e8f0')
        
    plt.tight_layout()
    return fig

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
    
    col1, col2 = st.columns(2)
    with col1:
        home_x = st.number_input("📍 Tọa độ X của nhà:", value=4.0, step=0.1)
    with col2:
        home_y = st.number_input("📍 Tọa độ Y của nhà:", value=4.0, step=0.1)
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn ", placeholder="đau bụng , ho")

    # Bước 1: Tìm phòng khám gần nhất dựa trên tọa độ nhà
    nearest_clinic, dist = find_nearest_clinic(home_x, home_y, clinics)
    
    # Bước 2: Tìm bác sĩ phù hợp với triệu chứng TẠI phòng khám gần nhất đó
    matched_doctors = find_doctors_by_symptom(symptom_input, nearest_clinic['id'], doctors)

    st.markdown("---")
    st.header("2. Kết quả tìm kiếm & Bản đồ lộ trình")
    
    # Hiển thị phòng khám gần nhất (Yêu cầu 2)
    st.info(f"📍 **Phòng khám gần nhất:** {nearest_clinic['name']} (Khoảng cách tính toán: {dist:.2f} km)")
    
    # Hiển thị bản đồ giả lập trực quan bằng matplotlib
    with st.spinner("Đang dựng bản đồ lộ trình..."):
        map_fig = draw_simulation_map(home_x, home_y, nearest_clinic, clinics)
        st.pyplot(map_fig)

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