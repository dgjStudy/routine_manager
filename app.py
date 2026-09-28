import customtkinter as ctk
import time
from typing import List
from models import ConfigManager, RoutineItem
from tracker import ProcessWindowTracker


# 커밋 테스트트
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def format_time(seconds: int) -> str:
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

class MicroRoutineApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("마이크로 루틴 타이머 (Active Window Tracker)")
        self.geometry("620x680")
        self.minsize(580, 500)

        # 시스템 모듈 초기화
        self.config_manager = ConfigManager("config.json")
        self.routines: List[RoutineItem] = self.config_manager.load_routines()
        self.tracker = ProcessWindowTracker()

        # UI 생성
        self._create_widgets()

        # 실시간 측정 타이머 등록 (1초 간격)
        self.after(1000, self._update_loop)

    def _create_widgets(self):
        # 헤더
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="⏱️ 마이크로 루틴 타이머", 
            font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold")
        )
        title_label.pack(side="left")

        subtitle_label = ctk.CTkLabel(
            header_frame, 
            text="실시간 활성 창 추적 모드", 
            font=ctk.CTkFont(family="Malgun Gothic", size=12),
            text_color="#94A3B8"
        )
        subtitle_label.pack(side="right")

        # 현재 활성 창 대시보드 카드의
        self.active_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        self.active_card.pack(fill="x", padx=20, pady=10)

        active_header = ctk.CTkLabel(
            self.active_card, 
            text="현재 활성 작업 (Active Window)", 
            font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold"),
            text_color="#60A5FA"
        )
        active_header.pack(anchor="w", padx=16, pady=(12, 4))

        self.active_process_label = ctk.CTkLabel(
            self.active_card, 
            text="감지 중...", 
            font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold")
        )
        self.active_process_label.pack(anchor="w", padx=16, pady=(0, 2))

        self.active_title_label = ctk.CTkLabel(
            self.active_card, 
            text="-", 
            font=ctk.CTkFont(family="Malgun Gothic", size=12),
            text_color="#94A3B8"
        )
        self.active_title_label.pack(anchor="w", padx=16, pady=(0, 12))

        # 루틴 리스트 섹션 헤더
        section_label = ctk.CTkLabel(
            self, 
            text="추적 중인 루틴 목록", 
            font=ctk.CTkFont(family="Malgun Gothic", size=15, weight="bold")
        )
        section_label.pack(anchor="w", padx=20, pady=(15, 5))

        # 스크롤 가능한 루틴 리스트 레이아웃
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.routine_cards = []
        self._build_routine_list()

        # 하단 푸터 (저장 / 정보)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=(0, 15))

        save_btn = ctk.CTkButton(
            footer_frame,
            text="설정 및 상태 저장 (config.json)",
            command=self._save_state,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold")
        )
        save_btn.pack(fill="x")

    def _build_routine_list(self):
        # 기존 카드 초기화
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.routine_cards.clear()

        for item in self.routines:
            card = ctk.CTkFrame(self.scrollable_frame, fg_color="#1E293B", corner_radius=10)
            card.pack(fill="x", pady=6)

            # 상단 레이블 (이름 & 타입 뱃지)
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(12, 4))

            name_lbl = ctk.CTkLabel(
                top_row, 
                text=item.name, 
                font=ctk.CTkFont(family="Malgun Gothic", size=15, weight="bold")
            )
            name_lbl.pack(side="left")

            badge_color = "#3B82F6" if item.type == "TARGET" else "#EF4444"
            badge_text = "목표 달성" if item.type == "TARGET" else "시간 제한"
            badge = ctk.CTkLabel(
                top_row, 
                text=f" {badge_text} ", 
                fg_color=badge_color, 
                corner_radius=6,
                font=ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold")
            )
            badge.pack(side="right")

            # 타겟 프로세스 명시
            target_lbl = ctk.CTkLabel(
                card, 
                text=f"대상: {item.target}", 
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color="#64748B"
            )
            target_lbl.pack(anchor="w", padx=14, pady=(0, 6))

            # 프로그레스 바
            progress_bar = ctk.CTkProgressBar(card, height=8, corner_radius=4)
            progress_bar.pack(fill="x", padx=14, pady=(4, 6))
            progress_bar.set(item.progress_ratio)

            # 시간 현황 표시
            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", padx=14, pady=(0, 10))

            time_str = f"{format_time(item.elapsed_seconds)} / {format_time(item.goal_seconds)}"
            time_lbl = ctk.CTkLabel(
                bottom_row, 
                text=time_str, 
                font=ctk.CTkFont(family="Malgun Gothic", size=12)
            )
            time_lbl.pack(side="left")

            status_lbl = ctk.CTkLabel(
                bottom_row, 
                text="대기 중", 
                font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
                text_color="#94A3B8"
            )
            status_lbl.pack(side="right")

            self.routine_cards.append({
                "item": item,
                "card": card,
                "progress_bar": progress_bar,
                "time_lbl": time_lbl,
                "status_lbl": status_lbl
            })

    def _update_loop(self):
        info = self.tracker.get_active_window_info()
        curr_proc = info.get("process_name", "")
        curr_title = info.get("title", "")

        # 대시보드 업데이트
        self.active_process_label.configure(text=curr_proc if curr_proc else "활성 창 없음")
        self.active_title_label.configure(text=curr_title[:45] + ("..." if len(curr_title) > 45 else ""))

        # 루틴 누적 및 UI 업데이트
        for card_data in self.routine_cards:
            item: RoutineItem = card_data["item"]
            progress_bar: ctk.CTkProgressBar = card_data["progress_bar"]
            time_lbl: ctk.CTkLabel = card_data["time_lbl"]
            status_lbl: ctk.CTkLabel = card_data["status_lbl"]
            card: ctk.CTkFrame = card_data["card"]

            # 현재 활성 프로세스와 타겟이 일치하는지 확인
            is_active = (curr_proc.lower() == item.target.lower()) if curr_proc else False

            if is_active:
                item.elapsed_seconds += 1

            # 시간 & 프로그레스 업데이트
            progress_bar.set(item.progress_ratio)
            time_lbl.configure(text=f"{format_time(item.elapsed_seconds)} / {format_time(item.goal_seconds)}")

            # 상태 및 색상 갱신
            if item.type == "TARGET":
                if item.is_goal_reached:
                    status_text = "🎉 목표 달성!"
                    status_color = "#10B981"  # Emerald Green
                    bar_color = "#10B981"
                elif is_active:
                    status_text = "🔥 진행 중"
                    status_color = "#3B82F6"
                    bar_color = "#3B82F6"
                else:
                    status_text = "일시정지"
                    status_color = "#64748B"
                    bar_color = "#3B82F6"
            else:  # LIMIT
                if item.is_goal_reached:
                    status_text = "⚠️ 시간 초과!"
                    status_color = "#EF4444"  # Red
                    bar_color = "#EF4444"
                elif is_active:
                    status_text = "🚨 사용 중 (경고)"
                    status_color = "#F59E0B"  # Amber
                    bar_color = "#F59E0B"
                else:
                    status_text = "안전"
                    status_color = "#64748B"
                    bar_color = "#F59E0B"

            status_lbl.configure(text=status_text, text_color=status_color)
            progress_bar.configure(progress_color=bar_color)

        # 다음 1초 후 재호출
        self.after(1000, self._update_loop)

    def _save_state(self):
        self.config_manager.save_routines(self.routines)

    def on_closing(self):
        self._save_state()
        self.destroy()

if __name__ == "__main__":
    app = MicroRoutineApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
