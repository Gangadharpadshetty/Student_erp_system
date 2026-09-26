# Product Requirements Document (PRD) - Student ERP System

## 1. Executive Summary
The Student ERP System is a centralized management platform designed to streamline school administration. It eliminates manual paperwork by digitizing student records, teacher assignments, attendance, and academic reporting. The system provides a clear hierarchy where the Admin manages the ecosystem, Teachers input academic data, and Students track their own progress.

## 2. Target Users (Personas)
### 2.1 Administrator (Super User)
*   **Goal:** Maintain the integrity of the school's data and manage staff and students.
*   **Key Actions:** Create accounts, assign class teachers, manage financial summaries, and resolve student tickets.

### 2.2 Teacher
*   **Goal:** Efficiently track student attendance and academic performance.
*   **Key Actions:** Mark daily attendance, enter subject marks for students, and view their assigned class.

### 2.3 Student
*   **Goal:** Access academic results and attendance records transparently.
*   **Key Actions:** View report cards, check attendance percentages, and raise tickets for data corrections.

## 3. Functional Requirements

### 3.1 User & Account Management
*   **Admin Creation:** The first Admin account is created via the database.
*   **User Provisioning:** Admin can create Teacher and Student accounts and manually distribute credentials (Email/Password).
*   **Role-Based Access Control (RBAC):** Different dashboards and permissions for Admin, Teacher, and Student.

### 3.2 Academic & Class Management
*   **Class Structure:** Support for grades 1 through 10.
*   **Teacher Assignment:** Admin assigns a specific Teacher as the "Class Teacher" for each grade.

### 3.3 Attendance Tracking
*   **Teacher Input:** Teachers can mark students as 'Present' or 'Absent' daily.
*   **Student View:** Students can view their attendance history.

### 3.4 Academic Reporting (The Marks Module)
*   **Core Subjects:** Support for English, Kannada, Hindi, Maths, Science, and Social Science.
*   **Result Calculation:** Automatic calculation of overall percentage and Pass/Fail status.
*   **Performance Summary:** The system tracks "Distinctions" and "Pass Rates" for administrative review.

### 3.5 Financial & High-Level Academics
*   **Administrative Dashboard:** A summary view showing total students, total fees collected, and total teacher salaries paid per academic year/class.

### 3.6 Support Ticket System
*   **Student Grievance:** Students can create a "Ticket" if they find an error in their marks or attendance.
*   **Admin Resolution:** Admin can review and mark tickets as 'Resolved'.

## 4. Feature Importance Matrix

| Feature | Importance | Impact | Why it matters |
| :--- | :--- | :--- | :--- |
| Admin User Mgmt | Critical | High | The system cannot function without managed accounts. |
| Grade/Class Structure| Critical | High | Ensures data is organized by academic level. |
| Attendance Module | High | Medium | Tracks student consistency and school compliance. |
| Report Card System | High | High | The core value for students and parents. |
| Ticket System | Medium | Low | Ensures data accuracy and trust in the system. |
| Academic Summary | Medium | Medium | Helps Admin understand the school's health (Financial/Pass rate). |

## 5. Non-Functional Requirements
*   **Security:** Passwords must be hashed before being stored in the database.
*   **Data Integrity:** Foreign keys must ensure that a student cannot be added to a non-existent class.
*   **Usability:** The Student dashboard must be read-only to prevent unauthorized changes to marks.
