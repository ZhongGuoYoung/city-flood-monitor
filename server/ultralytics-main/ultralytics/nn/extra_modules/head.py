# ultralytics\nn\extra_modules\head.py
from ultralytics.nn.modules.head import Detect as _Detect

# 替代自定义SCConv版本头部
class Head_SCConv(_Detect):
    pass

class Detect_SCConv(_Detect):
    pass

# 新增：兼容 DetectAux
class DetectAux(_Detect):
    pass

# 默认映射
Detect = _Detect
Head = _Detect
