Wait-Process -Id 4788 -ErrorAction SilentlyContinue
Set-Location 'C:\Users\raosa\OneDrive\Documents\poker'
Add-Content log_chain_nash.txt "seq driver exited at $(Get-Date)"
$env:KUHN_MODE = 'nash'
# silent branch again under the value-margin contractor (bnb6 fix of 2026-09-16 18:20)
Start-Process -FilePath python -ArgumentList '-u','enum6.py','silent','16','silentN2' -RedirectStandardOutput 'log_enum6_silentN2.txt' -RedirectStandardError 'log_enum6_silentN2_err.txt' -WindowStyle Hidden -Wait
Start-Process -FilePath python -ArgumentList '-u','symleaf.py','silentN2','16','-','0','300','600' -RedirectStandardOutput 'log_symleaf_silentN2.txt' -RedirectStandardError 'log_symleaf_silentN2_err.txt' -WindowStyle Hidden -Wait
Start-Process -FilePath python -ArgumentList '-u','control_symleaf.py','silentN2' -RedirectStandardOutput 'log_control_symleaf_silentN2.txt' -RedirectStandardError 'log_control_symleaf_silentN2_err.txt' -WindowStyle Hidden -Wait
Add-Content log_chain_nash.txt "silentN2 done at $(Get-Date)"
Start-Process -FilePath python -ArgumentList '-u','runbet6.py','16','300' -RedirectStandardOutput 'log_runbet6_driver_nash.txt' -RedirectStandardError 'log_runbet6_driver_nash_err.txt' -WindowStyle Hidden -Wait
Add-Content log_chain_nash.txt "nash driver exited at $(Get-Date)"
