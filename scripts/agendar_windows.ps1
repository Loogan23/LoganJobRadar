# Script para registrar o JobRadar no Agendador de Tarefas do Windows
# Executa silenciosamente a cada 3 horas sem abrir janelas no terminal.

$TaskName = "JobRadar_AutoScan"
$WorkingDirectory = "C:\Users\levie\OneDrive\Desktop\JobRadar"

# Localizar o executável pythonw.exe (versão silenciosa sem janela)
$PythonPath = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if ($PythonPath) {
    $PythonW = $PythonPath -replace "python\.exe", "pythonw.exe"
} else {
    $PythonW = "$env:LOCALAPPDATA\Programs\Python\Python314\pythonw.exe"
}

Write-Host "Configurando agendamento automático do JobRadar..." -ForegroundColor Cyan

# Ação: Executar 'pythonw.exe main.py run'
$Action = New-ScheduledTaskAction -Execute $PythonW -Argument "main.py run" -WorkingDirectory $WorkingDirectory

# Gatilho: Repete a cada 3 horas durante o ano
$Trigger = New-ScheduledTaskTrigger -Once -At "00:00" -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration (New-TimeSpan -Days 365)

# Configurações adicionais de energia e execução
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Varredura automática e envio de vagas do JobRadar para o Telegram" -User $env:USERNAME
    
    Write-Host "`n✅ Tarefa '$TaskName' agendada com sucesso no Windows!" -ForegroundColor Green
    Write-Host "O robô executará em segundo plano (invisível) a cada 3 horas e enviará as novas vagas para o seu Telegram."
    Write-Host "Para remover o agendamento no futuro, execute: .\scripts\remover_agendamento.ps1"
} catch {
    Write-Host "`n❌ Erro ao registrar tarefa: $_" -ForegroundColor Red
}
