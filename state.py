# state.py
from typing import TypedDict, List, Dict, Optional, Annotated
from operator import add
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
class MemeSample(TypedDict):
    id: str
    meme_src: str
    meme_text: str
    meme_content: str
    ground_truth: str
    paper_pdf_path: str

class AgentState(TypedDict):
    # ====== 基础状态 ======
    error_iteration:int
    iteration: int
    phase: str  # 'global_eval', 'error_focus', 'global_verify', 'end'
    
    # 当前使用的prompt/code
    current_prompt: str
    current_code: str
    
    # 历史记录
    prompt_history: Annotated[List[dict], add]
    
    # 数据集
    dataset: List[MemeSample]
    paper_text: str
    paper_pdf_path: str
    
    # ====== 全局评估相关 ======
    # 注意：scorer_agent根据阶段返回不同的键
    # global_eval阶段返回 predictions
    # global_verify阶段返回 global_predictions
    predictions: Dict[str, dict]  # global_eval阶段的预测
    global_predictions: Dict[str, dict]  # global_verify阶段的预测
    
    # 全局评估结果
    global_errors: List[str]  # 全局错误样本ID
    global_accuracy: float
    best_global_accuracy: float
    best_global_prompt: str
    best_global_code: str
    converged: bool
    
    # ====== 错误聚焦相关 ======
    # 固定错误样本集（从全局评估中获得）
    fixed_error_dataset: List[MemeSample]
    error_predictions: Dict[str, dict]  # 错误样本子集的预测
    error_errors: List[str]  # 错误样本中仍然错误的ID
    error_accuracy: float
    best_error_accuracy: float
    best_error_prompt: str
    best_error_code: str
    error_summary:str
    pre1l0_summary:str
    pre0l1_summary:str
    # ====== 误判统计 ======
    # 使用list而不是set，避免合并问题
    pre1l0: List[str]  # 将无害判为有害的ID列表
    pre0l1: List[str]  # 将有害判为无害的ID列表

    pre1l0_memory:str
    pre0l1_memory:str


    #========机器学习 ======
    performance:str
    formula:str
    scaler_params:Dict
    intercept:float
    weights:List
    feature_importance:List
    #========error阶段机器学习=======
    error_performance:str
    error_formula:str
    error_scaler_params:Dict
    error_intercept:float
    error_weights:List

    error_feature_importance:List