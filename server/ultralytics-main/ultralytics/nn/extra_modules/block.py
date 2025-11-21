# 兼容旧权重中的自定义层，把它们映射到官方最接近的基础模块。
# 注意：这是“兼容垫片”，非真实实现；精度可能下降。

import importlib
import torch
import torch.nn as nn
import torch.nn.functional as F

def _get(name, fallbacks=()):
    # 从官方模块里取可用的近似类
    for n in (name, *fallbacks):
        try:
            return getattr(importlib.import_module("ultralytics.nn.modules.block"), n)
        except Exception:
            pass
    # 实在找不到就给个最小占位
    import torch.nn as nn
    class _Dummy(nn.Module):
        def __init__(self, *a, **k): super().__init__()
        def forward(self, x): return x
    _Dummy.__name__ = "Dummy"
    return _Dummy

_Bottleneck = _get("Bottleneck", ("C3",))
_C3        = _get("C3", ())
_C2f       = _get("C2f", ("C3",))
_C3k2      = _get("C3k2", ("C3",))
_SPPF      = _get("SPPF", ())
_Conv      = _get("Conv", ())
_DWConv    = _get("DWConv", ("Conv",))
_RepC3     = _get("RepC3", ("C3",))
_C3Ghost   = _get("C3Ghost", ("C3",))
_C3k2 = _get("C3k2", ("C3",))

class SCConv(nn.Module):
    """兼容版 SCConv：通道自动对齐，防止残差维度不一致"""
    def __init__(self, in_channels, out_channels, stride=1, padding=1, dilation=1, groups=1, bias=False, norm_layer=nn.BatchNorm2d, activation=nn.SiLU):
        super().__init__()
        self.k2 = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, stride, padding, dilation, groups=in_channels, bias=bias),
            norm_layer(in_channels)
        )
        self.k3 = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 1, bias=bias),
            norm_layer(in_channels)
        )
        self.k4 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1, bias=bias),
            norm_layer(out_channels)
        )
        self.align = None
        if in_channels != out_channels:
            self.align = nn.Conv2d(in_channels, out_channels, 1, bias=False)
        self.act = activation()

    def forward(self, x):
        identity = x
        out = torch.sigmoid(self.k2(x)) * self.k3(x)
        out = self.k4(out)
        if self.align is not None:
            identity = self.align(identity)
        return self.act(out + identity)


# 这里把你可能遇到的自定义名映射到官方基类
_MAP = {
    "Bottleneck_MLCA": _Bottleneck,
    "C3k2_MLCA":       _C3k2,
    "C3_MLCA":         _C3,
    "C2f_MLCA":        _C2f,
    "SPPF_MLCA":       _SPPF,
    "Conv_MLCA":       _Conv,
    "DWConv_MLCA":     _DWConv,
    "RepC3_MLCA":      _RepC3,
    "C3Ghost_MLCA":    _C3Ghost,

    # 你当前报错的这个：
    "C3k2_SCConv":     _C3k2,   # 没有 SCConv 实现时退回 C3k2
    "C3k_SCConv":      _C3,
    "Bottleneck_SCConv":  _Bottleneck,
    "SCConv": SCConv,
}

def _mk(name, base_cls):
    class _Shim(base_cls):
        """Compatibility shim for '{}' -> {}""".format(name, base_cls.__name__)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
    _Shim.__name__ = name
    return _Shim

__all__ = []
for _name, _base in _MAP.items():
    globals()[_name] = _mk(_name, _base)
    __all__.append(_name)
