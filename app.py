import customtkinter as ctk
import time
import os
import psutil
from typing import List, Optional
from models import ConfigManager, RoutineItem
from tracker import ProcessWindowTracker

if os.name == "nt":
    import win32gui
    import win32process

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def format_time(seconds: int) -> str:
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def get_running_windows_processes() -> List[dict]:
    """현재 실행 중인 주요 사용자 창 프로그램 목록 반환"""
    results = []
    if os.name != "nt":
        return results

    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title and title not in ["Program Manager", "Settings", "NVIDIA GeForce Overlay"]:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    p = psutil.Process(pid)
                    proc_name = p.name()
                    my_pid = os.getpid()
                    if pid != my_pid and proc_name.lower() not in ["explorer.exe", "searchhost.exe"]:
                        results.append({
                            "name": proc_name,
                            "title": title[:25]
                        })
                except Exception:
                    pass
        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        pass

    seen = set()
    unique_results = []
    for item in results:
        if item["name"].lower() not in seen:
            seen.add(item["name"].lower())
            unique_results.append(item)
    return unique_results[:8]


class RoutineAddDialog(ctk.CTkToplevel):
    """루틴 추가 및 설정을 위한 GUI 다이얼로그 창"""
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.picking = False

        self.title("➕ 새 루틴 추가")
        self.geometry("440x600")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        lbl_title = ctk.CTkLabel(
            self, 
            text="새 추적 루틴 추가", 
            font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold")
        )
        lbl_title.pack(anchor="w", padx=20, pady=(16, 5))

        detect_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=8)
        detect_frame.pack(fill="x", padx=20, pady=(5, 10))

        lbl_detect_info = ctk.CTkLabel(
            detect_frame,
            text="👇 실행 중인 프로그램을 클릭하거나 자동 감지를 누르세요",
            font=ctk.CTkFont(family="Malgun Gothic", size=11),
            text_color="#94A3B8"
        )
        lbl_detect_info.pack(padx=12, pady=(8, 4))

        running_apps = get_running_windows_processes()
        if running_apps:
            apps_scroll = ctk.CTkScrollableFrame(detect_frame, height=75, fg_color="transparent")
            apps_scroll.pack(fill="x", padx=8, pady=(0, 6))

            for app_info in running_apps:
                proc = app_info["name"]
                t_title = app_info["title"]
                btn_app = ctk.CTkButton(
                    apps_scroll,
                    text=f"📱 {proc} ({t_title})",
                    anchor="w",
                    height=24,
                    fg_color="#334155",
                    hover_color="#475569",
                    font=ctk.CTkFont(family="Malgun Gothic", size=10),
                    command=lambda p=proc: self._select_app_directly(p)
                )
                btn_app.pack(fill="x", pady=2)

        self.btn_pick_app = ctk.CTkButton(
            detect_frame,
            text="🎯 화면의 원하는 앱 창 클릭하여 자동 감지",
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
            command=self._start_pick_app
        )
        self.btn_pick_app.pack(fill="x", padx=12, pady=(4, 8))

        lbl_name = ctk.CTkLabel(self, text="목표 이름", font=ctk.CTkFont(family="Malgun Gothic", size=12))
        lbl_name.pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_name = ctk.CTkEntry(self, placeholder_text="예: Code.exe", font=ctk.CTkFont(family="Malgun Gothic", size=13))
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))

        lbl_target = ctk.CTkLabel(self, text="대상 프로세스 파일명 (.exe)", font=ctk.CTkFont(family="Malgun Gothic", size=12))
        lbl_target.pack(anchor="w", padx=20, pady=(5, 2))
        
        self.entry_target = ctk.CTkEntry(self, placeholder_text="예: Code.exe", font=ctk.CTkFont(family="Consolas", size=13))
        self.entry_target.pack(fill="x", padx=20, pady=(0, 10))

        lbl_type = ctk.CTkLabel(self, text="루틴 유형", font=ctk.CTkFont(family="Malgun Gothic", size=12))
        lbl_type.pack(anchor="w", padx=20, pady=(5, 2))
        self.option_type = ctk.CTkOptionMenu(
            self, 
            values=["목표 달성 (TARGET)", "시간 제한 (LIMIT)"],
            font=ctk.CTkFont(family="Malgun Gothic", size=12)
        )
        self.option_type.pack(fill="x", padx=20, pady=(0, 10))

        lbl_goal = ctk.CTkLabel(self, text="목표 시간 (분 단위)", font=ctk.CTkFont(family="Malgun Gothic", size=12))
        lbl_goal.pack(anchor="w", padx=20, pady=(5, 2))
        self.entry_goal = ctk.CTkEntry(self, placeholder_text="60", font=ctk.CTkFont(family="Malgun Gothic", size=13))
        self.entry_goal.insert(0, "60")
        self.entry_goal.pack(fill="x", padx=20, pady=(0, 15))

        btn_save = ctk.CTkButton(
            self, 
            text="저장하기", 
            command=self._save_routine,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold")
        )
        btn_save.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(family="Malgun Gothic", size=11))
        self.lbl_status.pack()

    def _select_app_directly(self, process_name: str):
        self.entry_target.delete(0, "end")
        self.entry_target.insert(0, process_name)
        
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, process_name)
        
        self.lbl_status.configure(text=f"'{process_name}'이(가) 선택되었습니다!", text_color="#10B981")

    def _start_pick_app(self):
        self.picking = True
        self.btn_pick_app.configure(text="⏳ 3초 내에 원하는 앱 창을 클릭하세요!", fg_color="#F59E0B")
        self.lbl_status.configure(text="다른 창을 클릭하여 활성화해 주세요...", text_color="#60A5FA")
        self._check_pick_loop(countdown=15)

    def _check_pick_loop(self, countdown: int):
        if not self.picking:
            return

        info = self.parent.tracker.get_active_window_info()
        proc_name = info.get("process_name", "")

        my_pid = os.getpid()
        is_self = False
        try:
            if proc_name and psutil.Process(my_pid).name().lower() == proc_name.lower():
                is_self = True
        except Exception:
            pass

        if proc_name and not is_self and proc_name.lower() not in ["python.exe", "pythonw.exe"]:
            self.picking = False
            self.entry_target.delete(0, "end")
            self.entry_target.insert(0, proc_name)
            
            self.entry_name.delete(0, "end")
            self.entry_name.insert(0, proc_name)

            self.btn_pick_app.configure(text=f"✓ 감지됨: {proc_name}", fg_color="#10B981")
            self.lbl_status.configure(text=f"'{proc_name}' 프로그램이 선택되었습니다!", text_color="#10B981")
            return

        if countdown <= 0:
            self.picking = False
            self.btn_pick_app.configure(text="🎯 화면의 원하는 앱 창 클릭하여 자동 감지", fg_color="#8B5CF6")
            self.lbl_status.configure(text="감지 시간이 초과되었습니다. 다시 시도해 주세요.", text_color="#EF4444")
            return

        self.after(200, lambda: self._check_pick_loop(countdown - 1))

    def _save_routine(self):
        name = self.entry_name.get().strip()
        target = self.entry_target.get().strip()
        type_str = "TARGET" if "목표 달성" in self.option_type.get() else "LIMIT"
        goal_mins_str = self.entry_goal.get().strip()

        if not name or not target:
            self.lbl_status.configure(text="목표 이름과 대상 프로세스를 입력해 주세요.", text_color="#EF4444")
            return
        try:
            goal_mins = int(goal_mins_str)
            if goal_mins <= 0:
                raise ValueError
        except ValueError:
            self.lbl_status.configure(text="목표 시간은 양의 정수(분)이어야 합니다.", text_color="#EF4444")
            return

        new_item = RoutineItem(
            id=int(time.time()),
            name=name,
            target=target,
            type=type_str,
            goal_seconds=goal_mins * 60,
            elapsed_seconds=0
        )

        if self.on_save_callback:
            self.on_save_callback(new_item)

        self.destroy()


class MicroRoutineApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⏱️ 타이머 모드")
        
        self.is_expanded = False
        self.geometry("380x110")
        self.resizable(True, True)

        # 항시 상단 표시 (Always-on-Top)
        self.attributes("-topmost", True)

        self.config_manager = ConfigManager("config.json")
        self.routines: List[RoutineItem] = self.config_manager.load_routines()
        self.tracker = ProcessWindowTracker()
        self.current_routine_id: Optional[int] = self.routines[0].id if self.routines else None

        self._create_widgets()
        self.after(1000, self._update_loop)

    def _create_widgets(self):
        # 1. 상단 타이머 모드 카드
        self.mini_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0)
        self.mini_card.pack(fill="x", expand=False, padx=0, pady=0)

        # 헤더 바
        mini_header = ctk.CTkFrame(self.mini_card, fg_color="transparent")
        mini_header.pack(fill="x", padx=12, pady=(6, 0))

        self.option_routines = ctk.CTkOptionMenu(
            mini_header,
            values=["루틴 없음"],
            width=165,
            height=26,
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
            command=self._on_routine_selected
        )
        self.option_routines.pack(side="left")

        self.btn_toggle_expand = ctk.CTkButton(
            mini_header,
            text="⚙️ 관리/추가",
            width=70,
            height=24,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Malgun Gothic", size=11),
            command=self._toggle_expand
        )
        self.btn_toggle_expand.pack(side="right")

        self.lbl_badge = ctk.CTkLabel(
            mini_header,
            text=" TARGET ",
            fg_color="#3B82F6",
            corner_radius=4,
            font=ctk.CTkFont(family="Malgun Gothic", size=10, weight="bold")
        )
        self.lbl_badge.pack(side="right", padx=(0, 6))

        # 디지털 타이머 디스플레이
        self.lbl_timer_display = ctk.CTkLabel(
            self.mini_card,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
            text_color="#60A5FA"
        )
        self.lbl_timer_display.pack(pady=(1, 0))

        # 프로그레스 바
        self.mini_progress = ctk.CTkProgressBar(self.mini_card, height=5, corner_radius=2)
        self.mini_progress.pack(fill="x", padx=12, pady=(2, 2))
        self.mini_progress.set(0)

        # 상태 안내 레이블
        mini_footer = ctk.CTkFrame(self.mini_card, fg_color="transparent")
        mini_footer.pack(fill="x", padx=12, pady=(0, 4))

        self.lbl_status = ctk.CTkLabel(
            mini_footer,
            text="감지 중...",
            font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
            text_color="#94A3B8"
        )
        self.lbl_status.pack(side="left")

        # 2. 확장 관리 레이아웃 (여백 최소화 밀착 설계)
        self.expand_frame = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        
        list_header = ctk.CTkFrame(self.expand_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=10, pady=(4, 2))

        lbl_list_title = ctk.CTkLabel(
            list_header, 
            text="전체 루틴 목록", 
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold")
        )
        lbl_list_title.pack(side="left")

        btn_add = ctk.CTkButton(
            list_header,
            text="➕ 스마트 루틴 추가",
            width=110,
            height=22,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold"),
            command=self._open_add_dialog
        )
        btn_add.pack(side="right")

        self.scrollable_frame = ctk.CTkScrollableFrame(self.expand_frame, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.routine_cards = []
        self._refresh_routine_dropdown()
        self._build_routine_list()

    def _refresh_routine_dropdown(self):
        if not self.routines:
            self.option_routines.configure(values=["루틴 없음"])
            self.option_routines.set("루틴 없음")
            self.current_routine_id = None
            return

        names = [r.name for r in self.routines]
        self.option_routines.configure(values=names)

        current_item = self._get_current_routine()
        if current_item:
            self.option_routines.set(current_item.name)
        else:
            self.current_routine_id = self.routines[0].id
            self.option_routines.set(self.routines[0].name)

    def _on_routine_selected(self, selected_name: str):
        for r in self.routines:
            if r.name == selected_name:
                self.current_routine_id = r.id
                break
        self._update_mini_card()

    def _get_current_routine(self) -> Optional[RoutineItem]:
        if not self.routines:
            return None
        for r in self.routines:
            if r.id == self.current_routine_id:
                return r
        return self.routines[0]

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.geometry("380x480")
            self.mini_card.pack_configure(fill="x", expand=False)
            self.expand_frame.pack(fill="both", expand=True, pady=(0, 0))
            self.btn_toggle_expand.configure(text="▲ 타이머 모드")
        else:
            self.expand_frame.pack_forget()
            self.geometry("380x110")
            self.mini_card.pack_configure(fill="both", expand=True)
            self.btn_toggle_expand.configure(text="⚙️ 관리/추가")

    def _build_routine_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.routine_cards.clear()

        for item in self.routines:
            card = ctk.CTkFrame(self.scrollable_frame, fg_color="#1E293B", corner_radius=8)
            card.pack(fill="x", pady=3)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(6, 2))

            name_lbl = ctk.CTkLabel(
                top_row, 
                text=item.name, 
                font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold")
            )
            name_lbl.pack(side="left")

            del_btn = ctk.CTkButton(
                top_row,
                text="삭제",
                width=38,
                height=18,
                fg_color="#334155",
                hover_color="#DC2626",
                font=ctk.CTkFont(family="Malgun Gothic", size=10),
                command=lambda r=item: self._delete_routine(r)
            )
            del_btn.pack(side="right")

            sub_lbl = ctk.CTkLabel(
                card,
                text=f"대상: {item.target} | {format_time(item.elapsed_seconds)} / {format_time(item.goal_seconds)}",
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="#94A3B8"
            )
            sub_lbl.pack(anchor="w", padx=8, pady=(0, 5))

    def _open_add_dialog(self):
        RoutineAddDialog(self, on_save_callback=self._add_routine)

    def _add_routine(self, new_item: RoutineItem):
        self.routines.append(new_item)
        self.current_routine_id = new_item.id
        self.config_manager.save_routines(self.routines)
        self._refresh_routine_dropdown()
        self._build_routine_list()

    def _delete_routine(self, item: RoutineItem):
        self.routines = [r for r in self.routines if r.id != item.id]
        if self.current_routine_id == item.id:
            self.current_routine_id = self.routines[0].id if self.routines else None
        self.config_manager.save_routines(self.routines)
        self._refresh_routine_dropdown()
        self._build_routine_list()

    def _update_mini_card(self):
        curr_item = self._get_current_routine()
        if not curr_item:
            self.lbl_timer_display.configure(text="00:00 / 00:00")
            self.lbl_status.configure(text="⚙️ 관리/추가 버튼으로 루틴을 등록하세요")
            self.mini_progress.set(0)
            return

        self.lbl_timer_display.configure(
            text=f"{format_time(curr_item.elapsed_seconds)} / {format_time(curr_item.goal_seconds)}"
        )
        self.mini_progress.set(curr_item.progress_ratio)
        
        badge_text = "목표 달성" if curr_item.type == "TARGET" else "시간 제한"
        badge_color = "#3B82F6" if curr_item.type == "TARGET" else "#EF4444"
        self.lbl_badge.configure(text=f" {badge_text} ", fg_color=badge_color)

    def _update_loop(self):
        info = self.tracker.get_active_window_info()
        curr_proc = info.get("process_name", "")
        idle_secs = info.get("idle_seconds", 0.0)

        is_idle_over_10s = (idle_secs >= 10.0)

        for item in self.routines:
            is_matched = (curr_proc.lower() == item.target.lower()) if curr_proc else False
            is_active = is_matched and not is_idle_over_10s

            if is_active:
                item.elapsed_seconds += 1
                self.config_manager.save_routines(self.routines)

        self._update_mini_card()

        curr_item = self._get_current_routine()
        if curr_item:
            is_matched = (curr_proc.lower() == curr_item.target.lower()) if curr_proc else False
            
            if curr_item.is_goal_reached:
                status_txt = "🎉 목표 달성!" if curr_item.type == "TARGET" else "⚠️ 시간 초과!"
                status_clr = "#10B981" if curr_item.type == "TARGET" else "#EF4444"
            elif is_matched and is_idle_over_10s:
                status_txt = f"⏸️ 유휴 감지 ({int(idle_secs)}초 미입력)"
                status_clr = "#F59E0B"
            elif is_matched:
                status_txt = "🔥 집계 중..."
                status_clr = "#3B82F6"
            else:
                status_txt = f"대기 중 (현재: {curr_proc[:15] if curr_proc else '없음'})"
                status_clr = "#94A3B8"

            self.lbl_status.configure(text=status_txt, text_color=status_clr)

        self.after(1000, self._update_loop)

    def on_closing(self):
        self.config_manager.save_routines(self.routines)
        self.destroy()

if __name__ == "__main__":
    app = MicroRoutineApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
