# Digital Evidence Management System

A secure web-based **Digital Evidence Management System (DEMS)** built with **Flask** and **MongoDB** for storing, managing, and verifying digital forensic evidence while maintaining the **Chain of Custody**.

---

## 📖 Overview

The Digital Evidence Management System helps investigators securely upload, organize, verify, and manage digital evidence collected during investigations. The system maintains evidence integrity using cryptographic hashing and records every action performed on evidence for accountability.

---

## 🚀 Features

- 🔐 Secure User Authentication
- 👥 Role-Based Access Control
- 📂 Case Management
- 📁 Digital Evidence Upload
- 🔍 Evidence Search & Filtering
- 🔒 SHA-256 Hash Verification
- 🔗 Chain of Custody Tracking
- 📊 Dashboard with Statistics
- 📝 Audit Logs
- 📄 Report Generation
- 🌐 REST API Support

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- Flask Login
- Flask JWT Extended
- Flask WTF
- Flask Limiter

### Database
- MongoDB

### Frontend
- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

### Other Libraries
- PyMongo
- bcrypt
- python-dotenv
- ReportLab
- OpenPyXL
- Gunicorn

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Rupesh-001/Digital-Evidence-Management-System.git
```

### 2. Go to the Project Folder

```bash
cd Digital-Evidence-Management-System
```

### 3. Create Virtual Environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file using `.env.example`.

Example:

```env
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
MONGO_URI=your_mongodb_connection_string
```

### 6. Run the Application

```bash
python app.py
```

The application will be available at

```
http://127.0.0.1:5000
```

---

## 🔐 Security Features

- Password Hashing using bcrypt
- JWT Authentication
- CSRF Protection
- Request Rate Limiting
- Secure Session Management
- Evidence Integrity Verification
- Audit Logging

---

## 📁 Main Modules

### Authentication

- Login
- Register
- Logout

### Dashboard

- Overview
- Statistics

### Case Management

- Create Case
- Edit Case
- View Cases

### Evidence Management

- Upload Evidence
- View Evidence
- Verify Evidence Hash
- Search Evidence

### Chain of Custody

- Track Evidence Transfers
- View Custody Logs

### Reports

- Case Reports
- Evidence Reports
- Audit Reports
- Custody Reports

### Admin Panel

- User Management
- Audit Logs

---

## 🔍 Evidence Integrity

Every uploaded file is protected using **SHA-256 hashing**.

The system allows investigators to verify whether any evidence has been modified after upload.

---

## 📈 Future Enhancements

- Two-Factor Authentication
- Digital Signature Support
- Email Notifications
- AI-based Evidence Classification
- Cloud Storage Integration
- OCR for Documents
- Blockchain-based Chain of Custody

---

## 👨‍💻 Team Members

- Rupesh Varma
- Manish Kushwaha
- Team Member 3

---

## 📚 Academic Project

**Course:** MSc Information Technology (Cyber Security & Digital Forensics)

**University:** Parul University

---

## 📜 License

This project is developed for educational and academic purposes.

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub.
