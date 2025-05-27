import sys
import os
import json
import ctypes
import wmi
import tempfile
import subprocess
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QMessageBox, QHBoxLayout, QFrame, QScrollArea, QDialog, QAction,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar, QComboBox, QCheckBox
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtMultimedia import QSound

SETTINGS_FILE = "settings.json"

def load_settings():
    defaults = {
        "filesystem": "auto",
        "enable_sound": True,
        "enable_log": True,
        "auto_refresh": True,
        "suppress_warnings": False
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v
            return data
        except:
            return defaults
    else:
        return defaults

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

settings = load_settings()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

run_as_admin()

class AnimatedSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # USB icon
        if os.path.exists("usb.png"):
            pixmap = QPixmap("usb.png").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(100, 100)
            pixmap.fill(Qt.transparent)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_label)

        # Başlatılıyor yazısı
        self.text_label = QLabel("VolkanFormatter başlatılıyor")
        self.text_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent;")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)

        self.dot_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(500)

    def update_text(self):
        dots = "." * (self.dot_count % 4)
        self.text_label.setText(f"VolkanFormatter başlatılıyor{dots}")
        self.dot_count += 1


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setMinimumSize(350, 300)
        layout = QVBoxLayout(self)
        self.setStyleSheet("font-size: 13px;")

        layout.addWidget(QLabel("<b>Dosya Sistemi Seçimi:</b>"))
        self.fs_combo = QComboBox()
        self.fs_combo.addItems(["auto", "FAT32", "NTFS"])
        self.fs_combo.setCurrentText(settings.get("filesystem", "auto"))
        layout.addWidget(self.fs_combo)

        self.log_checkbox = QCheckBox("🔍 Log Kaydını Aktif Et")
        self.log_checkbox.setChecked(settings.get("enable_log", True))
        layout.addWidget(self.log_checkbox)

        self.sound_checkbox = QCheckBox("🔔 Ses Efekti Aktif")
        self.sound_checkbox.setChecked(settings.get("enable_sound", True))
        layout.addWidget(self.sound_checkbox)

        self.refresh_checkbox = QCheckBox("🔄 Biçimlendirme sonrası otomatik yenile")
        self.refresh_checkbox.setChecked(settings.get("auto_refresh", True))
        layout.addWidget(self.refresh_checkbox)

        self.warn_checkbox = QCheckBox("⚠️ Uyarı Pencerelerini Gösterme")
        self.warn_checkbox.setChecked(settings.get("suppress_warnings", False))
        layout.addWidget(self.warn_checkbox)

        save_btn = QPushButton("Kaydet")
        save_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def save(self):
        settings["filesystem"] = self.fs_combo.currentText()
        settings["enable_log"] = self.log_checkbox.isChecked()
        settings["enable_sound"] = self.sound_checkbox.isChecked()
        settings["auto_refresh"] = self.refresh_checkbox.isChecked()
        settings["suppress_warnings"] = self.warn_checkbox.isChecked()
        save_settings(settings)
        self.accept()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkında")
        self.setMinimumSize(350, 200)
        layout = QVBoxLayout(self)

        about_text = QLabel("""
        <b>VolkanFormatter v1.0.2</b><br><br>
        Bu uygulama, USB / SD kartları hızlı biçimlendirmek için geliştirilmiştir.<br><br>
        <b>Geliştirici:</b> Volkan Aymak<br>
        <b>İletişim:</b> <a href='mailto:volkanaymak@gmail.com'>volkanaymak@gmail.com</a>
        """)
        about_text.setOpenExternalLinks(True)
        about_text.setWordWrap(True)
        layout.addWidget(about_text)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VolkanFormatter v1.0.2")
        self.setMinimumSize(640, 500)
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))

        menubar = self.menuBar()
        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self.open_settings)
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.open_about)

        menu = menubar.addMenu("Menü")
        menu.addAction(settings_action)
        menu.addAction(about_action)

        self.disk_widget = DiskListWidget(self)
        self.setCentralWidget(self.disk_widget)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_():
            self.disk_widget.refresh_disks()

    def open_about(self):
        dlg = AboutDialog(self)
        dlg.exec_()

class DiskListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #222;")
        layout.addWidget(self.status_label)

        self.recent_log = QListWidget()
        self.recent_log.setMaximumHeight(100)
        self.recent_log.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(QLabel("Son İşlemler:"))
        layout.addWidget(self.recent_log)

        self.refresh_btn = QPushButton("🔄 Diskleri Yenile")
        self.refresh_btn.clicked.connect(self.refresh_disks)
        self.refresh_btn.setStyleSheet("font-size: 12px; padding: 6px; font-weight: bold;")
        layout.addWidget(self.refresh_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.disk_container = QWidget()
        self.disk_layout = QVBoxLayout(self.disk_container)
        self.scroll.setWidget(self.disk_container)
        layout.addWidget(self.scroll)

        self.load_recent_logs()
        self.refresh_disks()

    def load_recent_logs(self):
        self.recent_log.clear()
        if os.path.exists("log.txt"):
            with open("log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()[-5:]
                for line in lines[::-1]:
                    self.recent_log.addItem(QListWidgetItem(line.strip()))

    def refresh_disks(self):
        while self.disk_layout.count():
            child = self.disk_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        c = wmi.WMI()
        disks = [d for d in c.Win32_DiskDrive() if d.Size and int(d.Size) <= 128 * 1024**3 and "Fixed" not in (d.MediaType or "")]

        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"Toplam: {len(disks)} disk | Saat: {now}")

        if not disks:
            empty = QLabel("💡 Bağlı uygun USB/SD kart bulunamadı.")
            empty.setStyleSheet("color: gray; font-size: 13px; padding: 10px;")
            self.disk_layout.addWidget(empty)
            return

        for disk in disks:
            try:
                index = int(disk.Index)
                model = disk.Model.strip()
                media = disk.MediaType or "Unknown"
                fs = "Bilinmiyor"
                letter = "Yok"
                for part in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical in part.associators("Win32_LogicalDiskToPartition"):
                        letter = logical.DeviceID
                        fs = logical.FileSystem or fs
                if "C:\\" in letter:
                    continue

                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #f9f9f9;
                        border-radius: 12px;
                        padding: 12px;
                        border: 1px solid #ccc;
                    }
                    QPushButton {
                        background-color: #0078d7;
                        color: white;
                        border-radius: 8px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover {
                        background-color: #005fa3;
                    }
                """)
                card_layout = QHBoxLayout(card)

                icon = QLabel()
                if os.path.exists("usb.png"):
                    icon.setPixmap(QPixmap("usb.png").scaled(40, 40, Qt.KeepAspectRatio))
                else:
                    icon.setText("USB")
                icon.setAlignment(Qt.AlignCenter)

                info = QLabel(
    f"<b>{model}</b><br>"
    f"Tip: {media} | FS: {fs} | Sürücü: {letter}<br>"
    f"Boyut: {int(disk.Size)/(1024**3):.1f} GB"
)

                info.setWordWrap(True)

                left = QVBoxLayout()
                left.addWidget(icon)
                left.addWidget(info)
                card_layout.addLayout(left)

                btn = QPushButton(" Biçimlendir")
                btn.clicked.connect(lambda _, i=index: self.ask_volume_label(i))
                card_layout.addWidget(btn)

                self.disk_layout.addWidget(card)
            except:
                continue
    # ... önceki kodla uyumlu şekilde devam eder
    def ask_volume_label(self, disk_index):
        if not settings.get("suppress_warnings", False):
            reply = QMessageBox.question(self, "Emin misin?", "Disk tamamen silinecek. Devam edilsin mi?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        dlg = QDialog(self)
        dlg.setWindowTitle("Etiket İsmi")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Disk etiketi girin (örn: VOLKAN):"))
        input = QLineEdit("VOLKAN")
        layout.addWidget(input)
        ok_btn = QPushButton("Biçimlendir")
        ok_btn.clicked.connect(lambda: dlg.accept())
        layout.addWidget(ok_btn)
        dlg.exec_()
        label = input.text().strip() or "VOLKAN"
        self.format_disk(disk_index, label)

    def format_disk(self, index, label):
        c = wmi.WMI()
        size = next((int(d.Size) for d in c.Win32_DiskDrive() if int(d.Index) == index), 0)
        fs = settings.get("filesystem", "auto").lower()
        if fs == "auto":
            fs = "ntfs" if size > 32 * 1024 ** 3 else "fat32"

        script = os.path.join(tempfile.gettempdir(), f"format_{index}.txt")
        with open(script, "w") as f:
            f.write(f"select disk {index}\nclean\ncreate partition primary\nselect partition 1\nactive\nformat fs={fs} label={label} quick\nassign\nexit\n")

        success = self.show_progress(script, index, fs.upper())
        try:
            os.remove(script)
        except:
            pass

        if success:
            if settings.get("enable_log", True):
                with open("log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Disk {index} {fs.upper()} olarak biçimlendirildi.\n")

            if settings.get("enable_sound", True) and os.path.exists("ok.wav"):
                QSound.play("ok.wav")

            QMessageBox.information(self, "Başarılı", f"Disk {fs.upper()} olarak biçimlendirildi.")
            self.load_recent_logs()
            if settings.get("auto_refresh", True):
                self.refresh_disks()

    def show_progress(self, script_path, index, fs_label):
        # Blur arka plan
        blur = QWidget(self.parent())
        blur.setStyleSheet("background-color: rgba(0,0,0,120);")
        blur.setGeometry(self.parent().geometry())
        blur.show()

        dlg = QDialog(self)
        dlg.setWindowTitle("Biçimlendiriliyor...")
        layout = QVBoxLayout(dlg)

        step_keywords = {
            "🔄 Disk seçiliyor": ["select disk", "is now the selected disk"],
            "🔄 Temizleniyor": ["clean", "succeeded in cleaning"],
            "🔄 Bölüm oluşturuluyor": ["create partition", "succeeded in creating"],
            "🔄 Biçimlendiriliyor": ["format", "percent completed"],
            "🔄 Sürücü atanıyor": ["assign", "drive letter"],
            "🔄 Tamamlandı": ["exit", "leaving diskpart"]
        }

        labels = []
        for step in step_keywords.keys():
            lbl = QLabel(step)
            lbl.setStyleSheet("font-size: 13px;")
            layout.addWidget(lbl)
            labels.append(lbl)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        layout.addWidget(progress)

        dlg.setFixedSize(360, 320)
        dlg.setModal(True)
        dlg.show()
        QApplication.processEvents()

        output = ""
        error_detected = False
        completed_steps = 0

        try:
            from subprocess import CREATE_NO_WINDOW
            proc = subprocess.Popen(
                ["diskpart", "/s", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=CREATE_NO_WINDOW
            )
            for line in proc.stdout:
                decoded = line.decode(errors="ignore")
                output += decoded
                line_lc = decoded.lower()

                if "error" in line_lc or "erişim engellendi" in line_lc:
                    error_detected = True

                for i, (step, keywords) in enumerate(step_keywords.items()):
                    if any(k in line_lc for k in keywords):
                        if not labels[i].text().startswith("🟢"):
                            labels[i].setText(step.replace("🔄", "🟢"))
                            completed_steps += 1
                            target = int((completed_steps / len(step_keywords)) * 100)
                            current = progress.value()
                            while current < target:
                                current += 1
                                progress.setValue(current)
                                QApplication.processEvents()
                                time.sleep(0.01)

            proc.wait()
        except Exception as e:
            output += f"\n[HATA] {str(e)}"
            error_detected = True

        dlg.close()
        blur.hide()

        with open("diskpart_debug_output.txt", "a", encoding="utf-8") as f:
            f.write(output + "\n\n")

        return not error_detected

def main():
    global window
    app = QApplication(sys.argv)
    splash = AnimatedSplash()
    splash.show()

    def show_main():
        global window
        window = MainWindow()
        window.show()
        splash.close()

    QTimer.singleShot(2000, show_main)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


# VolkanFormatter v1.0.2
# Developed by Volkan Aymak
# Contact: volkanaymak@gmail.com
