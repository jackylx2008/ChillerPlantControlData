param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

# 用途：
# - 扫描 output/cleaned 目录下的 cleaned_*.csv 文件
# - 从每个 cleaned 文件名中提取中文关键词，作为图表生成关键字
# - 调用 generate_charts.py，为指定月份批量生成月度图表
#
# 用法：
# - 在项目根目录执行：.\generate_monthly_charts.ps1
# - 指定月份执行：.\generate_monthly_charts.ps1 --2025.07
# - 也兼容以下格式：2025.07、2025-07、--2025-07

$ErrorActionPreference = "Stop"

function Resolve-ChartKeyword {
    param(
        [string]$Keyword
    )

    switch ($Keyword) {
        "总供水温度" { return "总供回水温度" }
        "总回水温度" { return "总供回水温度" }
        "总供水压力" { return "总供回水压力" }
        "总回水压力" { return "总供回水压力" }
        default { return $Keyword }
    }
}

function Resolve-TargetMonth {
    param(
        [string[]]$RawArgs
    )

    if (-not $RawArgs -or $RawArgs.Count -eq 0) {
        return (Get-Date -Format "yyyy-MM")
    }

    foreach ($rawArg in $RawArgs) {
        if ([string]::IsNullOrWhiteSpace($rawArg)) {
            continue
        }

        $normalized = $rawArg.Trim()
        if ($normalized.StartsWith("--")) {
            $normalized = $normalized.Substring(2)
        }

        if ($normalized -match '^(?<year>\d{4})[.-](?<month>\d{2})$') {
            $monthNumber = [int]$Matches["month"]
            if ($monthNumber -lt 1 -or $monthNumber -gt 12) {
                throw "月份参数无效：$rawArg。月份必须在 01 到 12 之间。"
            }

            return ("{0}-{1}" -f $Matches["year"], $Matches["month"])
        }
    }

    throw "未识别的月份参数。请使用 --2025.07、2025.07、2025-07 或 --2025-07。"
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonEntry = Join-Path $ProjectRoot "src\chiller_plant_control_data\entries\generate_charts.py"
$CleanedDir = Join-Path $ProjectRoot "output\cleaned"
$TargetMonth = Resolve-TargetMonth -RawArgs $ArgsList

if (-not (Test-Path -LiteralPath $PythonEntry)) {
    throw "未找到图表入口脚本：$PythonEntry"
}

if (-not (Test-Path -LiteralPath $CleanedDir)) {
    throw "未找到清洗后数据目录：$CleanedDir"
}

$files = Get-ChildItem -LiteralPath $CleanedDir -Filter "cleaned_*.csv" | Sort-Object Name

if (-not $files) {
    Write-Warning "在 $CleanedDir 下没有找到 cleaned_*.csv 文件。"
    exit 0
}

$processedKeywords = [System.Collections.Generic.HashSet[string]]::new()

foreach ($file in $files) {
    $matches = [regex]::Matches($file.BaseName, "[\p{IsCJKUnifiedIdeographs}]+")
    if ($matches.Count -eq 0) {
        Write-Warning "跳过未包含中文关键词的文件：$($file.Name)"
        continue
    }

    $keyword = ($matches | ForEach-Object { $_.Value }) -join "_"
    $keyword = Resolve-ChartKeyword -Keyword $keyword
    if (-not $processedKeywords.Add($keyword)) {
        Write-Host "跳过已处理的组合图关键字：" $keyword
        continue
    }

    Write-Host "正在生成 $TargetMonth 月度图表：" $keyword

    python $PythonEntry `
        --keyword $keyword `
        --period-type month `
        --target-month $TargetMonth `
        --cleaned-dir $CleanedDir
}

Write-Host "$TargetMonth 的月度图表已全部生成。"
