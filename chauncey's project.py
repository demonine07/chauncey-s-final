import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, date, timedelta
import time
import threading

# this is my config and colors
DATA_FILE = "study_planner_data.json"

COLORS = {
    "bg_dark":      "#1e1e2e",
    "bg_medium":    "#2a2a3e",
    "bg_light":     "#313149",
    "accent":       "#7c6af7",
    "accent_hover": "#9b8dff",
    "success":      "#50fa7b",
    "warning":      "#ffb86c",
    "danger":       "#ff5555",
    "text_primary": "#cdd6f4",
    "text_muted":   "#6c7086",
    "white":        "#ffffff",
    "card":         "#2d2d44",
}

PRIORITIES = ["🔴 High", "🟡 Medium", "🟢 Low"]
STATUSES   = ["Pending ⏳", "In Progress 🔄", "Completed ✅"]
SUBJECTS   = ["Mathematics", "Science", "History", "English",
              "Physics", "Chemistry", "Biology", "Computer Science",
              "Literature", "Geography", "Art", "Music", "Other"]


#  this is my save and load
class DataManager:
    def __init__(self):
        self.data = {
            "tasks":    [],
            "sessions": [],
            "notes":    [],
            "goals":    [],
            "pomodoro_count": 0,
            "total_study_minutes": 0,
        }
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception:
                pass

    def save(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    # ── Tasks ──
    def add_task(self, task):
        task["id"] = int(datetime.now().timestamp() * 1000)
        task["created"] = str(date.today())
        self.data["tasks"].append(task)
        self.save()

    def delete_task(self, task_id):
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        self.save()

    def update_task_status(self, task_id, status):
        for t in self.data["tasks"]:
            if t["id"] == task_id:
                t["status"] = status
        self.save()

    # ── Sessions ──
    def add_session(self, session):
        session["id"] = int(datetime.now().timestamp() * 1000)
        self.data["sessions"].append(session)
        self.data["total_study_minutes"] += session.get("duration", 0)
        self.save()

    # ── Notes ──
    def add_note(self, note):
        note["id"]      = int(datetime.now().timestamp() * 1000)
        note["created"] = str(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.data["notes"].append(note)
        self.save()

    def delete_note(self, note_id):
        self.data["notes"] = [n for n in self.data["notes"] if n["id"] != note_id]
        self.save()

    # ── Goals ──
    def add_goal(self, goal):
        goal["id"]      = int(datetime.now().timestamp() * 1000)
        goal["created"] = str(date.today())
        self.data["goals"].append(goal)
        self.save()

    def delete_goal(self, goal_id):
        self.data["goals"] = [g for g in self.data["goals"] if g["id"] != goal_id]
        self.save()

    def toggle_goal(self, goal_id):
        for g in self.data["goals"]:
            if g["id"] == goal_id:
                g["done"] = not g.get("done", False)
        self.save()

    def increment_pomodoro(self):
        self.data["pomodoro_count"] += 1
        self.save()



#  my designs
def styled_button(parent, text, command, bg=None, fg=None,
                  width=None, font_size=10, padx=14, pady=6):
    bg  = bg  or COLORS["accent"]
    fg  = fg  or COLORS["white"]
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, relief="flat", cursor="hand2",
        font=("Segoe UI", font_size, "bold"),
        padx=padx, pady=pady, bd=0,
        activebackground=COLORS["accent_hover"],
        activeforeground=COLORS["white"],
    )
    if width:
        btn.config(width=width)
    btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["accent_hover"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def card_frame(parent, **kwargs):
    return tk.Frame(parent, bg=COLORS["card"],
                    relief="flat", bd=0, **kwargs)


def section_label(parent, text, size=13):
    return tk.Label(parent, text=text,
                    bg=COLORS["bg_dark"],
                    fg=COLORS["accent"],
                    font=("Segoe UI", size, "bold"))


def info_label(parent, text, size=10, color=None):
    return tk.Label(parent, text=text,
                    bg=COLORS["card"],
                    fg=color or COLORS["text_primary"],
                    font=("Segoe UI", size))


#  dashboard
class DashboardTab(tk.Frame):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm = dm
        self._build()

    def _build(self):
        # ── Title ──
        tk.Label(self, text="📊  Study Dashboard",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 18, "bold")).pack(pady=(20, 5))
        tk.Label(self, text=f"Today: {date.today().strftime('%A, %B %d %Y')}",
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 10)).pack(pady=(0, 20))

        # upper boxxes
        row = tk.Frame(self, bg=COLORS["bg_dark"])
        row.pack(fill="x", padx=30, pady=5)
        self._stat_card(row, "📝 Total Tasks",
                        str(len(self.dm.data["tasks"])),    COLORS["accent"])
        self._stat_card(row, "✅ Completed",
                        str(self._count_completed()),        COLORS["success"])
        self._stat_card(row, "🍅 Pomodoros",
                        str(self.dm.data["pomodoro_count"]), COLORS["warning"])
        self._stat_card(row, "⏱️ Study Time",
                        self._fmt_time(self.dm.data["total_study_minutes"]),
                        COLORS["danger"])

        # upcoming task
        section_label(self, "📌  Upcoming / Pending Tasks").pack(
            anchor="w", padx=30, pady=(20, 5))

        tframe = card_frame(self)
        tframe.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        cols = ("Subject", "Task", "Due Date", "Priority", "Status")
        self.tree = ttk.Treeview(tframe, columns=cols,
                                 show="headings", height=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=COLORS["card"],
                        foreground=COLORS["text_primary"],
                        fieldbackground=COLORS["card"],
                        rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLORS["bg_light"],
                        foreground=COLORS["accent"],
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", COLORS["accent"])])

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130, anchor="center")

        sb = ttk.Scrollbar(tframe, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.refresh()

    def _stat_card(self, parent, label, value, color):
        card = tk.Frame(parent, bg=color, padx=20, pady=15,
                        relief="flat", bd=0)
        card.pack(side="left", expand=True, fill="x", padx=8)
        tk.Label(card, text=value, bg=color, fg="white",
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(card, text=label, bg=color, fg="white",
                 font=("Segoe UI", 9)).pack()

    def _count_completed(self):
        return sum(1 for t in self.dm.data["tasks"]
                   if "Completed" in t.get("status", ""))

    def _fmt_time(self, mins):
        h, m = divmod(int(mins), 60)
        return f"{h}h {m}m"

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for t in self.dm.data["tasks"]:
            if "Completed" not in t.get("status", ""):
                self.tree.insert("", "end", values=(
                    t.get("subject", ""),
                    t.get("title", ""),
                    t.get("due_date", ""),
                    t.get("priority", ""),
                    t.get("status", ""),
                ))



#  TASKS TAB

class TasksTab(tk.Frame):
    def __init__(self, parent, dm: DataManager, refresh_dash):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm            = dm
        self.refresh_dash  = refresh_dash
        self._build()

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=COLORS["bg_dark"])
        hdr.pack(fill="x", padx=20, pady=15)
        tk.Label(hdr, text="📝  Task Manager",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 16, "bold")).pack(side="left")
        styled_button(hdr, "＋ Add Task", self._add_task_dialog
                      ).pack(side="right", padx=5)
        styled_button(hdr, "🗑 Delete", self._delete_task,
                      bg=COLORS["danger"]).pack(side="right", padx=5)
        styled_button(hdr, "✅ Mark Done", self._mark_done,
                      bg=COLORS["success"]).pack(side="right", padx=5)

        # ── Filter Row ──
        frow = tk.Frame(self, bg=COLORS["bg_dark"])
        frow.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(frow, text="Filter by Status:",
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        for s in ["All", "Pending ⏳", "In Progress 🔄", "Completed ✅"]:
            tk.Radiobutton(
                frow, text=s, variable=self.filter_var, value=s,
                bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
                selectcolor=COLORS["bg_light"],
                activebackground=COLORS["bg_dark"],
                font=("Segoe UI", 9), command=self.refresh
            ).pack(side="left", padx=8)

        # ── Tree ──
        cols = ("ID", "Subject", "Title", "Due Date",
                "Priority", "Status", "Notes")
        self.tree = ttk.Treeview(self, columns=cols,
                                 show="headings", height=16)
        widths = [0, 120, 200, 100, 110, 130, 200]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c,
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=w,
                             anchor="center",
                             minwidth=0 if c == "ID" else 50)

        sb = ttk.Scrollbar(self, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(20, 0))
        sb.pack(side="right", fill="y", padx=(0, 10))

        # Tag colors
        self.tree.tag_configure("done",   foreground=COLORS["success"])
        self.tree.tag_configure("high",   foreground=COLORS["danger"])
        self.tree.tag_configure("medium", foreground=COLORS["warning"])

        self.refresh()

    # ── Dialog ──
    def _add_task_dialog(self):
        win = tk.Toplevel(self)
        win.title("Add New Task")
        win.configure(bg=COLORS["bg_dark"])
        win.geometry("420x460")
        win.resizable(False, False)
        win.grab_set()

        def lbl(text):
            tk.Label(win, text=text, bg=COLORS["bg_dark"],
                     fg=COLORS["text_primary"],
                     font=("Segoe UI", 10)).pack(anchor="w",
                                                 padx=20, pady=(10, 2))

        lbl("Subject")
        subj_var = tk.StringVar()
        tk.Entry(win, textvariable=subj_var,
         bg=COLORS["bg_light"],
         fg=COLORS["text_primary"],
         insertbackground="white",
         font=("Segoe UI", 10), width=37).pack(padx=20)

        lbl("Task Title *")
        title_entry = tk.Entry(win, bg=COLORS["bg_light"],
                               fg=COLORS["text_primary"],
                               insertbackground="white",
                               font=("Segoe UI", 10), width=37)
        title_entry.pack(padx=20)

        lbl("Due Date (YYYY-MM-DD)")
        due_entry = tk.Entry(win, bg=COLORS["bg_light"],
                             fg=COLORS["text_primary"],
                             insertbackground="white",
                             font=("Segoe UI", 10), width=37)
        due_entry.insert(0, str(date.today()))
        due_entry.pack(padx=20)

        lbl("Priority")
        priority_var = tk.StringVar(value=PRIORITIES[1])
        ttk.Combobox(win, textvariable=priority_var,
                     values=PRIORITIES, width=35).pack(padx=20)

        lbl("Status")
        status_var = tk.StringVar(value=STATUSES[0])
        ttk.Combobox(win, textvariable=status_var,
                     values=STATUSES, width=35).pack(padx=20)

        lbl("Notes")
        notes_entry = tk.Entry(win, bg=COLORS["bg_light"],
                               fg=COLORS["text_primary"],
                               insertbackground="white",
                               font=("Segoe UI", 10), width=37)
        notes_entry.pack(padx=20)

        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Title is required!",
                                       parent=win)
                return
            self.dm.add_task({
                "subject":  subj_var.get(),
                "title":    title,
                "due_date": due_entry.get().strip(),
                "priority": priority_var.get(),
                "status":   status_var.get(),
                "notes":    notes_entry.get().strip(),
            })
            self.refresh()
            self.refresh_dash()
            win.destroy()

        styled_button(win, "💾  Save Task", save).pack(pady=20)

    def _delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a task first.")
            return
        if messagebox.askyesno("Confirm", "Delete selected task?"):
            task_id = int(self.tree.item(sel[0])["values"][0])
            self.dm.delete_task(task_id)
            self.refresh()
            self.refresh_dash()

    def _mark_done(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a task first.")
            return
        task_id = int(self.tree.item(sel[0])["values"][0])
        self.dm.update_task_status(task_id, "Completed ✅")
        self.refresh()
        self.refresh_dash()

    def _sort(self, col):
        pass   # extend if desired

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        filt = self.filter_var.get()
        for t in self.dm.data["tasks"]:
            status = t.get("status", "")
            if filt != "All" and status != filt:
                continue
            tag = "done" if "Completed" in status else (
                  "high" if "High" in t.get("priority", "") else
                  "medium" if "Medium" in t.get("priority", "") else "")
            self.tree.insert("", "end", iid=str(t["id"]), values=(
                t["id"],
                t.get("subject", ""),
                t.get("title", ""),
                t.get("due_date", ""),
                t.get("priority", ""),
                t.get("status", ""),
                t.get("notes", ""),
            ), tags=(tag,))



#  POMODORO TAB

class PomodoroTab(tk.Frame):
    WORK_MIN  = 25
    BREAK_MIN = 5
    LONG_MIN  = 15

    def __init__(self, parent, dm: DataManager, refresh_dash):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm            = dm
        self.refresh_dash  = refresh_dash
        self._running      = False
        self._thread       = None
        self._seconds_left = self.WORK_MIN * 60
        self._mode         = "Work"
        self._session_count = 0
        self._build()

    def _build(self):
        tk.Label(self, text="🍅  Pomodoro Timer",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 18, "bold")).pack(pady=20)

        # Mode buttons
        mrow = tk.Frame(self, bg=COLORS["bg_dark"])
        mrow.pack()
        for label, mins, mode in [
            ("🧠 Work (25m)",    self.WORK_MIN,  "Work"),
            ("☕ Short Break (5m)", self.BREAK_MIN, "Short Break"),
            ("🛌 Long Break (15m)", self.LONG_MIN,  "Long Break"),
        ]:
            styled_button(mrow, label,
                          lambda m=mins, md=mode: self._set_mode(m, md),
                          bg=COLORS["bg_light"],
                          font_size=9).pack(side="left", padx=6)

        # Timer display
        card = card_frame(self, padx=50, pady=30)
        card.pack(pady=25)

        self.mode_label = tk.Label(card, text="Work Session",
                                   bg=COLORS["card"],
                                   fg=COLORS["accent"],
                                   font=("Segoe UI", 13, "bold"))
        self.mode_label.pack()

        self.timer_label = tk.Label(card, text="25:00",
                                    bg=COLORS["card"],
                                    fg=COLORS["white"],
                                    font=("Consolas", 60, "bold"))
        self.timer_label.pack(pady=10)

        self.session_label = tk.Label(card,
            text="Session: 0  |  Total Pomodoros: 0",
            bg=COLORS["card"], fg=COLORS["text_muted"],
            font=("Segoe UI", 10))
        self.session_label.pack()

        # Controls
        brow = tk.Frame(self, bg=COLORS["bg_dark"])
        brow.pack(pady=10)
        self.start_btn = styled_button(
            brow, "▶  Start", self._start,
            bg=COLORS["success"], font_size=12, padx=20)
        self.start_btn.pack(side="left", padx=8)

        styled_button(brow, "⏸  Pause", self._pause,
                      bg=COLORS["warning"], font_size=12,
                      padx=20).pack(side="left", padx=8)
        styled_button(brow, "⏹  Reset", self._reset,
                      bg=COLORS["danger"], font_size=12,
                      padx=20).pack(side="left", padx=8)

        # Subject log
        tk.Label(self, text="Log study subject:",
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 10)).pack()
        self.log_subj = tk.Entry(self,
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            insertbackground="white",
            font=("Segoe UI", 10), width=30)
        self.log_subj.insert(0, "General")
        self.log_subj.pack(pady=5)

        # Tips
        tips = [
            "💡 Stay focused — avoid distractions during work sessions.",
            "💡 Take real breaks: stand up, stretch, hydrate!",
            "💡 After 4 pomodoros, take a long 15-minute break.",
        ]
        for tip in tips:
            tk.Label(self, text=tip,
                     bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                     font=("Segoe UI", 9, "italic")).pack()

    def _set_mode(self, mins, mode):
        self._running      = False
        self._mode         = mode
        self._seconds_left = mins * 60
        self._update_display()
        self.mode_label.config(text=f"{mode} Session")

    def _start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

    def _pause(self):
        self._running = False

    def _reset(self):
        self._running      = False
        self._seconds_left = self.WORK_MIN * 60
        self._mode         = "Work"
        self._update_display()
        self.mode_label.config(text="Work Session")

    def _countdown(self):
        while self._running and self._seconds_left > 0:
            time.sleep(1)
            if self._running:
                self._seconds_left -= 1
                self.after(0, self._update_display)
        if self._seconds_left == 0 and self._running:
            self._running = False
            self.after(0, self._session_done)

    def _update_display(self):
        m, s = divmod(self._seconds_left, 60)
        self.timer_label.config(text=f"{m:02d}:{s:02d}")

    def _session_done(self):
        if self._mode == "Work":
            self._session_count += 1
            self.dm.increment_pomodoro()
            self.dm.add_session({
                "subject":  self.log_subj.get(),
                "mode":     self._mode,
                "date":     str(date.today()),
                "duration": self.WORK_MIN,
            })
            self.refresh_dash()
        total = self.dm.data["pomodoro_count"]
        self.session_label.config(
            text=f"Session: {self._session_count}  |  Total Pomodoros: {total}")
        messagebox.showinfo("⏰ Time's Up!",
                            f"{self._mode} session complete!\n"
                            f"Total pomodoros today: {self._session_count}")
        self._reset()



