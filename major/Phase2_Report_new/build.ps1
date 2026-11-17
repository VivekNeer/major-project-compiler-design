<#
.SYNOPSIS
    Builds the team report and individual reports on Windows with pdflatex.
.DESCRIPTION
    Usage:
        .\build.ps1             # Build team copy + 4 individual copies -> out\
        .\build.ps1 team        # Team copy only
        .\build.ps1 D           # Vivek Neeralagi's individual copy (A..D)
#>
param(
    [string]$What = "all"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$OutDir = Join-Path $ScriptDir "out"
if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

$Students = @{
    "A" = "Aniket_De"
    "B" = "Kushal_S_M"
    "C" = "Manas_S"
    "D" = "Vivek_Neeralagi"
}

function Invoke-LatexCompile {
    param(
        [string]$JobName,
        [string]$ExtraPre = ""
    )

    Write-Host "Compiling $JobName..." -ForegroundColor Cyan
    $LogFile = Join-Path $OutDir "$JobName.log"
    $TexInput = if ($ExtraPre) { "$ExtraPre\input{report.tex}" } else { "report.tex" }

    for ($pass = 1; $pass -le 3; $pass++) {
        $proc = Start-Process -FilePath "pdflatex" `
            -ArgumentList "-interaction=nonstopmode", "-halt-on-error", "-jobname=$JobName", "`"$TexInput`"" `
            -NoNewWindow -PassThru -Wait -RedirectStandardOutput $LogFile
        if ($proc.ExitCode -ne 0) {
            Write-Warning "Compile failed on pass $pass (ExitCode: $($proc.ExitCode)). Check $LogFile"
            Get-Content $LogFile -Tail 30
            return
        }
    }

    $PdfOut = "$JobName.pdf"
    if (Test-Path $PdfOut) {
        Move-Item -Force $PdfOut (Join-Path $OutDir $PdfOut)
    }

    # Clean intermediate auxiliary files
    foreach ($ext in @("aux", "lof", "lot", "out", "toc", "log")) {
        $tmp = "$JobName.$ext"
        if (Test-Path $tmp) { Remove-Item -Force $tmp }
    }

    Write-Host "Successfully built out\$JobName.pdf" -ForegroundColor Green
}

if ($What -eq "all" -or $What -eq "team") {
    Invoke-LatexCompile -JobName "report_team"
}

foreach ($key in @("A", "B", "C", "D")) {
    if ($What -eq "all" -or $What -eq $key) {
        $studentName = $Students[$key]
        Invoke-LatexCompile -JobName "report_$studentName" -ExtraPre "\def\Individual{$key}"
    }
}
