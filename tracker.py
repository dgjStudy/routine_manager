import sys
import ctypes
from typing import Optional, Dict

if sys.platform == "win32":
    import win32gui
    import win32process
    import psutil

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

class BaseTrackerProvider:
    """2단계/3단계 확장을 위한 추적 인터페이스 추상 클래스"""
    def get_active_window_info(self) -> Dict[str, any]:
        raise NotImplementedError

class ProcessWindowTracker(BaseTrackerProvider):
    """1단계: Windows OS 최상위 활성 창의 프로세스(.exe) 및 창 제목, 유휴 시간 추적 모듈"""
    
    def get_idle_seconds(self) -> float:
        if sys.platform != "win32":
            return 0.0
        try:
            lastInputInfo = LASTINPUTINFO()
            lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
                millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
                return millis / 1000.0
        except Exception:
            pass
        return 0.0

    def get_active_window_info(self) -> Dict[str, any]:
        idle_secs = self.get_idle_seconds()

        if sys.platform != "win32":
            return {"process_name": "unknown.exe", "title": "Non-Windows OS", "idle_seconds": idle_secs}
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"process_name": "", "title": "Desktop / None", "idle_seconds": idle_secs}
            
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if pid > 0:
                process = psutil.Process(pid)
                process_name = process.name()
            else:
                process_name = ""
                
            return {
                "process_name": process_name,
                "title": title or "No Title",
                "idle_seconds": idle_secs
            }
        except Exception as e:
            return {
                "process_name": "",
                "title": f"Error: {str(e)}",
                "idle_seconds": idle_secs
            }

