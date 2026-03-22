import logging
import os
from datetime import datetime

class LoggingConfig:
    """日志配置类"""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO"):
        """设置日志配置"""
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"agent_{timestamp}.log")
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 配置根日志器
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                # 控制台日志
                logging.StreamHandler(),
                # 文件日志
                logging.FileHandler(log_file, encoding="utf-8")
            ]
        )
        
        # 禁用某些第三方库的日志
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        logger = logging.getLogger(__name__)
        logger.info(f"日志配置完成，日志文件：{log_file}")
        
        return logger
