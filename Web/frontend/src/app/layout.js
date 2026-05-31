import "./globals.css";

export const metadata = {
  title: "Hate Speech Detection — Dashboard",
  description: "Hệ thống quản lý dữ liệu và kết quả huấn luyện mô hình Hate Speech Detection",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
