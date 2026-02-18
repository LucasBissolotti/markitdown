$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'streamlit' }
if ($procs) {
    foreach ($p in $procs) {
        Write-Output "Killing PID $($p.ProcessId) CommandLine: $($p.CommandLine)"
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Output "Failed to kill PID $($p.ProcessId): $_"
        }
    }
} else {
    Write-Output "No streamlit processes found"
}
