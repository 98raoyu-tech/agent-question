"""
简化应用入口

导入并运行api/main.py中创建的app。
"""

import sys
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_workflow_os.api.main import main

if __name__ == "__main__":
    main()
