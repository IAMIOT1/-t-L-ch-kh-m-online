# Hệ Thống Đặt Lịch Khám Online

## Cách Deploy Lên Streamlit Cloud (Miễn Phí)

### Bước 1: Push code lên GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Bước 2: Deploy lên Streamlit Cloud
1. Vào https://streamlit.io/cloud
2. Đăng nhập bằng GitHub
3. Click "New app"
4. Chọn repository của bạn
5. File path: `index.py`
6. Click "Deploy"

### Bước 3: Chờ deploy hoàn tất
- Streamlit sẽ tự động cài đặt dependencies từ `requirements.txt`
- Sau vài phút, bạn sẽ có URL như: `https://your-app-name.streamlit.app`

## Chạy Local
```bash
pip install -r requirements.txt
streamlit run index.py
```

## Yêu cầu Đề Bài
✅ 1. Dữ liệu CSV (doctors.csv, clinics.csv, appointments.csv)
✅ 2. Tìm phòng khám gần nhất bằng khoảng cách giả lập
✅ 3. Chọn chuyên khoa + bác sĩ theo triệu chứng
✅ 4. Đặt lịch theo thời gian mong muốn
✅ 5. Phát hiện trùng lịch và đề xuất khung giờ thay thế
✅ 6. Gửi nhắc lịch qua email (giả lập)
