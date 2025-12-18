"""
Android后台服务入口
用于在Android系统中运行定时分析任务
"""
import os
import sys
import time
import datetime

# 添加项目目录到Python路径
if __name__ == '__main__':
    # 获取应用的私有存储目录
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    context = PythonActivity.mActivity
    
    # 设置工作目录
    files_dir = context.getFilesDir().getAbsolutePath()
    os.chdir(files_dir)
    
    print(f"[Android服务] 服务启动 - {datetime.datetime.now()}")
    print(f"[Android服务] 工作目录: {files_dir}")
    
    try:
        # 导入服务模块
        from service import get_service
        from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        service = get_service()
        
        print(f"[Android服务] 服务实例创建完成")
        
        # 启动服务循环
        service.start_service()
        
        print(f"[Android服务] 进入服务循环...")
        
        # 保持服务运行
        while True:
            time.sleep(60)
            print(f"[Android服务] 心跳检查 - {datetime.datetime.now()}")
            
            # 检查服务是否还在运行
            if not service.is_running:
                print(f"[Android服务] 服务已停止,退出")
                break
    
    except Exception as e:
        print(f"[Android服务] 服务出错: {e}")
        import traceback
        traceback.print_exc()
