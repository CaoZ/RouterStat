:: 使用 nssm 注册为 Windows 服务

:: 如果 nssm 的目录在 path 里就不用这句话了
cd C:\Soft\nssm-2.24\win64

set serviceName="RouterStat"
:: python 目录
set pathonExe="C:\Dev\Envs\router-stat-env\Scripts\python.exe"
:: 项目路径
set executePath="C:\Dev\Code\RouterStat\app"
set logPath="C:\Dev\Code\RouterStat\service.log"
:: 脚本以及脚本的参数
set executeScript="main.py"
:: 注册服务
nssm install %serviceName% %pathonExe% %executeScript%
nssm set %serviceName% Application %pathonExe%
nssm set %serviceName% AppDirectory %executePath%
nssm set %serviceName% AppParameters %executeScript%
nssm set %serviceName% AppStderr %logPath%
nssm set %serviceName% AppRotateSeconds 86400
:: 启动服务
nssm start %serviceName%
pause
