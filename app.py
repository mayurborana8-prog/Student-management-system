"""
Student Management System
BCA Python Mini Project
Technology: Python, Tkinter, SQLite
Run: python app.py
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import csv


class StudentDatabase:
    """Handles all database operations for students, attendance and marks."""

    def __init__(self, db_name="students.db"):
        self.connection = sqlite3.connect(db_name)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                semester TEXT NOT NULL,
                phone TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                obtained REAL NOT NULL,
                maximum REAL NOT NULL,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
        """)
        self.connection.commit()

    def add_student(self, values):
        self.connection.execute(
            "INSERT INTO students (roll_no, name, course, semester, phone) VALUES (?, ?, ?, ?, ?)",
            values
        )
        self.connection.commit()

    def update_student(self, student_id, values):
        self.connection.execute(
            "UPDATE students SET roll_no=?, name=?, course=?, semester=?, phone=? WHERE id=?",
            (*values, student_id)
        )
        self.connection.commit()

    def delete_student(self, student_id):
        self.connection.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.connection.commit()

    def get_students(self, search=""):
        return self.connection.execute("""
            SELECT id, roll_no, name, course, semester, phone
            FROM students
            WHERE roll_no LIKE ? OR name LIKE ?
            ORDER BY name
        """, (f"%{search}%", f"%{search}%")).fetchall()

    def get_student_by_roll(self, roll_no):
        return self.connection.execute(
            "SELECT id, roll_no, name FROM students WHERE roll_no=?", (roll_no,)
        ).fetchone()

    def add_attendance(self, student_id, attendance_date, status):
        self.connection.execute(
            "INSERT INTO attendance (student_id, attendance_date, status) VALUES (?, ?, ?)",
            (student_id, attendance_date, status)
        )
        self.connection.commit()

    def get_attendance(self):
        return self.connection.execute("""
            SELECT s.roll_no, s.name, a.attendance_date, a.status
            FROM attendance a JOIN students s ON a.student_id=s.id
            ORDER BY a.attendance_date DESC, s.name
        """).fetchall()

    def add_marks(self, student_id, subject, obtained, maximum):
        self.connection.execute(
            "INSERT INTO marks (student_id, subject, obtained, maximum) VALUES (?, ?, ?, ?)",
            (student_id, subject, obtained, maximum)
        )
        self.connection.commit()

    def get_marks(self):
        return self.connection.execute("""
            SELECT s.roll_no, s.name, m.subject, m.obtained, m.maximum,
                   ROUND((m.obtained * 100.0 / m.maximum), 2)
            FROM marks m JOIN students s ON m.student_id=s.id
            ORDER BY s.name, m.subject
        """).fetchall()

    def get_counts(self):
        students = self.connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        attendance = self.connection.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        marks = self.connection.execute("SELECT COUNT(*) FROM marks").fetchone()[0]
        return students, attendance, marks

    def close(self):
        self.connection.close()


