#!/usr/bin/python

import os
import sys
import csv
import youtube_dl
import ffmpeg
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import argparse
import shutil

from PyQt5.QtCore import QStandardPaths, QDir, QFileInfo, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout, QLineEdit, QPushButton, QFileDialog, QCheckBox, QSizePolicy, QTextEdit
from PyQt5.QtGui import QIcon

#To log only errors
class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def progress_hook(d):
    pass

def get_title(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['title']

def download_video(url,
                    ffmpeg_exec,
                    output,
                    start='00:00:00',
                    duration='00:00:15',
                    fade_in_start=0,
                    fade_in_duration=1,
                    fade_out_start=15,
                    fade_out_duration=1):
    k = output.rfind(".")
    tmp_output = output[:k] + '_tmp.' + output[k+1:]
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'outtmpl': tmp_output,
        'logger': MyLogger(),
        'progress_hooks': [progress_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    ffmpeg_input = ffmpeg.input(tmp_output, ss=start, t=duration)
    audio = ffmpeg_input.audio.filter("afade", type='in', start_time=fade_in_start, duration=fade_in_duration)
    audio = audio.filter("afade", type='out', start_time=fade_out_start, duration=fade_out_duration)
    out = ffmpeg.output(audio, filename = output, format='ogg')
    out.run(quiet=True, overwrite_output=True, cmd=ffmpeg_exec)

    if(os.path.exists(tmp_output)):
        os.remove(tmp_output)

def seconds(duration):
    splitted = duration.split(':')
    hours = int(splitted[0])
    mins = int(splitted[1])
    secs = int(splitted[2])
    seconds = int(hours * 3600 + mins * 60 + secs)
    return seconds

def make_blind_test(name, extracts, ffmpeg_exec, output_fn):
    if(not os.path.exists(name)):
        os.mkdir(name)

    def download_and_get_answer(name, n, url, start, duration):
        download_video( url=url,
                        ffmpeg_exec=ffmpeg_exec,
                        output='./{0}/extract_{1}.ogg'.format(name, n),
                        start=start,
                        duration=duration,
                        fade_out_start=seconds(duration)-1)
        return '<li>Extract {0}: <a href="{2}">{1}</a></li>'.format(n, get_title(url), url)

    futures = []
    future_names = dict()
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        for i in range(len(extracts)):
            extract=extracts[i]
            future = executor.submit(download_and_get_answer, name,
                                                                i+1,
                                                                extract['url'],
                                                                extract['start'],
                                                                extract['duration'])
            future_names[future] = 'Extract {}'.format(i+1)
            futures.append(future)

    answers_html = []
    for future in as_completed(futures):
        answers_html.append(future.result())
        output_fn('{} completed'.format(future_names[future]))

    answers_html.sort(key=lambda extract: int(extract[extract.find(' '):extract.find(':')]))

    answers_file=open('{}/answers.html'.format(name), 'w+')
    answers_file.write('<body><ul>')
    answers_file.write(''.join(answers_html))
    answers_file.write('</body></ul>')
    answers_file.close()

def csv_to_extracts_list(csv_file_path):
    extracts=[]
    with open(csv_file_path) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=' ')
        for row in readCSV:
            extract=dict()
            extract['url']=str(row[0])
            try:
                extract['start']=str(row[1])
                if(not extract['start']):
                    raise 'Empty start' 
            except:
                extract['start']='00:00:00'
            try:
                extract['duration']=str(row[2])
                if(not extract['duration']):
                    raise 'Empty duration' 
            except:
                extract['duration']='00:00:15'
            extracts.append(extract)
    return extracts

def build_ui(main_window):
    layout = QGridLayout(main_window)

    ffmpeg_lbl = QLabel(parent=main_window, text="FFmpeg command")
    quizz_name_lbl = QLabel(parent=main_window, text="Quizz name")
    csv_file_path_lbl = QLabel(parent=main_window, text="Extracts file")
    output_folder_lbl = QLabel(parent=main_window, text="Output Folder")


    ffmpeg_path_edit = QLineEdit(parent=main_window, text='ffmpeg')
    ffmpeg_path_btn = QPushButton(parent=main_window, icon=QIcon.fromTheme('folder'))
    quizz_name_edit = QLineEdit(parent=main_window, placeholderText='Quizz name')
    csv_file_path_edit = QLineEdit(parent=main_window)
    csv_file_path_btn = QPushButton(parent=main_window, icon=QIcon.fromTheme('folder'))
    output_folder_edit = QLineEdit(parent=main_window)
    output_folder_edit.setText(QStandardPaths.writableLocation(QStandardPaths.MusicLocation))
    output_folder_btn = QPushButton(parent=main_window, icon=QIcon.fromTheme('folder'))

    zip_checkbox = QCheckBox(parent=main_window, text='Put result in ZIP archive')

    create_btn = QPushButton(parent=main_window, text="Create quizz")

    log = QTextEdit(parent=main_window)
    log.setReadOnly(True)
    log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    layout.addWidget(quizz_name_lbl,0,0)
    layout.addWidget(csv_file_path_lbl,1,0)
    layout.addWidget(output_folder_lbl,2,0)
    layout.addWidget(ffmpeg_lbl,3,0)

    layout.addWidget(quizz_name_edit,0,1)
    layout.addWidget(csv_file_path_edit,1,1)
    layout.addWidget(csv_file_path_btn,1,2)
    layout.addWidget(output_folder_edit,2,1)
    layout.addWidget(output_folder_btn,2,2)
    layout.addWidget(ffmpeg_path_edit,3,1)
    layout.addWidget(ffmpeg_path_btn,3,2)

    layout.addWidget(zip_checkbox,4, 0, 1 ,3)

    layout.addWidget(create_btn,5,0,1,3)
    layout.addWidget(log,6,0,1,3)
    main_window.setLayout(layout)

    def ffmpeg_path_clicked():
        selected_file = ''
        if(sys.platform == 'win32'):
            selected_file = QFileDialog.getOpenFileName(
                main_window,
                'Select Path to ffmpeg',
                QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation),
                'Executable files (*.exe)')[0]
        else:
            dialog = QFileDialog(main_window)
            dialog.setFilter(QDir.Files | QDir.Executable)
            selected_file = dialog.getOpenFileName(
                main_window,
                'Select Path to ffmpeg',
                QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)
                )[0]
        if(selected_file):
            ffmpeg_path_edit.setText(selected_file)

    def csv_file_path_clicked():
        selected_file = QFileDialog.getOpenFileName(
            main_window,
            'Select Extracts file',
            QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
            'CSV Files (*.csv)')[0]
        if(selected_file):
            csv_file_path_edit.setText(selected_file)

    def output_path_clicked():
        selected_file = QFileDialog.getExistingDirectory(
            main_window,
            'Select Output Directory',
            output_folder_edit.text())
        if(selected_file):
            output_folder_edit.setText(selected_file)

    ffmpeg_path_btn.clicked.connect(ffmpeg_path_clicked)
    csv_file_path_btn.clicked.connect(csv_file_path_clicked)
    output_folder_btn.clicked.connect(output_path_clicked)

    def log_fn(str):
        log.setPlainText('{0}\n{1}'.format(
            log.toPlainText(),
            str
            ))

    def set_enabled_input(enabled):
        for input_elem in [ffmpeg_path_edit,
                            ffmpeg_path_btn,
                            quizz_name_edit,
                            csv_file_path_edit,
                            csv_file_path_btn,
                            output_folder_edit,
                            output_folder_btn,
                            zip_checkbox,
                            create_btn]:
            input_elem.setEnabled(enabled)

    def lock_inputs():
        set_enabled_input(False)

    def unlock_inputs():
        set_enabled_input(True)


    class MusicQuizzWorker(QThread):
        clear_log = pyqtSignal()
        log_text = pyqtSignal(str)

        def __init__(self, parent=None):
            QThread.__init__(self, parent)

        def run(self):
            self.clear_log.emit()
            self.log_text.emit('Create quizz {}'.format(quizz_name_edit.text()))
            make_music_quizz_from_args(
                quizz_name=quizz_name_edit.text(),
                extracts_file=csv_file_path_edit.text(),
                ffmpeg_exec=ffmpeg_path_edit.text(),
                zip=zip_checkbox.isChecked(),
                output_fn=self.log_text.emit,
                output_folder=output_folder_edit.text()
                )

    worker = MusicQuizzWorker()
    worker.finished.connect(unlock_inputs)
    worker.clear_log.connect(log.clear)
    worker.log_text.connect(log_fn)

    def make_music_quizz():
        lock_inputs()
        log.setText('')
        worker.start()

    create_btn.clicked.connect(make_music_quizz)

    def check_create_button_active_state():
        quizz_name_empty = bool(quizz_name_edit.text())
        csv_file_path_empty = bool(csv_file_path_edit.text())
        ffmpeg_path_edit_empty = bool(ffmpeg_path_edit.text())
        csv_file_exits = QFileInfo.exists(csv_file_path_edit.text())
        output_folder_edit_empty = bool(output_folder_edit.text())
        output_folder_exists = QFileInfo.exists(output_folder_edit.text())
        create_btn.setEnabled( quizz_name_empty
                                and csv_file_path_empty
                                and csv_file_exits
                                and ffmpeg_path_edit_empty
                                and output_folder_edit_empty
                                and output_folder_exists)

    quizz_name_edit.textChanged.connect(check_create_button_active_state)
    csv_file_path_edit.textChanged.connect(check_create_button_active_state)
    ffmpeg_path_edit.textChanged.connect(check_create_button_active_state)
    output_folder_edit.textChanged.connect(check_create_button_active_state)

    check_create_button_active_state()


