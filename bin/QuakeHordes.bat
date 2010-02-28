set args=
for %%a in (%*) do set args=!args! %%a
%PY_INSTALL_PATH%\python.exe %QUAKEHORDES_BIN%\QuakeHordes.py %args% 