class StudentManagementApp:
    """Main Tkinter application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Student Management System")
        self.root.geometry("1050x680")
        self.root.minsize(900, 580)
        self.root.configure(bg="#f3f6fb")
        self.db = StudentDatabase()
        self.selected_student_id = None

        self.setup_style()
        self.build_header()
        self.build_tabs()
        self.refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 10, "bold"))
        style.configure("TButton", padding=7, font=("Segoe UI", 9))

    def build_header(self):
        header = tk.Frame(self.root, bg="#182848", height=86)
        header.pack(fill="x")
        tk.Label(header, text="STUDENT MANAGEMENT SYSTEM",
                 bg="#182848", fg="white",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=24, pady=(15, 0))
        tk.Label(header, text="A Python-based application to manage student records, attendance and marks",
                 bg="#182848", fg="#d8e2f3",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=26, pady=(3, 12))

    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=16)

        self.dashboard_tab = ttk.Frame(self.notebook, padding=18)
        self.students_tab = ttk.Frame(self.notebook, padding=18)
        self.attendance_tab = ttk.Frame(self.notebook, padding=18)
        self.marks_tab = ttk.Frame(self.notebook, padding=18)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.students_tab, text="Students")
        self.notebook.add(self.attendance_tab, text="Attendance")
        self.notebook.add(self.marks_tab, text="Marks")

        self.build_dashboard()
        self.build_students()
        self.build_attendance()
        self.build_marks()

    def build_dashboard(self):
        ttk.Label(self.dashboard_tab, text="Dashboard",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 5))
        ttk.Label(self.dashboard_tab, text="Quick overview of the information stored in the system.",
                  foreground="#566").pack(anchor="w", pady=(0, 22))

        cards = ttk.Frame(self.dashboard_tab)
        cards.pack(fill="x", pady=5)
        self.stat_vars = []
        for title in ("Registered Students", "Attendance Entries", "Marks Entries"):
            card = tk.Frame(cards, bg="white", highlightbackground="#dce3ee",
                            highlightthickness=1, padx=22, pady=20)
            card.pack(side="left", fill="both", expand=True, padx=7)
            tk.Label(card, text=title, bg="white", fg="#526078",
                     font=("Segoe UI", 10)).pack(anchor="w")
            value = tk.StringVar(value="0")
            self.stat_vars.append(value)
            tk.Label(card, textvariable=value, bg="white", fg="#182848",
                     font=("Segoe UI", 27, "bold")).pack(anchor="w", pady=(8, 0))

        info = tk.Frame(self.dashboard_tab, bg="#eaf0fa", padx=18, pady=16)
        info.pack(fill="x", pady=28)
        tk.Label(info, text="How to use", bg="#eaf0fa", fg="#182848",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(info, text=(
            "1. Open Students to add, search, update or delete student records.\n"
            "2. Open Attendance to record a student's daily attendance.\n"
            "3. Open Marks to save subject marks and view calculated percentages.\n"
            "4. Use Export CSV in the Students tab to save the student list."
        ), justify="left", bg="#eaf0fa", fg="#26364d",
                 font=("Segoe UI", 10), pady=8).pack(anchor="w")

    def build_students(self):
        ttk.Label(self.students_tab, text="Student Records",
                  font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 12))

        form = ttk.LabelFrame(self.students_tab, text="Student details", padding=12)
        form.pack(fill="x", pady=(0, 12))

        self.student_vars = {key: tk.StringVar() for key in
                             ("roll", "name", "course", "semester", "phone")}
        fields = [
            ("Roll number", "roll"), ("Full name", "name"),
            ("Course", "course"), ("Semester", "semester"), ("Phone", "phone")
        ]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=5, pady=3)
            ttk.Entry(form, textvariable=self.student_vars[key], width=19).grid(
                row=1, column=i, padx=5, pady=3, sticky="ew")
            form.columnconfigure(i, weight=1)

        actions = ttk.Frame(form)
        actions.grid(row=2, column=0, columnspan=5, sticky="w", padx=4, pady=(10, 0))
        ttk.Button(actions, text="Add Student", command=self.add_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Update Selected", command=self.update_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Delete Selected", command=self.delete_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Clear Form", command=self.clear_student_form).pack(side="left", padx=3)
        ttk.Button(actions, text="Export CSV", command=self.export_students).pack(side="left", padx=3)

        search_row = ttk.Frame(self.students_tab)
        search_row.pack(fill="x", pady=(0, 8))
        ttk.Label(search_row, text="Search by name or roll number:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=8)
        self.search_var.trace_add("write", lambda *_: self.refresh_students())
        ttk.Button(search_row, text="Show All", command=lambda: self.search_var.set("")).pack(side="left")

        columns = ("id", "roll", "name", "course", "semester", "phone")
        self.student_tree = ttk.Treeview(self.students_tab, columns=columns, show="headings")
        headings = {"id": "ID", "roll": "Roll No.", "name": "Student Name",
                    "course": "Course", "semester": "Semester", "phone": "Phone"}
        widths = {"id": 45, "roll": 110, "name": 230, "course": 160, "semester": 100, "phone": 140}
        for col in columns:
            self.student_tree.heading(col, text=headings[col])
            self.student_tree.column(col, width=widths[col], anchor="center")
        self.student_tree.pack(fill="both", expand=True)
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_select)

    def build_attendance(self):
        ttk.Label(self.attendance_tab, text="Attendance Management",
                  font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 14))
        form = ttk.LabelFrame(self.attendance_tab, text="Record attendance", padding=14)
        form.pack(fill="x", pady=(0, 14))

        self.att_roll_var = tk.StringVar()
        self.att_date_var = tk.StringVar(value=date.today().isoformat())
        self.att_status_var = tk.StringVar(value="Present")
        ttk.Label(form, text="Student roll number").grid(row=0, column=0, sticky="w", padx=6)
        ttk.Entry(form, textvariable=self.att_roll_var, width=22).grid(row=1, column=0, padx=6, pady=6)
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=1, sticky="w", padx=6)
        ttk.Entry(form, textvariable=self.att_date_var, width=18).grid(row=1, column=1, padx=6, pady=6)
        ttk.Label(form, text="Status").grid(row=0, column=2, sticky="w", padx=6)
        ttk.Combobox(form, textvariable=self.att_status_var, values=("Present", "Absent"),
                     state="readonly", width=15).grid(row=1, column=2, padx=6, pady=6)
        ttk.Button(form, text="Save Attendance", command=self.add_attendance).grid(
            row=1, column=3, padx=12)
        columns = ("roll", "name", "date", "status")
        self.att_tree = ttk.Treeview(self.attendance_tab, columns=columns, show="headings")
        for col, heading, width in zip(columns, ("Roll No.", "Student Name", "Date", "Status"),
                                        (130, 260, 180, 150)):
            self.att_tree.heading(col, text=heading)
            self.att_tree.column(col, width=width, anchor="center")
        self.att_tree.pack(fill="both", expand=True)

    def build_marks(self):
        ttk.Label(self.marks_tab, text="Marks Management",
                  font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 14))
        form = ttk.LabelFrame(self.marks_tab, text="Add subject marks", padding=14)
        form.pack(fill="x", pady=(0, 14))

        self.mark_roll_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.obtained_var = tk.StringVar()
        self.maximum_var = tk.StringVar(value="100")
        fields = [
            ("Student roll number", self.mark_roll_var),
            ("Subject", self.subject_var),
            ("Marks obtained", self.obtained_var),
            ("Maximum marks", self.maximum_var)
        ]
        for i, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=6)
            ttk.Entry(form, textvariable=variable, width=20).grid(row=1, column=i, padx=6, pady=6)
        ttk.Button(form, text="Save Marks", command=self.add_marks).grid(
            row=1, column=4, padx=12)
        columns = ("roll", "name", "subject", "obtained", "maximum", "percentage")
        self.mark_tree = ttk.Treeview(self.marks_tab, columns=columns, show="headings")
        headings = ("Roll No.", "Student Name", "Subject", "Obtained", "Maximum", "Percentage")
        widths = (100, 210, 170, 100, 100, 120)
        for col, heading, width in zip(columns, headings, widths):
            self.mark_tree.heading(col, text=heading)
            self.mark_tree.column(col, width=width, anchor="center")
        self.mark_tree.pack(fill="both", expand=True)

    def validate_student(self):
        values = tuple(self.student_vars[k].get().strip()
                       for k in ("roll", "name", "course", "semester", "phone"))
        if not all(values[:4]):
            messagebox.showwarning("Missing information",
                                   "Roll number, name, course and semester are required.")
            return None
        if len(values[0]) > 20:
            messagebox.showwarning("Invalid roll number", "Roll number must be 20 characters or fewer.")
            return None
        if values[4] and not values[4].replace("+", "").replace("-", "").replace(" ", "").isdigit():
            messagebox.showwarning("Invalid phone", "Enter a valid phone number.")
            return None
        return values

    def add_student(self):
        values = self.validate_student()
        if values is None:
            return
        try:
            self.db.add_student(values)
            messagebox.showinfo("Success", "Student added successfully.")
            self.clear_student_form()
            self.refresh_all()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate roll number", "This roll number already exists.")

    def update_student(self):
        if self.selected_student_id is None:
            messagebox.showwarning("Select a record", "Select a student from the table first.")
            return
        values = self.validate_student()
        if values is None:
            return
        try:
            self.db.update_student(self.selected_student_id, values)
            messagebox.showinfo("Success", "Student record updated.")
            self.clear_student_form()
            self.refresh_all()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate roll number", "Another student already uses this roll number.")

    def delete_student(self):
        if self.selected_student_id is None:
            messagebox.showwarning("Select a record", "Select a student from the table first.")
            return
        if messagebox.askyesno("Confirm deletion",
                               "Delete this student and their attendance/marks records?"):
            self.db.delete_student(self.selected_student_id)
            self.clear_student_form()
            self.refresh_all()

    def on_student_select(self, _event):
        selection = self.student_tree.selection()
        if not selection:
            return
        row = self.student_tree.item(selection[0], "values")
        self.selected_student_id = int(row[0])
        for key, value in zip(("roll", "name", "course", "semester", "phone"), row[1:]):
            self.student_vars[key].set(value)

    def clear_student_form(self):
        self.selected_student_id = None
        for variable in self.student_vars.values():
            variable.set("")
        for item in self.student_tree.selection():
            self.student_tree.selection_remove(item)

    def add_attendance(self):
        roll = self.att_roll_var.get().strip()
        day = self.att_date_var.get().strip()
        status = self.att_status_var.get()
        if not roll or not day:
            messagebox.showwarning("Missing information", "Enter a roll number and date.")
            return
        try:
            date.fromisoformat(day)
        except ValueError:
            messagebox.showerror("Invalid date", "Use the date format YYYY-MM-DD.")
            return
        student = self.db.get_student_by_roll(roll)
        if not student:
            messagebox.showerror("Student not found", "No student has this roll number.")
            return
        try:
            self.db.add_attendance(student[0], day, status)
            self.att_roll_var.set("")
            self.refresh_all()
            messagebox.showinfo("Success", "Attendance saved.")
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))

    def add_marks(self):
        roll = self.mark_roll_var.get().strip()
        subject = self.subject_var.get().strip()
        try:
            obtained = float(self.obtained_var.get())
            maximum = float(self.maximum_var.get())
            if obtained < 0 or maximum <= 0 or obtained > maximum:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid marks",
                                 "Enter valid numbers. Obtained marks must be between 0 and maximum marks.")
            return
        if not roll or not subject:
            messagebox.showwarning("Missing information", "Enter roll number and subject.")
            return
        student = self.db.get_student_by_roll(roll)
        if not student:
            messagebox.showerror("Student not found", "No student has this roll number.")
            return
        try:
            self.db.add_marks(student[0], subject, obtained, maximum)
            self.mark_roll_var.set("")
            self.subject_var.set("")
            self.obtained_var.set("")
            self.maximum_var.set("100")
            self.refresh_all()
            messagebox.showinfo("Success", "Marks saved.")
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))

    def export_students(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile="student_records.csv")
        if not path:
            return
        try:
            rows = self.db.get_students()
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Roll Number", "Name", "Course", "Semester", "Phone"])
                writer.writerows(rows)
            messagebox.showinfo("Export complete", f"Student records exported to:\n{path}")
        except OSError as error:
            messagebox.showerror("File error", str(error))

    def refresh_students(self):
        if not hasattr(self, "student_tree"):
            return
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        for row in self.db.get_students(self.search_var.get() if hasattr(self, "search_var") else ""):
            self.student_tree.insert("", "end", values=row)

    def refresh_attendance(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        for row in self.db.get_attendance():
            self.att_tree.insert("", "end", values=row)

    def refresh_marks(self):
        for item in self.mark_tree.get_children():
            self.mark_tree.delete(item)
        for row in self.db.get_marks():
            self.mark_tree.insert("", "end", values=row)

    def refresh_dashboard(self):
        for variable, count in zip(self.stat_vars, self.db.get_counts()):
            variable.set(str(count))

    def refresh_all(self):
        self.refresh_students()
        self.refresh_attendance()
        self.refresh_marks()
        self.refresh_dashboard()

    def on_close(self):
        self.db.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentManagementApp(root)
    root.mainloop()
