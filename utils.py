import cv2
import os
import streamlit as st
import subprocess
import re
import ffmpeg
import datetime
import time
import os
import pysrt
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from faster_whisper import WhisperModel
from gtts import gTTS
from pydub import AudioSegment
from mutagen.mp3 import MP3
import numpy as np
import wave
import math
from audiostretchy.stretch import stretch_audio
from moviepy.editor import VideoFileClip, concatenate_videoclips


import matplotlib.pyplot as plt

from mutagen.mp4 import MP4

def get_mp4_duration(file_path):
    audio = MP4(file_path)
    duration = audio.info.length  # Độ dài tính bằng giây
    return duration



def speedup(audio_path, speed):
    # Tạo tệp tạm thời để lưu kết quả
    temp_output = 'temp_speedup.mp3'
    
    # Lệnh ffmpeg
    command = [
        "sox",
        "-t", "mp3", audio_path,
        "-t", "mp3", temp_output,
        "tempo", "-s", str(speed)
    ]

    # Thực hiện lệnh
    subprocess.run(command)

    # Ghi đè nội dung tệp tạm thời lên tệp gốc
    os.replace(temp_output, audio_path)

def stretch_video(input_path, output_path, srt_path, segment_directory):
    t = []
    input_video = input_path
    subtitle = pysrt.open(srt_path)
    stretched_clips = []

    audio_files = [f for f in os.listdir(segment_directory) if f.endswith('.mp3')]
    audio_files.sort(key=lambda f: os.path.getctime(os.path.join(segment_directory, f)))

    video =  VideoFileClip(input_video).set_fps(15)
    for i, sub in enumerate(subtitle):
        start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds/ 1000
        end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
        clip = video.subclip(start, end)
        audio_len = get_mp3_duration(f"{segment_directory}/{audio_files[i]}") 
        srt_len = end - start
        if audio_len > srt_len:
            stretched_clip = clip.speedx(factor=srt_len/audio_len) 
        else:
            stretched_clip = clip
        stretched_clips.append(stretched_clip)
        t.append(max(0, srt_len-audio_len))
    # Gộp tất cả các đoạn lại thành video mới

    final_video = concatenate_videoclips(stretched_clips)
    final_video.write_videofile(output_path)
    return t, final_video.duration

def merge_audio_with_video_ffmpeg(video_path, audio_path1, audio_path2):
    temp_video_path = "temp_video.mp4"
    mixed_audio_path = "mixed_audio.mp3"
    
    # # Bước 1: Trộn hai file âm thanh
    mmix_command = [
        'ffmpeg',
        '-i', audio_path1,
        '-i', audio_path2,
        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=longest',
        '-y',  # ghi đè file output nếu đã tồn tại
        mixed_audio_path
    ]
    
    # Gọi lệnh FFmpeg
    subprocess.run(mmix_command)
    
    # # Bước 2: Kết hợp video với âm thanh đã trộn
    command = [
        'ffmpeg',
        '-y',  # Ghi đè nếu file đã tồn tại
        '-i', video_path,  # Tệp video đầu vào
        '-i', mixed_audio_path,  # Tệp âm thanh đã trộn
        '-c:v', 'copy',    # Giữ nguyên stream video
        '-c:a', 'aac',     # Chuyển đổi âm thanh thành AAC
        '-strict', 'experimental',  # Bắt buộc sử dụng AAC
        '-map', '0:v:0',   # Lấy stream zzvideo từ tệp video
        '-map', '1:a:0',   # Lấy stream âm thanh từ tệp âm thanh đã trộn
        temp_video_path    # Tệp đầu ra
    ]
    
    subprocess.run(command)

    # # Ghi đè file video gốc
    os.replace(temp_video_path, video_path)
    # # Xóa file âm thanh tạm
    os.remove(mixed_audio_path)
    
def change_audio_volume(audio_path, volume_percent):
    # Load the audio file
    audio = AudioSegment.from_file(audio_path)
    
    # Handle the case where volume_percent is 0 (completely mute)
    if volume_percent == 0:
        # Create a silent audio segment with the same length as the original
        audio = AudioSegment.silent(duration=len(audio))
    else:
        # Calculate the change in dB based on percentage
        dB_change = 80 * math.log10(volume_percent / 100)
        
        # Change volume
        audio = audio + dB_change
    
    # Overwrite the original audio file
    audio.export(audio_path, format="mp3")  # Replace 'mp3' with the actual format if different

