<#
.SYNOPSIS
    Compiles the research paper LaTeX source into a PDF.
.DESCRIPTION
    Runs two passes of pdflatex to resolve references and citations,
    then cleans up intermediate files.
.PARAMETER Target
    "copy"     - Compiles "Revised Paper (Final) - Copy.tex" (default)
    "original" - Compiles "Revised Paper (Final).tex"
    "all"      - Compiles both
#>
param(
    [string]$Target = "copy"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

function Invoke-PaperBuild {
    param([string]$JobName)

    $TexFile = "$JobName.tex"
    $LogFile = "$JobName.build.log"

    Write-Host "Compiling $TexFile..." -ForegroundColor Cyan

    for ($pass = 1; $pass -le 2; $pass++) {
        Write-Host "  Pass $pass of 2..." -ForegroundColor DarkGray
        $proc = Start-Process -FilePath "pdflatex" `
            -ArgumentList "-interaction=nonstopmode", "-halt-on-error", "`"$TexFile`"" `
            -NoNewWindow -PassThru -Wait -RedirectStandardOutput $LogFile
        if ($proc.ExitCode -ne 0) {
            Write-Warning "Compile failed on pass $pass. Inspect $LogFile for details."
            Get-Content $LogFile -Tail 30
            return
        }
    }

    # Clean intermediate auxiliary files
    foreach ($ext in @("aux", "log", "out", "toc", "build.log")) {
        $tmp = "$JobName.$ext"
        if (Test-Path $tmp) { Remove-Item -Force $tmp }
    }

    Write-Host "Successfully generated '$JobName.pdf'" -ForegroundColor Green
}

if ($Target -eq "copy" -or $Target -eq "all") {
    Invoke-PaperBuild -JobName "Revised Paper (Final) - Copy"
}
if ($Target -eq "original" -or $Target -eq "all") {
    Invoke-PaperBuild -JobName "Revised Paper (Final)"
}
