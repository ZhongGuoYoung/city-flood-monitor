# D:\ultralytics-main\ultralytics\nn\extra_modules\attention.py
# 说明：这是兼容旧权重的“占位注意力”实现，全部为恒等（Identity）。
# 目的：让旧的 *.pt 能成功反序列化、跑通推理。可能会有精度下降。

import torch.nn as nn

class _IdentityAttn(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.id = nn.Identity()
    def forward(self, x):
        return self.id(x)

# 常见的自定义注意力名，全部映射为恒等占位
class MLCA(_IdentityAttn):       pass
class SE(_IdentityAttn):         pass  # Squeeze-Excitation（占位）
class CBAM(_IdentityAttn):       pass  # Convolutional Block Attn Module（占位）
class ECA(_IdentityAttn):        pass  # Efficient Channel Attn（占位）
class SK(_IdentityAttn):         pass  # Selective Kernel（占位）
class CA(_IdentityAttn):         pass  # Coordinate Attn（占位）
class SCA(_IdentityAttn):        pass
class PSA(_IdentityAttn):        pass
class GAM(_IdentityAttn):        pass

__all__ = ["MLCA", "SE", "CBAM", "ECA", "SK", "CA", "SCA", "PSA", "GAM"]
class _Id(nn.Module):
    def __init__(self, *a, **k): super().__init__()
    def forward(self, x): return x

# 常见注意力名全部指向恒等层；若你有真实实现再替换
SE = CBAM = ECA = SK = CA = SCA = PSA = GAM = _Id