def stretch_voice_to_fit(srt_path, segment_directory, output_path, audio = None):
    subtitle = pysrt.open(srt_path)
    total_time = 0
    max_time = []
    for i, sub in enumerate(subtitle):
        start = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds/ 1000
        end = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
        srt_time = (end-start)*1000
        audio_time = get_mp3_duration(f"{segment_directory}/segment_{i}.mp3")*1000
        max_time.append(max(srt_time, audio_time))
        total_time += max_time[i]
    
    v = 0
    trans_voice = AudioSegment.silent(duration=total_time)
    for i in range(len(subtitle)):
        segment_audio = AudioSegment.from_file(f"{segment_directory}/segment_{i}.mp3")
        trans_voice = trans_voice.overlay(segment_audio, position=v)    
        v += max_time[i]

    trans_voice.export(output_path, format="mp3")
    return output_path

def add_audio_trans(video_path, output_path, audio_path, srt_path, segment_directory):
    t, d = stretch_video(video_path, output_path, srt_path, segment_directory)
    audio_duration = get_mp3_duration(audio_path)
    speedup(audio_path, audio_duration/d)
    audio_name = audio_path.split('/')[-1].split('.')[-2]
    st.session_state['translated_voice_path'] =  stretch_voice_to_fit(srt_path, segment_directory, f"{audio_name}_translated.mp3")
    adjust_audio(st.session_state['bgm'], st.session_state['trans_voice'])
    merge_audio_with_video_ffmpeg(output_path, st.session_state['translated_voice_path'], st.session_state['audio_path'])
    st.success(f"Complete! New video saving as {output_path}")
    return output_path



def speak_my_text(text, output_path, language='vi', speed=1.0):
    tts = gTTS(text, lang=language)
    tts.save(output_path)
    speedup(output_path, speed)
    

def speak_my_subtitle(srt_path, save_directory, speed):
    segments = pysrt.open(srt_path)
    #combined = AudioSegment.empty()

    for i, segment in enumerate(segments):
        speak_my_text(segment.text, f"{save_directory}/segment_{i}.mp3", 'vi', speed)
        #audio_segment = AudioSegment.from_file(f"{save_directory}/segment_{i}.mp3")
        #combined += audio_segment

    combine_path = f"combine.mp3"
    #combined.export(combine_path, format='mp3')

    return combine_path

def get_mp3_duration(file_path):
    audio = MP3(file_path)
    return audio.info.length

def adjust_audio(background_music_volumn, translated_voice_volumn):
    background_music_duration = get_mp3_duration(st.session_state['audio_path'])
    translated_voice_duration = get_mp3_duration(st.session_state['translated_voice_path'])
    if abs(background_music_duration-translated_voice_duration)>0.5:
        speedup(get_mp3_duration(st.session_state['translated_voice_path']), background_music_duration/ translated_voice_duration)
    change_audio_volume(st.session_state['audio_path'], background_music_volumn)
    change_audio_volume(st.session_state['translated_voice_path'], translated_voice_volumn)

