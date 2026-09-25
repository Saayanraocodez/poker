# Restart everything after a reboot (2026-09-18).  Run from the poker folder:
#     powershell -NoProfile -ExecutionPolicy Bypass -File restart.ps1
# 1. keep the box awake (it idle-sleeps after 60 min otherwise)
# 2. the Nash-mode betting run: skips every branch already in
#    runbet6_summary_nash.txt, resumes the interrupted branch's exact stage
#    from its checkpoint (symleaf_b_M_M_M_1N.npz, ~600k of 737k leaves done),
#    then continues with the 60 remaining branches.
Set-Location $PSScriptRoot
Start-Process -FilePath python -ArgumentList "-u","keepawake.py" -RedirectStandardOutput "log_keepawake5.txt" -WindowStyle Hidden
Start-Sleep -Seconds 3
$env:KUHN_MODE = "nash"
$env:KUHN_ENUM = "layered"
$env:KUHN_ORDER = "bet"
Start-Process -FilePath python -ArgumentList "-u","runbet6.py","16","300" -RedirectStandardOutput "log_runbet6_driver_nash2.txt" -RedirectStandardError "log_runbet6_driver_nash2_err.txt" -WindowStyle Hidden
Write-Host "started keepawake.py and KUHN_MODE=nash runbet6.py 16 300; ledger: runbet6_summary_nash.txt; progress: python summarize6.py"
