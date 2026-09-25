Set-Location 'C:\Users\raosa\OneDrive\Documents\poker'
$env:KUHN_MODE = 'nash'
python -u enum6.py silent 8 silentX > log_enum6_silentX.txt 2>&1
python -u symleaf.py silentX 8 - 0 300 600 > log_symleaf_silentX.txt 2>&1
python -u control_symleaf.py silentX > log_control_symleaf_silentX.txt 2>&1
