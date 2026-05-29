import csv
import math
import random
import streamlit as st
import matplotlib.pyplot as plt

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
def draw_simulation_map(home_x, home_y, target_clinic, all_clinics):
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Tìm giới hạn bản đồ dựa trên tất cả các phòng khám
    all_x = [float(clinic['x']) for clinic in all_clinics] + [home_x]
    all_y = [float(clinic['y']) for clinic in all_clinics] + [home_y]
    min_x, max_x = min(all_x) - 2, max(all_x) + 2
    min_y, max_y = min(all_y) - 2, max(all_y) + 2
    
    # 1. Vẽ nền bản đồ giả lập (màu xanh nhạt như đất)
    ax.set_facecolor('#e8f5e9')
    
    # 2. Vẽ lưới đường giả lập
    for i in range(int(min_x), int(max_x) + 1):
        ax.axvline(x=i, color='#bdbdbd', linestyle='-', linewidth=0.5, alpha=0.5)
    for i in range(int(min_y), int(max_y) + 1):
        ax.axhline(y=i, color='#bdbdbd', linestyle='-', linewidth=0.5, alpha=0.5)
    
    # 3. Vẽ tất cả các phòng khám khác (Màu cam) - Loại bỏ dấu tiếng Việt trên nhãn bản đồ để tuyệt đối không lỗi font
    for clinic in all_clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        if clinic['id'] != target_clinic['id']:
            ax.scatter(cx, cy, color='#ff9800', s=120, zorder=3, edgecolors='black', linewidth=1)
            short_name = clinic['name'].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
            ax.text(cx, cy + 0.4, short_name, fontsize=7, ha='center', color='#e65100', fontweight='bold')
            
    # 4. Vẽ vị trí nhà của bạn (Điểm màu Đỏ với ngôi sao)
    ax.scatter(home_x, home_y, color='#f44336', s=200, marker='*', label='Nha cua ban', zorder=6, edgecolors='darkred', linewidth=2)
    ax.text(home_x, home_y - 0.7, 'Ban o day', fontsize=9, fontweight='bold', color='#b71c1c', ha='center')
    
    # 5. Vẽ phòng khám gần nhất được chọn (Điểm màu Xanh lá với marker P)
    target_x, target_y = float(target_clinic['x']), float(target_clinic['y'])
    ax.scatter(target_x, target_y, color='#4caf50', s=200, marker='P', label='Phong kham gan nhat', zorder=6, edgecolors='darkgreen', linewidth=2)
    target_short = target_clinic["name"].replace('Phòng Khám ', 'PK ').replace('Bệnh Viện ', 'BV ')
    ax.text(target_x, target_y + 0.6, target_short, fontsize=8, fontweight='bold', color='#1b5e20', ha='center')
    
    # 6. Vẽ đường đi giả lập lộ trình tối ưu
    mid_points = []
    num_points = 3
    for i in range(1, num_points):
        ratio = i / num_points
        mid_x = home_x + (target_x - home_x) * ratio
        mid_y = home_y + (target_y - home_y) * ratio
        mid_x += random.uniform(-0.15, 0.15)  # Giảm độ nhiễu một chút để lộ trình nhìn mượt mà hơn
        mid_y += random.uniform(-0.15, 0.15)
        mid_points.append((mid_x, mid_y))
    
    route_x = [home_x] + [p[0] for p in mid_points] + [target_x]
    route_y = [home_y] + [p[1] for p in mid_points] + [target_y]
    ax.plot(route_x, route_y, color='#2196f3', linestyle='-', linewidth=3, label='Tuyen duong toi uu', zorder=4, alpha=0.8)
    
    for mx, my in mid_points:
        ax.scatter(mx, my, color='#2196f3', s=30, zorder=5, marker='o')
    
    # 7. Thêm khoảng cách thông tin
    distance = math.sqrt((target_x - home_x)**2 + (target_y - home_y)**2)
    ax.text((home_x + target_x)/2, (home_y + target_y)/2 + 0.3, 
            f'{distance:.2f} km', fontsize=9, fontweight='bold', 
            color='#1976d2', ha='center', 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Định dạng bản đồ
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
st.subheader("Khoa CNTT - Trường Đại học Đại Nam")
st.markdown("---")

# Tải dữ liệu đầu vào
clinics = read_csv('clinics.csv')
doctors = read_csv('doctors.csv')
appointments = read_csv('appointments.csv')

if clinics and doctors:
    # ------------------ KHU VỰC NHẬP THÔNG TIN BỆNH NHÂN ------------------
    st.header("1. Nhập thông tin bệnh nhân")
    
    patient_email = st.text_input("📩 Email nhận nhắc lịch (Yêu cầu 6):", "nguyenvandan@gmail.com")
    
    col1, col2 = st.columns(2)
    with col1:
        home_x = st.number_input("📍 Tọa độ X của nhà:", value=4.0, step=0.1)
    with col2:
        home_y = st.number_input("📍 Tọa độ Y của nhà:", value=4.0, step=0.1)
        
    symptom_input = st.text_input("🤒 Nhập triệu chứng bệnh của bạn (Ví dụ: ho, sot, dau bung):", "dau bung")

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
        
        # Hiển thị thời gian hiện tại
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
        st.info(f"🕐 Thời gian hiện tại: {current_time}")
        
        # Chọn thời gian mong muốn (Yêu cầu 4)
        desired_date = st.date_input("📅 Chọn ngày khám:").strftime("%Y-%m-%d")
        desired_time = st.selectbox("⏰ Chọn khung giờ mong muốn:", ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"], index=1)

        # Nút bấm tiến hành đặt lịch
        if st.button("🚀 TIẾN HÀNH ĐẶT LỊCH"):
            # Kiểm tra xem khung giờ đã qua chưa
            from datetime import datetime, time
            current_datetime = datetime.now()
            selected_datetime = datetime.strptime(f"{desired_date} {desired_time}", "%Y-%m-%d %H:%M")
            
            if selected_datetime < current_datetime:
                st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} đã qua! Vui lòng chọn thời gian trong tương lai.")
                st.info("👉 Vui lòng chọn lại ngày và khung giờ phù hợp.")
            else:
                # Kiểm tra xem khung giờ đã được đặt chưa
                is_free = check_and_schedule(selected_doctor['id'], desired_date, desired_time, appointments)
                
                if is_free:
                    st.balloons()
                    st.success(f"✔️ Đặt lịch thành công lúc {desired_time} ngày {desired_date}!")
                    
                    # Lưu vào database CSV
                    new_app_id = len(appointments) + 1
                    write_appointment_to_csv('appointments.csv', [new_app_id, patient_email, selected_doctor['id'], desired_date, desired_time])
                    
                    # Hiển thị thông báo nhắc lịch qua Email chi tiết thông tin mở rộng (Yêu cầu 6)
                    st.code(f"""
📧 [HỆ THỐNG EMAIL TỰ ĐỘNG - GỬI TỚI: {patient_email}]
Xin chào! Lịch hẹn khám bệnh của bạn đã được phê duyệt thành công:
------------------------------------------------------------------
🏥 Địa điểm: {nearest_clinic['name']}
👨‍⚕️ Bác sĩ phụ trách: BS. {selected_doctor['name']} ({exp_year} kinh nghiệm)
📞 Hotline liên hệ bác sĩ: {phone_num}
📅 Thời gian: {desired_time} ngày {desired_date}
------------------------------------------------------------------
Vui lòng đến đúng giờ để tiến hành kiểm tra sức khỏe tốt nhất!
""", language="text")
                    
                    # Khởi động lại app để nạp lại bảng dữ liệu lịch hẹn mới lập tức
                    st.rerun()
                
                else:
                    st.error(f"❌ Khung giờ {desired_time} ngày {desired_date} của Bác sĩ {selected_doctor['name']} đã bị trùng lịch!")
                    
                    # Đề xuất khung giờ khác (Yêu cầu 5)
                    suggestions = suggest_alternative_slots(selected_doctor['id'], desired_date, appointments)
                    if suggestions:
                        st.warning(f"💡 Đề xuất các khung giờ thay thế còn trống trong ngày: {', '.join(suggestions)}")
                        st.info(f"👉 Vui lòng chọn lại một trong các khung giờ trống phía trên để đặt lịch.")
                    else:
                        st.error("Rất tiếc, bác sĩ này đã kín lịch hoàn toàn trong ngày hôm nay. Vui lòng chọn ngày khác.")

    # Hiển thị trực quan danh sách lịch hẹn hiện có trong database
    st.markdown("---")
    st.subheader("📋 Danh sách lịch hẹn đã đăng ký trong hệ thống")
    st.dataframe(appointments, use_container_width=True)

else:
    st.error("❌ Không thể tải dữ liệu. Vui lòng kiểm tra các file dữ liệu CSV.")