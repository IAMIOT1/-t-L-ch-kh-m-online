import csv
from datetime import datetime, timedelta
import math

# ==============================================================================
# YÊU CẦU 1: Đọc dữ liệu từ các file CSV
# ==============================================================================
def read_csv(file_name):
    data = []
    try:
        with open(file_name, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {file_name}. Hãy tạo file trước.")
    return data

def write_appointment_to_csv(file_name, appointment):
    with open(file_name, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(appointment)

# ==============================================================================
# YÊU CẦU 2: Tìm phòng khám gần nhà nhất (Sử dụng công thức khoảng cách Euclide)
# ==============================================================================
def find_nearest_clinic(home_x, home_y, clinics):
    nearest_clinic = None
    min_distance = float('inf')
    
    for clinic in clinics:
        cx, cy = float(clinic['x']), float(clinic['y'])
        # Công thức tính khoảng cách d = sqrt((x2-x1)^2 + (y2-y1)^2)
        distance = math.sqrt((cx - home_x)**2 + (cy - home_y)**2)
        
        if distance < min_distance:
            min_distance = distance
            nearest_clinic = clinic
            
    return nearest_clinic, min_distance

# ==============================================================================
# YÊU CẦU 3: Tìm bác sĩ đáp ứng triệu chứng bệnh tại phòng khám đã chọn
# ==============================================================================
def find_doctors_by_symptom(symptom, clinic_id, doctors):
    matching_doctors = []
    for doc in doctors:
        # Kiểm tra xem bác sĩ có ở phòng khám đó không và triệu chứng có khớp không
        if doc['clinic_id'] == clinic_id and symptom.lower() in doc['symptoms'].lower():
            matching_doctors.append(doc)
    return matching_doctors

# ==============================================================================
# YÊU CẦU 5 & 4: Tự động phát hiện trùng lịch và đề xuất khung giờ thay thế
# ==============================================================================
def check_and_schedule(doctor_id, date_str, time_str, appointments):
    # Kiểm tra xem bác sĩ đã có lịch vào ngày và giờ đó chưa
    for app in appointments:
        if app['doctor_id'] == str(doctor_id) and app['date'] == date_str and app['time_slot'] == time_str:
            return False # Bị trùng lịch
    return True # Lịch trống

def suggest_alternative_slots(doctor_id, date_str, appointments):
    # Khung giờ làm việc mặc định trong ngày
    working_slots = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    available_slots = []
    
    for slot in working_slots:
        if check_and_schedule(doctor_id, date_str, slot, appointments):
            available_slots.append(slot)
            
    return available_slots

# ==============================================================================
# YÊU CẦU 6: Nhắc lịch/Nhắc việc (Gửi đến email người bệnh)
# ==============================================================================
def send_email_reminder(patient_email, clinic_name, doctor_name, date_str, time_str):
    print("\n" + "="*50)
    print(f"📧 [HỆ THỐNG EMAIL] Đã gửi thông báo nhắc lịch tới: {patient_email}")
    print(f"Nội dung: Xin chào, bạn có lịch hẹn khám sức khỏe online:")
    print(f"   - Địa điểm: {clinic_name}")
    print(f"   - Bác sĩ chuyên khoa: {doctor_name}")
    print(f"   - Thời gian: {time_str} ngày {date_str}")
    print("Vui lòng đến đúng giờ. Chúc bạn nhiều sức khỏe!")
    print("="*50)

# ==============================================================================
# CHƯƠNG TRÌNH CHÍNH (MAIN PROCESS)
# ==============================================================================
def main():
    print("--- HỆ THỐNG ĐẶT LỊCH HẸN KHÁM SỨC KHỎE ONLINE ---")
    
    # Đọc dữ liệu từ file csv
    clinics = read_csv('clinics.csv')
    doctors = read_csv('doctors.csv')
    appointments = read_csv('appointments.csv')
    
    if not clinics or not doctors:
        print("Dữ liệu trống hoặc thiếu file cấu hình csv!")
        return

    # Giả lập thông tin của người bệnh nhập vào
    patient_email = "nguyenvandan@gmail.com"
    home_x, home_y = 4.0, 4.0  # Tọa độ vị trí nhà người bệnh
    symptom_input = "ho"       # Triệu chứng của bệnh nhân
    
    print(f"\n[Bước 1] Vị trí nhà bệnh nhân: ({home_x}, {home_y})")
    print(f"[Bước 2] Triệu chứng bệnh nhập vào: '{symptom_input}'")

    # 2. Tìm phòng khám gần nhất
    nearest_clinic, dist = find_nearest_clinic(home_x, home_y, clinics)
    print(f"-> Phòng khám gần nhất là: {nearest_clinic['name']} (Khoảng cách: {dist:.2f})")

    # 3. Tìm bác sĩ phù hợp tại phòng khám đó dựa trên triệu chứng
    matched_doctors = find_doctors_by_symptom(symptom_input, nearest_clinic['id'], doctors)
    
    if not matched_doctors:
        print(f"Không tìm thấy bác sĩ nào chữa triệu chứng '{symptom_input}' tại phòng khám này.")
        return
    
    # Chọn bác sĩ đầu tiên tìm được đáp ứng yêu cầu
    selected_doctor = matched_doctors[0]
    print(f"-> Bác sĩ chuyên khoa phù hợp tìm thấy: {selected_doctor['name']} (Chuyên khoa: {selected_doctor['specialty']})")

    # 4. Đặt lịch khám theo thời gian mong muốn
    desired_date = "2026-06-01"
    desired_time = "09:00"  # Thử nghiệm giờ trùng với lịch có sẵn trong file csv mẫu
    print(f"\n[Bước 3] Thời gian bạn muốn đặt: {desired_time} ngày {desired_date}")

    # 5. Tự động kiểm tra trùng lịch
    is_free = check_and_schedule(selected_doctor['id'], desired_date, desired_time, appointments)
    
    if is_free:
        print("✔️ Lịch trống! Tiến hành đăng ký lịch khám thành công.")
        final_time = desired_time
    else:
        print("❌ Cảnh báo: Khung giờ này bác sĩ đã có lịch hẹn trước (Trùng lịch)!")
        # Đề xuất khung giờ khác
        suggestions = suggest_alternative_slots(selected_doctor['id'], desired_date, appointments)
        if suggestions:
            print(f"👉 Gợi ý các khung giờ thay thế còn trống: {suggestions}")
            final_time = suggestions[0] # Tự động chọn khung giờ trống đầu tiên thay thế
            print(f"-> Hệ thống tự động chuyển lịch hẹn sang khung giờ trống: {final_time}")
        else:
            print("Rất tiếc, bác sĩ đã hết lịch trống trong ngày này.")
            return

    # Lưu lịch hẹn mới vào file csv (Giả lập tăng ID tiếp theo)
    new_app_id = len(appointments) + 1
    new_appointment = [new_app_id, patient_email, selected_doctor['id'], desired_date, final_time]
    write_appointment_to_csv('appointments.csv', new_appointment)

    # 6. Nhắc lịch gửi tới email bệnh nhân
    send_email_reminder(patient_email, nearest_clinic['name'], selected_doctor['name'], desired_date, final_time)

if __name__ == "__main__":
    main()