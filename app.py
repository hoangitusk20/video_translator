import streamlit as st
import subprocess
from utils import *
import os

#######################################SIDE BAR##################################################
with st.sidebar:
    st.title("Options")
    cuda = st.checkbox("Use cuda")

    if cuda:
        st.write("You are using cuda")
        device = 'cuda'
    else:
        st.write("You are using CPU")
        device = 'cpu'
    st.sidebar.write("---")
    
    voice_over = st.checkbox("Audio Translation")
    if voice_over:
        st.write("The translation will be voiced over.")
        language = st.selectbox(
        "Choose a speaker",
        ("Vietnamese (google voice)",""))
        if 'speed' not in st.session_state:
            st.session_state['speed'] = 1.5
        st.session_state['speed'] = st.slider("Speed", 0.0, 3.0, 1.5)
        test_speed = st.button("Test")
        if test_speed:
            speak_my_text("Xin chào, đây là công cụ hỗ trợ dịch video.",'test_speed.mp3', 'vi', st.session_state['speed'])
            test_audio = "test_speed.mp3"

            # Mở file âm thanh
            with open(test_audio, "rb") as audio_file:
                audio_byte_test = audio_file.read()

            # Hiển thị và phát âm thanh
            st.audio(audio_byte_test, format="audio/mp3")


    else:
        st.write("The translation will appear as subtitles.")
    st.sidebar.write("---")

    
    volumn_adjust = st.checkbox("Volume Adjustment")
    if volumn_adjust:
        st.write("Volume")
        voice_filter = st.checkbox("Apply voice filter")
        st.write("Using voice filter may take additional time")
        background_music = st.slider("Background music", 0, 200, 50)
        if voice_filter:
            original_voice = st.slider("Original voice", 0, 200, 50)
        translated_voice = st.slider("Translated voice", 0, 200, 100)
        st.session_state['bgm'] = background_music
        st.session_state['trans_voice'] = translated_voice
        adjust_volumn_state = st.button("OK")
        if adjust_volumn_state:
            adjust_audio(background_music, translated_voice)
    else:
        st.session_state['bgm'] = 50
        st.session_state['trans_voice'] = 100
            
    
    remove_subtitle = st.checkbox("Draw blackbox to hide subtitle")
    colt, cols = st.columns(2)
    model_size_quick = st.selectbox("Model size for quick translate / transcribe", ("large", "medium", "small", "base", "tiny"))
    describe_quick = st.text_input("Describe for quick translate / transcribe")
    quick_translate = colt.button("Quick translate")
    if quick_translate:
        if voice_over:
            video_black_sub = add_black_rectangle_to_video(st.session_state['file_path'], (0, int(st.session_state['height']*0.85)), (st.session_state['width'], st.session_state['height']))
            srt_path_quick = export_subscription(st.session_state['file_path'], model_size_quick, st.session_state['audio_path'], device)
            translate_srt = f"transcript/{st.session_state['audio_path']}.srt"
            get_translate(srt_path_quick, translate_srt, describe_quick)
            video_add_sub = add_sub(translate_srt, video_black_sub)
            speak_my_subtitle(translate_srt, "speech_segment", st.session_state['speed'])
            result = add_audio_trans(video_add_sub , 'translated.mp4', st.session_state['audio_path'], translate_srt, "speech_segment")
            st.success(f"Complete! Result save as {result}")

        else:
            video_black_sub = add_black_rectangle_to_video(st.session_state['file_path'], (0, int(st.session_state['height']*0.85)), (st.session_state['width'], st.session_state['height']))
            srt_path_quick = export_subscription(st.session_state['file_path'], model_size_quick, st.session_state['audio_path'], device)
            translate_srt = f"transcript/{st.session_state['audio_path']}_translate.srt"
            get_translate(srt_path_quick, translate_srt, describe_quick)
            video_add_sub = add_sub(translate_srt, video_black_sub)
            st.success(f"Complete! Result save as {video_add_sub}")





    
#=======================================================================================================  
def get_file_path():
    # Gọi zenity để chọn tệp
    result = subprocess.run(['zenity', '--file-selection'], stdout=subprocess.PIPE)
    file_path = result.stdout.decode('utf-8').strip()
    filename = str(file_path).split('/')[-1].split('.')[-2]
    audio_path = f"{filename}.mp3"

    cap = cv2.VideoCapture(file_path)

    # Lấy kích thước frame
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    ffmpeg.input(file_path).output(audio_path).run(overwrite_output=True)
    return file_path, audio_path, width, height

