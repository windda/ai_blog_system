
class classproperty:
    
    """自定义描述符实现类属性"""
    
    def __init__(self, method):
        self.method = method
        
    def __get__(self, instance, cls):
        return self.method(cls)