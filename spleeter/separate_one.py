import sys
import os
import subprocess
import tensorflow as tf
import gc
from spleeter.separator import Separator

# I spent forever getting 4 stems to work but it is not happening on my GPU.

def limit_gpu_memory_growth():
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"GPU memory growth set for {len(gpus)} GPU(s).")
        except RuntimeError as e:
            print(f"Could not set GPU memory growth: {e}")
    else:
        print("No GPUs found, running on CPU.")

def downsample_audio(input_path, output_path, target_sr=16000):
    # Use ffmpeg to downsample audio to 44.1kHz, overwrite output_path
    # -y overwrites output if exists, -loglevel error to reduce clutter
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_path,
        '-ar', str(target_sr),
        output_path
    ]
    print(f"Downsampling {input_path} to {target_sr} Hz...")
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Downsampled file saved to {output_path}")

def separate_audio_file(input_file_path, output_dir):
    song_name = os.path.splitext(os.path.basename(input_file_path))[0]
    expected_output = os.path.join(output_dir, song_name)
    
    if os.path.isdir(expected_output):
        print(f"✓ Already separated: {os.path.basename(input_file_path)}")
        return
    
    # Temp downsampled wav path
    downsampled_path = os.path.join(output_dir, f"{song_name}_44k.wav")
    
    downsample_audio(input_file_path, downsampled_path)
    
    print(f"⏳ Separating: {os.path.basename(input_file_path)}...")
    
    limit_gpu_memory_growth()
    
    separator = Separator('spleeter:2stems')
    separator.separate_to_file(downsampled_path, output_dir)
    
    print(f"✓ Done! Files saved in: {expected_output}")
    
    # Clean up temp downsampled file to save disk space
    if os.path.exists(downsampled_path):
        os.remove(downsampled_path)
    
    gc.collect()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python separate_one.py <input_wav_path> <output_dir>")
        sys.exit(1)

    input_wav = sys.argv[1]
    output_dir = sys.argv[2]

    separate_audio_file(input_wav, output_dir)
