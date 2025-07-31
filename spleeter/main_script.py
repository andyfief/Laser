import os
import subprocess

def separate_all():
    # Change this to your venv python executable path
    venv_python = '../spleeter-env/Scripts/python.exe'
    # Path to the separation script
    script_path = os.path.join(os.path.dirname(__file__), "separate_one.py")
    
    wavFolderPath = '../labeling/playlist_wavs'
    outputBaseDir = '../labeling/stems'
    
    filenames = os.listdir(wavFolderPath)
    
    for filename in filenames:
        if not filename.endswith('.wav'):
            continue
        
        songName = os.path.splitext(filename)[0]
        expectedOutput = os.path.join(outputBaseDir, songName)
        
        if os.path.isdir(expectedOutput):
            print(f'✓ Already separated: {filename}')
            continue
        
        input_file_path = os.path.abspath(os.path.join(wavFolderPath, filename))
        output_dir = os.path.abspath(outputBaseDir)
        
        print(f'⏳ Separating: {filename}...')
        
        # Call subprocess with input file and output dir arguments
        subprocess.run([venv_python, script_path, input_file_path, output_dir], check=True)

if __name__ == "__main__":
    separate_all()