#  NOTES TAB

class NotesTab(tk.Frame):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm = dm
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLORS["bg_dark"])
        hdr.pack(fill="x", padx=20, pady=15)
        tk.Label(hdr, text="🗒️  Quick Notes",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 16, "bold")).pack(side="left")
        styled_button(hdr, "＋ Add Note", self._save_note
                      ).pack(side="right", padx=5)
        styled_button(hdr, "🗑 Delete", self._delete_note,
                      bg=COLORS["danger"]).pack(side="right", padx=5)

        # Input area
        inp = card_frame(self, padx=15, pady=12)
        inp.pack(fill="x", padx=20, pady=(0, 10))

        row1 = tk.Frame(inp, bg=COLORS["card"])
        row1.pack(fill="x")
        tk.Label(row1, text="Title:", bg=COLORS["card"],
                 fg=COLORS["text_muted"],
                 font=("Segoe UI", 10)).pack(side="left")
        self.note_title = tk.Entry(row1, bg=COLORS["bg_light"],
                                   fg=COLORS["text_primary"],
                                   insertbackground="white",
                                   font=("Segoe UI", 10), width=30)
        self.note_title.pack(side="left", padx=8)
        tk.Label(row1, text="Subject:", bg=COLORS["card"],
                 fg=COLORS["text_muted"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 4))
        self.note_subj = tk.Entry(row1,
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            insertbackground="white",
            font=("Segoe UI", 10), width=20)
        self.note_subj.insert(0, "General")
        self.note_subj.pack(side="left")

        self.note_body = tk.Text(inp, height=5,
                                 bg=COLORS["bg_light"],
                                 fg=COLORS["text_primary"],
                                 insertbackground="white",
                                 font=("Segoe UI", 10),
                                 wrap="word", padx=6, pady=4)
        self.note_body.pack(fill="x", pady=(8, 0))

        # Notes list
        self.notes_frame = tk.Frame(self, bg=COLORS["bg_dark"])
        self.notes_frame.pack(fill="both", expand=True,
                              padx=20, pady=(0, 15))

        canvas = tk.Canvas(self.notes_frame,
                           bg=COLORS["bg_dark"], highlightthickness=0)
        sb     = ttk.Scrollbar(self.notes_frame,
                               orient="vertical", command=canvas.yview)
        self.scroll_inner = tk.Frame(canvas, bg=COLORS["bg_dark"])
        self.scroll_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._selected_note_id = None
        self.refresh()

    def _save_note(self):
        title = self.note_title.get().strip()
        body  = self.note_body.get("1.0", "end").strip()
        if not title:
            messagebox.showwarning("Warning", "Note title is required!")
            return
        self.dm.add_note({
            "title":   title,
            "subject": self.note_subj.get(),
            "body":    body,
        })
        self.note_title.delete(0, "end")
        self.note_body.delete("1.0", "end")
        self.refresh()

    def _delete_note(self):
        if self._selected_note_id is None:
            messagebox.showinfo("Info", "Click on a note card to select it.")
            return
        if messagebox.askyesno("Confirm", "Delete this note?"):
            self.dm.delete_note(self._selected_note_id)
            self._selected_note_id = None
            self.refresh()

    def refresh(self):
        for w in self.scroll_inner.winfo_children():
            w.destroy()
        for note in reversed(self.dm.data["notes"]):
            self._note_card(note)

    def _note_card(self, note):
        card = tk.Frame(self.scroll_inner,
                        bg=COLORS["card"],
                        pady=8, padx=12,
                        relief="flat", cursor="hand2")
        card.pack(fill="x", pady=4)

        def select(e, nid=note["id"]):
            self._selected_note_id = nid
            for w in self.scroll_inner.winfo_children():
                w.config(bg=COLORS["card"])
                for ch in w.winfo_children():
                    try: ch.config(bg=COLORS["card"])
                    except: pass
            card.config(bg=COLORS["accent"])
            for ch in card.winfo_children():
                try: ch.config(bg=COLORS["accent"])
                except: pass

        card.bind("<Button-1>", select)

        tk.Label(card, text=f"📌 {note['title']}",
                 bg=COLORS["card"], fg=COLORS["white"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card, text=f"{note['subject']}  •  {note['created']}",
                 bg=COLORS["card"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        preview = note["body"][:100] + ("…" if len(note["body"]) > 100 else "")
        tk.Label(card, text=preview,
                 bg=COLORS["card"], fg=COLORS["text_primary"],
                 font=("Segoe UI", 9), wraplength=600,
                 justify="left").pack(anchor="w", pady=(4, 0))

        for w in card.winfo_children():
            w.bind("<Button-1>", select)



#  GOALS TAB

class GoalsTab(tk.Frame):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm = dm
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg_dark"])
        hdr.pack(fill="x", padx=20, pady=15)
        tk.Label(hdr, text="🎯  Study Goals",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 16, "bold")).pack(side="left")
        styled_button(hdr, "＋ Add Goal", self._add_goal
                      ).pack(side="right", padx=5)
        styled_button(hdr, "🗑 Delete", self._delete_goal,
                      bg=COLORS["danger"]).pack(side="right", padx=5)

        # Progress bar summary
        self.progress_label = tk.Label(
            self, text="", bg=COLORS["bg_dark"],
            fg=COLORS["text_muted"], font=("Segoe UI", 10))
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(
            self, orient="horizontal",
            length=500, mode="determinate")
        self.progress_bar.pack(pady=(0, 15))

        # Goals list frame
        cols = ("ID", "Goal", "Deadline", "Done")
        self.tree = ttk.Treeview(self, columns=cols,
                                 show="headings", height=18)
        widths = [0, 350, 120, 80]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center",
                             minwidth=0 if c == "ID" else 60)

        sb = ttk.Scrollbar(self, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(fill="both", expand=True,
                       padx=20, side="left")
        sb.pack(side="right", fill="y", padx=(0, 10))

        self.tree.tag_configure("done", foreground=COLORS["success"])

        styled_button(self, "🔄 Toggle Complete",
                      self._toggle_goal, bg=COLORS["warning"]
                      ).pack(pady=8)
        self.refresh()

    def _add_goal(self):
        goal_text = simpledialog.askstring(
            "New Goal", "Enter your study goal:", parent=self)
        if not goal_text:
            return
        deadline = simpledialog.askstring(
            "Deadline", "Enter deadline (YYYY-MM-DD):",
            parent=self, initialvalue=str(date.today()))
        self.dm.add_goal({
            "goal":     goal_text.strip(),
            "deadline": deadline or "",
            "done":     False,
        })
        self.refresh()

    def _delete_goal(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a goal first.")
            return
        gid = int(self.tree.item(sel[0])["values"][0])
        self.dm.delete_goal(gid)
        self.refresh()

    def _toggle_goal(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a goal first.")
            return
        gid = int(self.tree.item(sel[0])["values"][0])
        self.dm.toggle_goal(gid)
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        goals = self.dm.data["goals"]
        done_count = sum(1 for g in goals if g.get("done"))
        total      = len(goals)
        pct        = int((done_count / total) * 100) if total else 0
        self.progress_bar["value"] = pct
        self.progress_label.config(
            text=f"Goals Completed: {done_count}/{total}  ({pct}%)")
        for g in goals:
            tag  = "done" if g.get("done") else ""
            tick = "✅" if g.get("done") else "⬜"
            self.tree.insert("", "end", iid=str(g["id"]), values=(
                g["id"], g["goal"], g.get("deadline", ""), tick,
            ), tags=(tag,))



#  SCHEDULE TAB

class ScheduleTab(tk.Frame):
    DAYS = ["Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]
    SLOTS = [f"{h:02d}:00" for h in range(6, 23)]

    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.dm       = dm
        self.schedule = {}   # {day: {slot: subject}}
        self._load_schedule()
        self._build()

    def _load_schedule(self):
        self.schedule = self.dm.data.get("schedule", {})
        for d in self.DAYS:
            if d not in self.schedule:
                self.schedule[d] = {}

    def _build(self):
        tk.Label(self, text="📅  Weekly Schedule",
                 bg=COLORS["bg_dark"], fg=COLORS["white"],
                 font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))
        tk.Label(self,
                 text="Click a cell and press 'Assign' to set a subject.",
                 bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 9)).pack(pady=(0, 10))

        # ── Assign Row ──
        arow = tk.Frame(self, bg=COLORS["bg_dark"])
        arow.pack(pady=5)
        self.assign_subj = tk.Entry(arow,
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            insertbackground="white",
            font=("Segoe UI", 10), width=24)
        self.assign_subj.insert(0, "General")
        self.assign_subj.pack(side="left", padx=4)
        styled_button(arow, "Assign to Cell", self._assign_cell
                      ).pack(side="left", padx=4)
        self.cell_info = tk.Label(
            arow, text="No cell selected",
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
            font=("Segoe UI", 9))
        self.cell_info.pack(side="left", padx=10)

        # ── Grid ──
        container = tk.Frame(self, bg=COLORS["bg_dark"])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container, bg=COLORS["bg_dark"],
                           highlightthickness=0)
        xsb    = ttk.Scrollbar(container, orient="horizontal",
                               command=canvas.xview)
        ysb    = ttk.Scrollbar(container, orient="vertical",
                               command=canvas.yview)
        inner  = tk.Frame(canvas, bg=COLORS["bg_dark"])
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(xscrollcommand=xsb.set,
                         yscrollcommand=ysb.set)
        xsb.pack(side="bottom", fill="x")
        ysb.pack(side="right",  fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Header row
        tk.Label(inner, text="Time",
                 bg=COLORS["bg_light"], fg=COLORS["accent"],
                 font=("Segoe UI", 9, "bold"),
                 width=8, relief="flat",
                 padx=4, pady=4).grid(row=0, column=0, padx=1, pady=1)
        for ci, day in enumerate(self.DAYS, start=1):
            tk.Label(inner, text=day,
                     bg=COLORS["bg_light"], fg=COLORS["white"],
                     font=("Segoe UI", 9, "bold"),
                     width=14, relief="flat").grid(
                         row=0, column=ci, padx=1, pady=1)

        self.cell_labels = {}
        self._selected   = None

        for ri, slot in enumerate(self.SLOTS, start=1):
            tk.Label(inner, text=slot,
                     bg=COLORS["bg_medium"],
                     fg=COLORS["text_muted"],
                     font=("Segoe UI", 8),
                     width=8).grid(row=ri, column=0, padx=1, pady=1)
            for ci, day in enumerate(self.DAYS, start=1):
                subj = self.schedule[day].get(slot, "")
                cell = tk.Label(inner,
                                text=subj or "",
                                bg=COLORS["bg_light"] if subj else COLORS["bg_medium"],
                                fg=COLORS["white"],
                                font=("Segoe UI", 8),
                                width=14, height=2,
                                cursor="hand2", relief="flat")
                cell.grid(row=ri, column=ci, padx=1, pady=1)
                self.cell_labels[(day, slot)] = cell
                cell.bind("<Button-1>",
                          lambda e, d=day, s=slot: self._select_cell(d, s))

    def _select_cell(self, day, slot):
        if self._selected:
            old = self.cell_labels[self._selected]
            d, s = self._selected
            old.config(bg=COLORS["bg_light"] if self.schedule[d].get(s)
                       else COLORS["bg_medium"])
        self._selected = (day, slot)
        self.cell_labels[(day, slot)].config(bg=COLORS["accent"])
        self.cell_info.config(text=f"Selected: {day}  {slot}")

    def _assign_cell(self):
        if not self._selected:
            messagebox.showinfo("Info", "Click a cell first.")
            return
        day, slot = self._selected
        subj = self.assign_subj.get()
        if subj.lower() == "— Clear —":
            self.schedule[day].pop(slot, None)
            self.cell_labels[(day, slot)].config(
                text="", bg=COLORS["bg_medium"])
        else:
            self.schedule[day][slot] = subj
            self.cell_labels[(day, slot)].config(
                text=subj, bg=COLORS["bg_light"])
        self.dm.data["schedule"] = self.schedule
        self.dm.save()
        self._selected = None
        self.cell_info.config(text="Saved! ✅")



#  MAIN APPLICATION

class StudyPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚  Student Study Planner")
        self.geometry("1050x680")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg_dark"])
        self.dm = DataManager()
        self._build_ui()

    def _build_ui(self):
        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=COLORS["bg_medium"], width=170)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📚", bg=COLORS["bg_medium"],
                 fg=COLORS["accent"],
                 font=("Segoe UI", 30)).pack(pady=(25, 2))
        tk.Label(sidebar, text="Study\nPlanner",
                 bg=COLORS["bg_medium"], fg=COLORS["white"],
                 font=("Segoe UI", 12, "bold")).pack()
        ttk.Separator(sidebar, orient="horizontal").pack(
            fill="x", pady=15, padx=10)

        self.tab_buttons = {}
        self._active_tab = None

        def nav_btn(icon, label, tab_name):
            frame = tk.Frame(sidebar, bg=COLORS["bg_medium"],
                             cursor="hand2")
            frame.pack(fill="x", pady=2)
            lbl = tk.Label(frame, text=f" {icon}  {label}",
                           bg=COLORS["bg_medium"],
                           fg=COLORS["text_primary"],
                           font=("Segoe UI", 10),
                           anchor="w", padx=12, pady=8)
            lbl.pack(fill="x")

            def click(_=None, tn=tab_name, f=frame, l=lbl):
                self._switch_tab(tn)
                for tf, tl in self.tab_buttons.values():
                    tf.config(bg=COLORS["bg_medium"])
                    tl.config(bg=COLORS["bg_medium"])
                f.config(bg=COLORS["accent"])
                l.config(bg=COLORS["accent"])

            frame.bind("<Button-1>", click)
            lbl.bind("<Button-1>", click)
            frame.bind("<Enter>",
                       lambda e, f=frame, l=lbl: None
                       if self._active_tab == tab_name else (
                           f.config(bg=COLORS["bg_light"]),
                           l.config(bg=COLORS["bg_light"])))
            frame.bind("<Leave>",
                       lambda e, f=frame, l=lbl: None
                       if self._active_tab == tab_name else (
                           f.config(bg=COLORS["bg_medium"]),
                           l.config(bg=COLORS["bg_medium"])))
            self.tab_buttons[tab_name] = (frame, lbl)

        nav_btn("📊", "Dashboard",  "dashboard")
        nav_btn("📝", "Tasks",      "tasks")
        nav_btn("🍅", "Pomodoro",   "pomodoro")
        nav_btn("📅", "Schedule",   "schedule")
        nav_btn("🗒️", "Notes",      "notes")
        nav_btn("🎯", "Goals",      "goals")

        # Bottom info
        ttk.Separator(sidebar, orient="horizontal").pack(
            fill="x", padx=10, pady=10)
        tk.Label(sidebar,
                 text=f"v1.0  •  {date.today().year}",
                 bg=COLORS["bg_medium"], fg=COLORS["text_muted"],
                 font=("Segoe UI", 8)).pack(side="bottom", pady=10)

        # ── Main Content ──
        self.content = tk.Frame(self, bg=COLORS["bg_dark"])
        self.content.pack(side="left", fill="both", expand=True)

        # Build all tabs
        self.tabs: dict[str, tk.Frame] = {
            "dashboard": DashboardTab(self.content, self.dm),
            "tasks":     TasksTab(self.content, self.dm,
                                  self._refresh_dashboard),
            "pomodoro":  PomodoroTab(self.content, self.dm,
                                     self._refresh_dashboard),
            "schedule":  ScheduleTab(self.content, self.dm),
            "notes":     NotesTab(self.content, self.dm),
            "goals":     GoalsTab(self.content, self.dm),
        }

        # Show dashboard
        self._switch_tab("dashboard")
        f, l = self.tab_buttons["dashboard"]
        f.config(bg=COLORS["accent"]); l.config(bg=COLORS["accent"])

    def _switch_tab(self, name):
        self._active_tab = name
        for tab in self.tabs.values():
            tab.pack_forget()
        self.tabs[name].pack(fill="both", expand=True)

    def _refresh_dashboard(self):
        self.tabs["dashboard"].refresh()



#  ENTRY POINT

if __name__ == "__main__":
    app = StudyPlannerApp()
    app.mainloop()