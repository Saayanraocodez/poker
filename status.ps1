# What is actually running on this project, and how far along.
#
# Get-Process python returns NOTHING on this machine -- the Windows Store
# interpreter is named python3.13.  Every liveness check written as
# `Get-Process python` is a silent false negative, which is how five duplicate
# runs once ended up stacked on 28 cores at the same time.  Match on the
# command line instead of guessing the executable name.
#
#   powershell -File status.ps1

$now = Get-Date
$procs = Get-CimInstance Win32_Process -Filter "name like 'python%'"
$tops = $procs | Where-Object { $_.CommandLine -notmatch 'from multiprocessing' }

"=== top-level runs: $(@($tops).Count)   (worker procs: $(@($procs).Count - @($tops).Count))"
$tops | ForEach-Object {
    $c = $_.CommandLine
    $n = if ($c -match '([a-z0-9_]+\.py)') { $matches[1] } else { '?' }
    $a = if ($c -match '\.py"?\s+(.{0,50})') { $matches[1].Trim() } else { '' }
    [PSCustomObject]@{
        PID    = $_.ProcessId
        Script = $n
        Args   = $a
        Hours  = [math]::Round(($now - $_.CreationDate).TotalHours, 1)
    }
} | Sort-Object Hours -Descending | Format-Table -AutoSize

$os = Get-CimInstance Win32_OperatingSystem
# Win32_Process exposes WorkingSetSize, not WorkingSet64 (that is Get-Process).
$rss = [math]::Round((($procs | Measure-Object WorkingSetSize -Sum).Sum) / 1GB, 2)
"cores $([Environment]::ProcessorCount)   python RSS ${rss}GB   free RAM $([math]::Round($os.FreePhysicalMemory/1MB,2))GB"

# Duplicate detection: the same script+data running twice is almost always an
# accident, and it is invisible in any single log.
$dupes = $tops | Group-Object { ($_.CommandLine -replace '.*?([a-z0-9_]+\.py)', '$1').Substring(0, [Math]::Min(60, ($_.CommandLine -replace '.*?([a-z0-9_]+\.py)', '$1').Length)) } |
         Where-Object Count -gt 1
if ($dupes) {
    ""
    "*** DUPLICATE RUNS DETECTED -- these are competing for the same cores:"
    $dupes | ForEach-Object { "    x$($_.Count)  $($_.Name)" }
}

# Checkpoint progress for any pipe2 run (pipe.py has no checkpoint: it saves
# only after the whole pool finishes, so a kill loses everything).
""
"=== pipe2 checkpoints"
Get-ChildItem ck_*.npz -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '*.tmp.npz' } | ForEach-Object {
    $tag = $_.BaseName -replace '^ck_', ''
    $py = "import numpy as np;z=np.load(r'$($_.FullName)');" +
          "print('%-8s %4d jobs  %8d screened  %8d infeasible (%.1f%%)  %.1fh'%" +
          "('$tag',len(z['done']),int(z['tot']),int(z['pv'])," +
          "100*int(z['pv'])/max(int(z['tot']),1),float(z['elapsed'])/3600))"
    & python -c $py
}
