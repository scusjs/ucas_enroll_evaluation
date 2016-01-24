# ucas_evaluate
中国科学院大学自动评教脚本
===
需要Python2.7环境，依赖Beautifulsoup和Requests，通过如下命令可安装

> pip install beautifulsoup4

> pip install requests

请在config填入你的用户名和密码

Fix 'system err'

Ubuntu系统下脚本可能会出现“no such course”的错误，即使填入的courseid是正确的，可以通过如下方法来修复：

  bash> sudo locale-gen en_US.UTF-8
  
  bash> export LC_ALL=en_US.UTF-8
  
  bash> python evaluate.py
  
  Bingo
