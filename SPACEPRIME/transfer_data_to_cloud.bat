@ECHO OFF

:: Replace with the actual name of your Anaconda environment
SET CONDA_ENV=psypy

:: Replace with the actual path to your project directory
SET PROJECT_DIR=C:\PycharmProjects\psychopy-experiments\SPACEPRIME

:: Replace with the actual name of your Python script
SET PYTHON_SCRIPT=transfer_data_to_cloud.py

:: Activate the Anaconda environment
CALL conda activate %CONDA_ENV%

:: Change to the project directory
CD /D %PROJECT_DIR%

:: Execute the Python script
python %PYTHON_SCRIPT%

:: Deactivate the environment if you want (optional)
CALL conda deactivate