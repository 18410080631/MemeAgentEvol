# graph.py
from langgraph.graph import StateGraph, END
from state import AgentState
from agents import (
    scorer_agent, evaluator_agent, error_summarizer_agent, 
    prompt_improver_agent, error_scorer_agent, error_evaluator_agent,
    increment_iteration, extract_pdf_agent
)
from config import MAX_ITERATIONS, THRESHOLD, error_focus_threshold

workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("extract", extract_pdf_agent)
workflow.add_node("scorer", scorer_agent)
workflow.add_node("evaluator", evaluator_agent)
workflow.add_node("summarizer", error_summarizer_agent)
workflow.add_node("improver", prompt_improver_agent)
workflow.add_node("error_scorer", error_scorer_agent)
workflow.add_node("error_evaluator", error_evaluator_agent)
workflow.add_node("increment", increment_iteration)

# 设置入口
workflow.set_entry_point("extract")

# 主要流程
workflow.add_edge("extract", "scorer")
workflow.add_edge("scorer", "evaluator")

# 首次评估后的路由
def route_after_evaluator(state):
    if state.get("phase") == "end":
        return "end"
    elif state.get("phase") == "error_focus":
        return "summarizer"
    else:
        return "end"

workflow.add_conditional_edges(
    "evaluator",
    route_after_evaluator,
    {"summarizer": "summarizer", "end": END}
)

# 错误聚焦循环
workflow.add_edge("summarizer", "improver")
workflow.add_edge("improver", "increment")
workflow.add_edge("increment", "error_scorer")
workflow.add_edge("error_scorer", "error_evaluator")

# 错误评估后的路由
def route_after_error_eval(state):
    iteration = state.get("iteration", 0)
    phase = state.get("phase", "error_focus")
    
    if iteration >= MAX_ITERATIONS:
        return 'end'
    elif phase == "global_verify":
        return "scorer"
    elif phase == "error_focus":
        return "summarizer"
    else:
        return 'end'

workflow.add_conditional_edges(
    "error_evaluator",
    route_after_error_eval,
    {
        "summarizer": "summarizer",
        "scorer": "scorer",
        "end": END
    }
)

# 全局验证后回到evaluator
workflow.add_edge("scorer", "evaluator")

# 编译工作流
app = workflow.compile()