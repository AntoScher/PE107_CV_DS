"""
Logging configuration for the AI Resume Analyzer application.
"""
import logging
import sys
from typing import Optional
from datetime import datetime
import os

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(
    name: str = "resume_analyzer",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "resume_analyzer") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Performance monitoring decorator
def log_performance(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance (optional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                log.info(f"{func.__name__} executed successfully in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                log.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

# Error tracking decorator
def log_errors(logger: Optional[logging.Logger] = None, reraise: bool = True):
    """
    Decorator to log errors with context.
    
    Args:
        logger: Logger instance (optional)
        reraise: Whether to re-raise the exception
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                if reraise:
                    raise
        
        return wrapper
    return decorator

# Request logging decorator
def log_requests(logger: Optional[logging.Logger] = None):
    """
    Decorator to log HTTP requests and responses.
    
    Args:
        logger: Logger instance (optional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            
            # Log request
            if args and isinstance(args[0], str):
                url = args[0]
                log.info(f"Making request to: {url}")
            
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Log response
                if hasattr(result, 'status_code'):
                    log.info(f"Request completed: {result.status_code} in {execution_time:.2f}s")
                else:
                    log.info(f"Request completed successfully in {execution_time:.2f}s")
                
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                log.error(f"Request failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

# Initialize default logger
default_logger = setup_logger()
