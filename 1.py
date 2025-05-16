if score >= max(60, target):
    return "测试通过，系统可用"
suggestion = '系统综合能力低于基线\n'
if U_GPU >= U_GPU_base + tolerance or M_peak >= M_peak_base + tolerance:
    suggestion += "GPU占用过高，建议升级GPU硬件"
if AVPT >= AVPT_base + tolerance:
    suggestion += "平均视觉处理时间高于基线，建议更换模型视觉编码器"
if CMAT >= CMAT_base + tolerance:
    suggestion += "跨模态对齐耗时高于基线，建议提高模型跨模态交互与特征融合的计算效率"
if ATGT >= ATGT_base + tolerance:
    suggestion += "平均文本生成时间高于基线，建议更换或改进模型文本解码器"
if E_query >= E_query_base + tolerance:
    suggestion += "系统平均功耗高于基线"
return suggestion