# Nút để mở hộp thoại chọn tệp
if 'file_path' not in st.session_state:
    st.session_state['file_path'] = None

if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

choose_file = st.button('Choose file')

if choose_file:
    st.session_state['file_path'], audio_path, width, height = get_file_path()
    st.session_state['audio_path'] =audio_path
    st.session_state['height'] = height
    st.session_state['width'] = width
    st.write(f'Path: {st.session_state["file_path"]}')

# Use the stored file path
file_path = st.session_state['file_path']
audio_path = st.session_state['audio_path']

# Display and process the file if a path is set
if file_path:
    # Display video from local path
    with open(file_path, 'rb') as video_file:
        video_bytes = video_file.read()

    st.video(video_bytes)
    mp4_name = str(file_path).split('/')[-1]

    ## save processing video
    temp_dir = 'temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if remove_subtitle:
        st.header("Hide subtitle")
        col1, col2 = st.columns(2)
        top_left_x = col1.number_input("Top-left x", value=0)  # Added default value
        top_left_y = col2.number_input("Top-left y", value=int(st.session_state['height']*0.85))  # Added default value

        st.write("Bottom right")
        col3, col4 = st.columns(2)
        bottom_right_x = col3.number_input("Bottom-right x", value=st.session_state['width'])  # Added default value
        bottom_right_y = col4.number_input("Bottom-right y", value=st.session_state['height'])  # Added default value
        replace_old = st.checkbox("Replace output with this video")
        apply_blur = st.button("Apply", type="primary")
        if apply_blur:
            if not replace_old:
                st.session_state['file_path'] = add_black_rectangle_to_video(file_path, (top_left_x, top_left_y), (bottom_right_x, bottom_right_x))
            else:
                st.session_state['file_path'] = add_black_rectangle_to_video(file_path, (top_left_x, top_left_y), (bottom_right_x, bottom_right_x))

    
        st.write("---")

    st.header('Generate subtitle to file')
    model_size = st.selectbox("Choose a model size", ("large", "medium", "small", "base", "tiny"))
    translate = st.button("Get subscript", type="primary")
    if translate:
        export_subscription(file_path, model_size, audio_path, device)

    st.header("Translate")
    st.session_state['video_describe'] = st.text_input("Describe this video to get a better translation")
    translate_button = st.button("Translate", type="primary")

    if 'translate_srt_path' not in st.session_state:
        st.session_state['translate_srt_path'] = None


    translate_srt_path = st.session_state['translate_srt_path']

    if translate_button:
        input_path = f"./transcript/{audio_path}.srt"
        translate_srt_path = f"./transcript/{audio_path}_translate.srt"
        st.session_state['translate_srt_path'] = translate_srt_path
        get_translate(input_path, translate_srt_path, st.session_state['video_describe'] )

    if translate_srt_path:
        translate_srt = pysrt.open(translate_srt_path)
        translate_result = st.text_area("Result", get_srt_content(translate_srt), height=500)
    else:
        ranslate_result = st.text_area("Result", height=500)

    add_subtitle = st.button("Add subtitle", type="primary")
    if add_subtitle:
        with open(st.session_state['translate_srt_path'], 'w') as f:
             f.write(translate_result)
        st.session_state['file_path'] = add_sub(translate_srt_path, file_path)

    if voice_over:
        segment_folder = 'speech_segment'
        if not os.path.exists(segment_folder):
            os.mkdir(segment_folder)

        st.header("Audio translate")
        st.write("To synchronize the translated audio with the video frames, we adjust the frame rate. If the translated audio is longer than the video frames, the frames will be extended. If the translated audio is shorter, we will insert some silent sections into the audio to match the frames. Please choose the speed that you feel is most appropriate")
        get_speak = st.button("Speak it out!", type = "primary")

        if get_speak:
            speak_my_subtitle(translate_srt_path, segment_folder, 1.5)
            #strech_audio(translate_srt_path, segment_folder, audio_path)
            st.session_state['file_path']  = add_audio_trans(file_path , 'translated.mp4', audio_path, translate_srt_path, segment_folder)


   
        

        
    

