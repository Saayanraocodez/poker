# Full re-derivation under ivl's DIRECTED ROUNDING (2026-09-20).  Run from the poker folder:
#     powershell -NoProfile -ExecutionPolicy Bypass -File rerunR.ps1
# Every file name carries the suffix R (KUHN_SUFFIX=R), so nothing from the
# 2026-09-19 run is touched or resumed from:
#   branches_alive_nashR.txt / branches_aliveR.txt      (root81, already written)
#   enum6_pat_b_*NR.npy, symleaf_b_*NR.npz, runbet6_summary_nashR.txt, log_runbet6_nashR.txt
#   enum6_pat_b_*R.npy,  symleaf_b_*R.npz,  runbet6_summaryR.txt,      log_runbet6R.txt
# The two drivers run side by side (28 cores): nash 18 workers, seq 8 workers.
Set-Location $PSScriptRoot
if (-not (Get-CimInstance Win32_Process -Filter "name like 'python%'" | Where-Object { $_.CommandLine -like '*keepawake.py*' })) {
    Start-Process -FilePath python -ArgumentList "-u","keepawake.py" -RedirectStandardOutput "log_keepawake6.txt" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}
$env:KUHN_ENUM = "layered"
$env:KUHN_ORDER = "bet"
$env:KUHN_SUFFIX = "R"
$env:KUHN_MODE = "nash"
Start-Process -FilePath python -ArgumentList "-u","runbet6.py","18","300" -RedirectStandardOutput "log_runbet6_driver_nashR.txt" -RedirectStandardError "log_runbet6_driver_nashR_err.txt" -WindowStyle Hidden
Start-Sleep -Seconds 2
$env:KUHN_MODE = "seq"
Start-Process -FilePath python -ArgumentList "-u","runbet6.py","8","300" -RedirectStandardOutput "log_runbet6_driverR.txt" -RedirectStandardError "log_runbet6_driverR_err.txt" -WindowStyle Hidden
Write-Host "started nash (18 workers) and seq (8 workers) drivers with KUHN_SUFFIX=R; ledgers runbet6_summary_nashR.txt / runbet6_summaryR.txt; progress: python summarize6.py R"
