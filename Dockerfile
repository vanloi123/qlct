# Sử dụng hình ảnh cơ bản của Python
FROM python:3.8-slim-buster

# Đặt thư mục làm việc
WORKDIR /app

# Sao chép các tệp yêu cầu
COPY requirements.txt requirements.txt

# Cài đặt các gói yêu cầu
RUN pip install -r requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Chạy ứng dụng Flask bằng Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
