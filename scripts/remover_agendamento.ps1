# Script para remover o agendamento do JobRadar do Windows
schtasks /delete /tn "JobRadar_AutoScan" /f
Write-Host "Tarefa JobRadar_AutoScan removida com sucesso!" -ForegroundColor Green
