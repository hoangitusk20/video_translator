
# Video Translator

## Overview

**Video Translator** is a tool that automates the process of extracting subtitles from videos, translating them, and providing voiceovers in the desired language. The app is built with several powerful libraries to streamline the process:
- **Faster-whisper**: Extracts subtitles from the video.
- **Gemini-API**: Translates the subtitles to the target language.
- **gTTS (Google Text-to-Speech)**: Adds voiceovers for the translated text.
- **FFmpeg**: Ensures that the audio and video are synchronized, handles adding new subtitles, and also covers the old ones.

The application is built with **Streamlit** to provide a user-friendly interface. It's designed to run efficiently on CPU, but due to the lack of GPU on my machine, I couldn't develop the GPU optimization feature. If you don't have access to a GPU, you can run the code via **Google Colab** using the provided link below. The GPU-optimized version has been successfully tested and works well on both **Kaggle** and **Colab**.

This tool is perfect if you want to translate videos but lack high-end hardware. Simply upload your video to YouTube (private mode is fine), paste the YouTube link into the notebook, and click **Save Version** (in Kaggle) or **Run All** (in Google Colab). The app will handle the translation process automatically.

## Installation (for running locally)

To use the app locally, follow the installation steps below. The environment configuration is provided in the `environment.yml` file, so setting it up is straightforward.

1. Clone this repository:
    ```bash
    git clone https://github.com/hoangitusk20/video_translator
    cd video-translator
    ```

2. Create the environment from the `environment.yml` file:
    ```bash
    conda env create -f environment.yml
    ```

3. Activate the environment:
    ```bash
    conda activate streamlit_app
    ```

4. Run the app:
    ```bash
    streamlit run app.py
    ```

This version has been successfully tested on **Ubuntu 22.04** but hasn't been tested on Windows or other operating systems yet.

## Running on Google Colab/Kaggle

If you don't have access to a GPU and prefer a cloud-based solution, you can run the optimized version of this app on **Google Colab** or **Kaggle**. Simply follow the instructions in the provided notebook link.

- Google Colab: [Colab Link](https://colab.research.google.com/drive/1V5iFAJ0EI9hJ9KClNlYAvPhKDm745zjL?usp=sharing)
## Demo

- **Before Translation**: [Video Link Before Translation](https://www.youtube.com/watch?v=S7jC1prfYF0)
- **After Translation**: [Video Link After Translation]()

## Contact

If you have any issues or need assistance with the app, feel free to reach out to me via email at hoangitusk20@gmail.com.

Thank you for visiting this GitHub repository!
