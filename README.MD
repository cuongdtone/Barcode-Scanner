# Barcode Scanner

## Cài đặt

### 1. Chuẩn bị
Cài python (add path), SD cardformat và win32disk image trong thư mục docs vào PC  
Tải image: [Google driver](https://drive.google.com/file/d/1FFTjlQ0FPzoflaPIuj35g858ELzJvnx_/view?usp=sharing)

### 2. Flash
Quick flash bằng SD card formator
Dùng win32disk image để flash image vào thẻ nhớ

### 2. Device setup
Sau khi flash, cắm cáp mạng LAN cho orange pi và cắm điện khởi động.  
Kết nối PC với mạng LAN đã dùng cho orange pi và chạy cài đặt thiết bị ban đầu bằng click vào: ```device-setup.bat```

### Đợi khi có thông báo cài hoàn tất Orangepi: Installed - tắt terminal và khởi động lại orange pi (có thể gỡ cáp mạng)

## Cách dùng
### 1. Đưa file cfg.json vào USB driver với việc hiệu chỉnh các cài đặt wifi và mạng trong đó
### 2. Khởi động PC app:
```pc-app.bat```
### 3. Khởi động lại Orange pi