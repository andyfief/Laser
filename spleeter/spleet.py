# CtrlP - select interpreter - 3.8 spleeter-env, OR Laser/spleeter-env/Scripts/python.exe
#spleeter-env\Scripts\activate 
#https://github.com/deezer/spleeter/wiki/2.-Getting-started

import os
from spleeter.separator import Separator
import tensorflow as tf
print("GPUs available:", tf.config.list_physical_devices('GPU'))

def separate_audio():
    wavFolderPath = '../labeling/wavs'
    
    for filename in os.listdir(wavFolderPath):
        if filename.endswith('.wav'):
            try:
                # Initialize separator fresh for each file
                separator = Separator('spleeter:4stems')
                
                full_path = os.path.join(wavFolderPath, filename)
                input_audio = full_path
                output_directory = f'../labeling/stems/{filename}'
                
                print(f"Separating audio: {filename}")
                separator.separate_to_file(input_audio, output_directory)
                print(f"Separation complete! Files saved in '{output_directory}'")
                
                # Clean up
                del separator
                tf.keras.backend.clear_session()
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

if __name__ == '__main__':
    separate_audio()