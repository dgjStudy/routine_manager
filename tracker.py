import sys
from typing import Optional, Dict

if sys.platform == "win32":
    import win32gui
    import win32process
    import psutil

class BaseTrackerProvider:
    """2단계/3단계 확장을 위한 추적 인터페이스 추상 클래스"""
    def get_active_window_info(self) -> Dict[str, str]:
        raise NotImplementedError

class ProcessWindowTracker(BaseTrackerProvider):
    """1단계: Windows OS 최상위 활성 창의 프로세스(.exe) 및 창 제목 추적 모듈"""
    
    def get_active_window_info(self) -> Dict[str, str]:
        if sys.platform != "win32":
            return {"process_name": "unknown.exe", "title": "Non-Windows OS"}
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"process_name": "", "title": "Desktop / None"}
            
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if pid > 0:
                process = psutil.Process(pid)
                process_name = process.name()
            else:
                process_name = ""
                
            return {
                "process_name": process_name,
                "title": title or "No Title"
            }
        except Exception as e:
            return {
                "process_name": "",
                "title": f"Error: {str(e)}"
            }
