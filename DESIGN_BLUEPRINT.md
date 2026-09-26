# Backend Design Blueprint - Student ERP System

This document defines the API architecture, User Flow, and Role-Based Access Control (RBAC) for the Student ERP backend built with FastAPI.

## 1. User Identity & Role Logic
Every user has a **Profile** and a **Role**. The role is the "Key" that opens different parts of the system.

### User Roles:
- **ADMIN**: Full system control.
- **TEACHER**: Manages attendance and marks for assigned classes.
- **STUDENT**: Read-only access to personal performance and attendance.

### The "Profile Fetch" Logic:
When any user logs in, the system executes a `GET /me` call. This returns:
- Basic Info: Name, Email, Phone.
- Role: (Admin/Teacher/Student).
- Role-Specific Data: 
    - If Student $\rightarrow$ Roll No, Class ID.
    - If Teacher $\rightarrow$ Specialization, Assigned Class.

---

## 2. Action Matrix (API Endpoints)

### 🔑 Authentication (All Users)
| Endpoint | Method | Action | Role |
| :--- | :--- | :--- | :--- |
| `/auth/login` | POST | Login $\rightarrow$ returns JWT Token | All |
| `/auth/me` | GET | Fetch my profile and my role | All |

### 🎓 Student Actions
| Endpoint | Method | Action | Logic |
| :--- | :--- | :--- | :--- |
| `/student/attendance` | GET | View present/past attendance | Filtered by `student_id` |
| `/student/performance`| GET | View current & past report cards | Filtered by `student_id` |
| `/student/tickets` | POST | Create a ticket for record errors | Linked to `student_id` |

### 🍎 Teacher Actions
| Endpoint | Method | Action | Logic |
| :--- | :--- | :--- | :--- |
| `/teacher/attendance` | POST | Mark attendance for a class | Updates `Attendance` table |
| `/teacher/students` | GET | View list of students in their class| Filtered by `class_teacher_id` |
| `/teacher/marks` | PUT | Update subject marks for students | Updates `Reports` table |

### ⚙️ Admin Actions
| Endpoint | Method | Action | Logic |
| :--- | :--- | :--- | :--- |
| `/admin/users` | POST | Create Student/Teacher accounts | Inserts into `Users` & `Profiles` |
| `/admin/classes` | PUT | Assign Teacher to a Class | Updates `Classes` table |
| `/admin/academics` | GET | View school-wide summary | Aggregates `Reports` & `Fees` |
| `/admin/tickets` | GET/PUT | View and Resolve student tickets | Manages `Tickets` table |

---

## 3. Database Relationship Blueprint
To support the "Fetch Profile" feature, the data flows as follows:

`User` $\xrightarrow{1:1}$ `Profile` $\xrightarrow{1:N}$ `Role`

1. **Login** $\rightarrow$ Finds `User` by email.
2. **Profile Fetch** $\rightarrow$ Uses `User.id` to find the corresponding entry in `Student_Profile` or `Teacher_Profile`.
3. **Role Check** $\rightarrow$ The `role` column in the User table tells the backend which endpoints the user is allowed to hit.

---

## 4. Implementation Roadmap
1. **Phase 1: Infrastructure** $\rightarrow$ FastAPI setup + SQLAlchemy Models + DB Connection.
2. **Phase 2: Auth System** $\rightarrow$ JWT implementation + Password Hashing + `/auth/me` profile fetch.
3. **Phase 3: Admin Module** $\rightarrow$ User creation and Class assignment.
4. **Phase 4: Teacher/Student Modules** $\rightarrow$ Attendance and Report Card logic.
5. **Phase 5: Support System** $\rightarrow$ Ticket creation and resolution.
