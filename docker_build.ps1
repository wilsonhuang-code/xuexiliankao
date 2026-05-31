# docker_build.ps1 - 用 Docker 构建 APK（避免 GitHub Actions 的 SDK 路径问题）

Write-Host "=== 学练考 APP - Docker 本地构建 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否安装
try {
    docker --version | Out-Null
    Write-Host "[OK] Docker 已安装" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "下载地址: <ADDRESS_REMOVED>
    exit 1
}

$projectDir = "C:\Users\Administrator\Desktop\学练考"
Set-Location $projectDir

Write-Host ""
Write-Host "步骤1: 拉取 kivy/buildozer 镜像..." -ForegroundColor Yellow
docker pull kivy/buildozer:latest

Write-Host ""
Write-Host "步骤2: 启动 Docker 容器构建 APK..." -ForegroundColor Yellow
Write-Host "（首次构建需要下载 SDK/NDK，约 10-20 分钟）"
Write-Host ""

docker run --rm `
  -v "${projectDir}:/home/user/hostcwd" `
  -w /home/user/hostcwd `
  kivy/buildozer:latest `
  buildozer android debug 2>&1 | Tee-Object -FilePath buildozer_log.txt

Write-Host ""
Write-Host "=== 构建完成 ===" -ForegroundColor Cyan

# 检查 APK 是否生成
$apkPath = "bin\*.apk"
if (Test-Path $apkPath) {
    Write-Host "[SUCCESS] APK 已生成！" -ForegroundColor Green
    Get-ChildItem bin\*.apk | ForEach-Object {
        Write-Host "  文件: $($_.FullName)" -ForegroundColor Green
        Write-Host "  大小: $([math]::Round($_.Length/1MB, 2)) MB" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "APK 路径: $projectDir\bin\" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] APK 未生成，请查看 buildozer_log.txt" -ForegroundColor Red
    Write-Host "最后 50 行日志：" -ForegroundColor Yellow
    Get-Content buildozer_log.txt -Tail 50
}