def get_video_duration(input_file):
    """Get the duration of the video in seconds."""
    result = subprocess.run(
        ['ffmpeg', '-i', input_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Extract the duration using regex
    duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
    if duration_match:
        hours, minutes, seconds = map(float, duration_match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def add_black_rectangle_to_video(input_file, top_left, bottom_right):
    """
    Thêm một hình chữ nhật màu đen vào video và hiển thị tiến độ xử lý.
    
    Parameters:
        input_file (str): Đường dẫn đến tệp video đầu vào.
        output_file (str): Đường dẫn đến tệp video đầu ra.
        top_left (tuple): Tọa độ (x, y) của góc trên bên trái của hình chữ nhật.
        bottom_right (tuple): Tọa độ (x2, y2) của góc dưới bên phải của hình chữ nhật.
    """

    # Get the current datetime
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output video file with timestamp
    output_file = f"./temp/temp_video_{current_time}.mp4"
    
    x, y = top_left
    x2, y2 = bottom_right
    width = x2 - x 
    height = y2 - y

    # Get video duration
    duration = get_video_duration(input_file)
    if duration is None:
        st.error("Không thể lấy thời lượng video.")
        return
    
    # Lệnh FFmpeg để thêm hình chữ nhật
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vf', f'drawbox=x={x}:y={y}:w={width}:h={height}:color=black@1:t=fill',
        '-c:a', 'copy',
        output_file
    ]
    
    # Set up the progress bar
    progress_bar = st.progress(0)
    
    # Start ffmpeg process
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Parse the stderr output for progress
    for line in process.stderr:
        # Look for a line containing time information
        time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
        if time_match:
            hours, minutes, seconds = map(float, time_match.groups())
            elapsed_time = hours * 3600 + minutes * 60 + seconds
            # Calculate the progress as a percentage
            progress = min(1.0, elapsed_time / duration)
            progress_bar.progress(progress)
    
    process.wait()  # Ensure ffmpeg finishes
    
    # Ensure the progress bar is full when done
    progress_bar.progress(1.0)
    st.success(f"Complete! Output saved as {output_file}")
    return output_file

def export_subscription(input, model_size, name, device='cpu'):

    if device == "cuda":
        model = WhisperModel(model_size, device="cuda", compute_type="float32")
    else:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(input, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    def time_convert(seconds):
        after_point = seconds - int(seconds)
        after_point = int(after_point * 1000)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{after_point:03}"

    script = ""
    for index, segment in enumerate(segments):
        str_segment = str(index) + "\n" + time_convert(segment.start)+ " --> " + time_convert(segment.end) + "\n" + segment.text + "\n\n"
        script+= str_segment
    with open(f"./transcript/{name}.srt", "w", encoding="utf-8") as f:
        f.write(script)
    st.success("Complete!!")
    return f"./transcript/{name}.srt"

def get_srt_content(sequences):
    content = ""
    for seq in sequences:
        content+= str(seq.index) + "\n" + str(seq.start) + " --> " + str(seq.end) + "\n" + str(seq.text) + "\n\n"
    return content


def get_translate(srt_path, output_path, video_describe):


    API_KEY = ['AIzaSyC4wF1-hvExUZUaWnVa1XlL_PvYiy73P48', 'AIzaSyDbgoXt-k3ZyJhaIAJZR6Wcz1Jp88RhRe8','AIzaSyBPOv4Y6EtsuHg6DqvvTK7rKauutbT9xso', 'AIzaSyAzEQttlKZuMUVs1FsEXyuuvpbhpbVrfa8']

    genai.configure(api_key='AIzaSyDbgoXt-k3ZyJhaIAJZR6Wcz1Jp88RhRe8')

    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
    safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    chat_session = model.start_chat(
    history=[
    ]
    )
    API_index = 0
    subtitle = pysrt.open(srt_path)
    print(type(subtitle))
    print(srt_path)
    vietsub = ""
    batch = 50
    for i in range(0, len(subtitle), batch):
        describe = f"{video_describe}. Chú ý giữ nguyên số thứ tự và timestamp của segment.Địnhh dạng output giống như file srt (không có ý tự khác như ``` hay srt...), lưu ý định dạng thời gian các segment là HH:mm:ss,SSS."
        if i + batch > len(subtitle):
            prompt = f"{get_srt_content(subtitle[i:])} {describe}"
        else:
            prompt = f"{get_srt_content(subtitle[i:i+batch])} {describe}"
        check = True
        while check:
            try:
                print("Response with API", API_index)
                response = chat_session.send_message(prompt)
                check = False
            except:
                print(API_index)
                API_index += 1
                genai.configure(api_key=API_KEY[API_index])
        vietsub += response.text + '\n'
        print(response.text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(vietsub)

import subprocess

def add_sub(subtitle_file, input_video):
    # Get the current datetime
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output video file with timestamp
    output_video = f"./temp/temp_video_{current_time}.mp4"
    
    # Command to add subtitles using FFmpeg
    command = [
        'ffmpeg',
        '-i', input_video,            # Input video file
        '-vf', f'subtitles={subtitle_file}',  # Subtitles filter with .srt file
        output_video                  # Output video file with timestamp
    ]
    
    # Run the FFmpeg command
    subprocess.run(command, check=True)
    
    # Replace the original video with the new one (optional, remove if not needed)    
    # Notify success and show the output video path with timestamp
    st.success(f"Complete! Output saved as {output_video}")
    return output_video