def make_music_quizz_from_args(quizz_name, extracts_file, ffmpeg_exec, zip, output_fn, output_folder):
    extracts=csv_to_extracts_list(extracts_file)
    make_blind_test(name=quizz_name, extracts=extracts, ffmpeg_exec=ffmpeg_exec, output_fn=output_fn)
    output_quizz_folder='{0}/{1}'.format(output_folder, quizz_name)
    shutil.move('./{}'.format(quizz_name), output_quizz_folder)
    if(zip):
        cwd = os.getcwd()
        os.chdir(output_folder)
        shutil.make_archive(quizz_name, 'zip', base_dir=quizz_name)
        shutil.rmtree(output_quizz_folder)
        os.chdir(cwd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quizz_name', help='The name of the quizz to generate')
    parser.add_argument('--extracts_file', help='Path to CSV file that contains the song extracts information')
    parser.add_argument('--zip', help='Zip resulting files', action='store_true')
    parser.add_argument('--ffmpeg_exec', help='The path to ffmpeg executable', default='ffmpeg')
    parser.add_argument('--output', help='Place to store the resulting files', default='./')
    args = parser.parse_args()

    if(args.quizz_name and args.extracts_file):
        make_music_quizz_from_args(
            quizz_name=args.quizz_name,
            extracts_file=args.extracts_file,
            ffmpeg_exec=args.ffmpeg_exec,
            zip=args.zip,
            output_fn=print,
            output_folder=args.output
            )
    else:
        app = QApplication([])
        main_window = QWidget()
        main_window.setWindowTitle("Music Quizz Maker")
        main_window.resize(600,400)
        build_ui(main_window)
        main_window.show()
        app.exec_()

if __name__== "__main__":
    main()