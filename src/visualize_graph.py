"""
LangGraph 工作流可视化工具

此脚本生成差旅报销智能体工作流的可视化图表。
"""

import os
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.font_manager import FontProperties

def create_workflow_graph():
    """创建并显示工作流图"""
    # 创建有向图
    G = nx.DiGraph()
    
    # 添加节点
    nodes = [
        "意图分析\n(IntentAnalysisNode)",
        "任务规划\n(PlanningNode)",
        "执行\n(DecisionNode)",
        "工具执行\n(ToolDecisionNode)",
        "结束\n(END)"
    ]
    
    for node in nodes:
        G.add_node(node)
    
    # 添加边和标签
    edges = [
        ("意图分析\n(IntentAnalysisNode)", "任务规划\n(PlanningNode)", "无工具调用"),
        ("意图分析\n(IntentAnalysisNode)", "工具执行\n(ToolDecisionNode)", "有工具调用"),
        ("工具执行\n(ToolDecisionNode)", "任务规划\n(PlanningNode)", "需继续规划"),
        ("工具执行\n(ToolDecisionNode)", "结束\n(END)", "有最终输出"),
        ("任务规划\n(PlanningNode)", "执行\n(DecisionNode)", ""),
        ("执行\n(DecisionNode)", "结束\n(END)", "")
    ]
    
    for src, dst, label in edges:
        G.add_edge(src, dst, label=label)
    
    # 设置布局
    pos = {
        "意图分析\n(IntentAnalysisNode)": (0, 0),
        "任务规划\n(PlanningNode)": (0, -2),
        "执行\n(DecisionNode)": (0, -4),
        "工具执行\n(ToolDecisionNode)": (3, -1),
        "结束\n(END)": (1.5, -6)
    }
    
    # 绘制图形
    plt.figure(figsize=(12, 10))
    
    # 设置中文字体（兼容Windows和macOS）
    try:
        if os.name == 'nt':  # Windows系统
            font_path = r"C:\Windows\Fonts\SimHei.ttf"
        else:  # macOS系统
            font_path = "/System/Library/Fonts/Supplemental/Songti.ttc"
        
        if os.path.exists(font_path):
            font = FontProperties(fname=font_path)
        else:
            font = None
    except:
        font = None
    
    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='lightblue', alpha=0.8)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, width=1.5, arrowsize=20, alpha=0.7, 
                          edge_color='gray', connectionstyle='arc3,rad=0.1')
    
    # 绘制节点标签
    if font:
        nx.draw_networkx_labels(G, pos, font_family=font.get_name(), font_size=10)
    else:
        nx.draw_networkx_labels(G, pos, font_size=10)
    
    # 绘制边标签
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True) if d['label']}
    if font:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                    font_family=font.get_name(), font_size=9)
    else:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)
    
    plt.title('差旅报销智能体工作流', fontsize=15, fontproperties=font if font else None)
    plt.axis('off')
    
    # 保存图片
    plt.savefig('workflow_graph.png', dpi=200, bbox_inches='tight')
    
    # 显示图形
    plt.show()
    
    print("工作流图已生成并保存为 workflow_graph.png")

if __name__ == "__main__":
    try:
        import matplotlib
        import networkx
        create_workflow_graph()
    except ImportError as e:
        print(f"请先安装所需库: {e}")
        print("使用命令: pip install matplotlib networkx") 