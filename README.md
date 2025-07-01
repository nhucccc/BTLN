🌐 Giả lập Upload/Download Dữ liệu IoT lên Cloud với Log Thời Gian
🎯 Mục tiêu
Phần mềm mô phỏng quá trình truyền dữ liệu cảm biến (sensor_data.txt) từ thiết bị IoT lên nền tảng Cloud AWS S3 giả lập thông qua kênh socket TCP, tích hợp các lớp bảo mật hiện đại gồm:




GIAO DIỆN CỦA ỨNG DỤNG VÀ DỮ LIỆU KHI ĐƯỢC GIẢI MÃ:

![Giao diện ứng dụng](https://github.com/nhucccc/BTLN/blob/main/up1.png)





![Dữ liệu ảnh khi được giải mã](https://github.com/nhucccc/BTLN/blob/main/up2.png)






Mã hóa AES-GCM

Ký số RSA/SHA-512

Kiểm tra toàn vẹn SHA-512

Giao diện ứng dụng cung cấp đầy đủ các chức năng upload, download, kiểm tra chữ ký, xóa file trên cloud và lưu log chi tiết thời gian giao dịch.

🖥️ Chức năng chính
📂 1. Upload dữ liệu lên Cloud hoặc Drive
Upload to Drive: Lưu file mã hóa cục bộ trên ổ đĩa máy tính, phục vụ kiểm thử offline.

Upload to Server: Gửi file mã hóa qua socket TCP lên dịch vụ cloud giả lập.

Trong quá trình upload:

Ký metadata bằng RSA/SHA-512 (thông tin file, timestamp, loại cảm biến).

Mã hóa SessionKey RSA 1024-bit.

Mã hóa dữ liệu bằng AES-GCM (tạo nonce, ciphertext và tag).

Tính hash SHA-512 để đảm bảo toàn vẹn.

Tạo gói tin upload (nonce, ciphertext, tag, hash, chữ ký).

Cloud kiểm tra hợp lệ:

Nếu hợp lệ: giải mã, lưu file và ghi log thời gian.

Nếu lỗi: trả về NACK (ví dụ: Signature mismatch như ảnh trên).

📥 2. Download dữ liệu từ Cloud hoặc Drive
Download from Drive: Tải file mã hóa lưu cục bộ, giải mã và hiển thị nội dung.

Download from Server: Yêu cầu cloud gửi gói tin mã hóa và chữ ký metadata:

Ứng dụng sẽ:

Kiểm tra chữ ký RSA/SHA-512.

Kiểm tra hash SHA-512.

Kiểm tra tag AES-GCM.

Nếu hợp lệ: giải mã và lưu file sensor_data.txt.

Nếu lỗi: thông báo lỗi toàn vẹn.

📝 3. Quản lý nhật ký giao dịch
Logs: Hiển thị thông tin quá trình upload/download, ví dụ:

"Signature mismatch!" – Chữ ký không trùng khớp, từ chối nhận dữ liệu.

"Upload successful." – Upload thành công, đã lưu log thời gian.

"Download ACK received." – Tải thành công.

Lưu log thời gian giao dịch phục vụ giám sát hiệu suất.

🗑️ 4. Xóa dữ liệu trên Cloud
Delete file on Drive: Xóa tệp tin được lưu trữ trên ổ đĩa cục bộ.

Có thể bổ sung nút xóa file trên server (cloud) nếu cần.

🔑 5. Bảo mật lớp cao
Phần mềm triển khai đầy đủ:

Handshake:

Thiết bị gửi Hello!.

Cloud trả lời Ready!.

Xác thực:

Ký metadata RSA/SHA-512.

Mã hóa SessionKey RSA (OAEP + SHA-512).

Mã hóa & toàn vẹn:

AES-GCM: mã hóa dữ liệu và sinh tag.

SHA-512: kiểm tra tính toàn vẹn gói tin.

Chữ ký số: xác thực người gửi/nhận.

Kênh truyền an toàn:

Giao thức socket TCP giả lập môi trường cloud.

📊 Ý nghĩa ứng dụng
Hệ thống này giúp kỹ sư IoT:
Kiểm tra luồng bảo mật end-to-end trước khi triển khai thực tế.

Giám sát hiệu suất truyền tải qua log thời gian.

Mô phỏng mô hình upload/download file nhạy cảm trong các dự án IoT sử dụng cloud.


