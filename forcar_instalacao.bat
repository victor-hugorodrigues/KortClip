@echo off
echo 1. Tentando consertar o instalador do Python (pip)...
"C:\Users\Victor\Documents\ViralCutter-main\.venv\Scripts\python.exe" -m ensurepip --upgrade

echo.
echo 2. Instalando o Gemini e outras IAs...
"C:\Users\Victor\Documents\ViralCutter-main\.venv\Scripts\python.exe" -m pip install google-generativeai transformers torchaudio

echo.
echo 3. Finalizado! Verifique se deu algum erro vermelho acima.
pause