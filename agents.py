# agents.py
from typing import Dict, Any, List
from tools import LLMTool,train_logistic_regression, extract_pdf_text, extract_code_from_markdown,code_fix,extract_dict_from_string,caculate_acc
from config import MODEL_NAME, TEMPERATURE, THRESHOLD, error_focus_threshold, MAX_ITERATIONS,DATASET_NAME,RECORD_PATH,USE_LMCL,USE_DMEE,dim_importance_threshold,HARM_text,FHM_text,MAMI_text
from tools import safe_append_markdown,save_model_minimal,PredictionSaver
import json_repair
import os
import random
from tqdm import tqdm
RECORD_PATH = f"{DATASET_NAME}/{RECORD_PATH}"
llm_tool = LLMTool(model_name=MODEL_NAME, temperature=TEMPERATURE)
prediction_saver = PredictionSaver(DATASET_NAME)
if DATASET_NAME == 'MAMI':
    THRESHOLD = 0.90
def extract_pdf_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """提取PDF文本"""
    # paper_text = extract_pdf_text(state["paper_pdf_path"])
    if DATASET_NAME == "FHM":
        paper_text = FHM_text
    elif DATASET_NAME == "MAMI":
        paper_text = MAMI_text
    else:
        paper_text = HARM_text
    safe_append_markdown(RECORD_PATH, f"## 论文文本提取:\n{paper_text}")
    return {"paper_text": paper_text}

def scorer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局打分agent"""
    current_code = state["current_code"]
    current_prompt = state["current_prompt"]
    dataset: List[Dict] = state["dataset"]
    pre1l0 = state.get('pre1l0', [])
    pre0l1 = state.get('pre0l1', [])
    predictions = {}
    iteration = state.get("iteration",0)
    pre1l0_memory = state.get('pre1l0_memory',[])
    pre0l1_memory = state.get('pre0l1_memory',[])
    data,feature_names = [],[]
    safe_append_markdown(RECORD_PATH, f"## 全局评估打分:\n")
    error_idxs = []
    for idx,sample in enumerate(tqdm(dataset)):
        system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
        user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
        id = sample['id']
        ground_truth = sample['ground_truth']
        ground_truth_label = [1] if ground_truth == "harmful" else [0]
        try:
            response = prediction_saver.get(iteration,id)
            if response == None:
                response = llm_tool.call_llm(
                    system_prompt=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                    meme_src=sample.get("meme_src", None),
                    max_tokens=2048
                )
                prediction_saver.save(round_id=iteration,meme_id=id,response=response)
            safe_append_markdown(RECORD_PATH, f"### 样本ID: {id}\n**打分结果:** {response}\n")
            scores = json_repair.loads(response)
            if len(scores)<3:
                error_idxs.append(idx)
                continue
        except Exception as e:
            error_idxs.append(idx)
            print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
            # print(f"原始响应: {response[:200]}...")
            continue  
        harmful_scores = scores["harmful_scores"] 
        harmless_scores = scores["harmless_scores"] 
        data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
        print(f"{id}: 当前打分：")
        print(f"  harmful_scores: {scores.get('harmful_scores', {})}")
        print(f"  harmless_scores: {scores.get('harmless_scores', {})}")
        print("-" * 50)
    feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
    res = train_logistic_regression(data=data,feature_names=feature_names)  
    performance = res["performance"]  
    formula = res["formula"]
    scaler_params = res["scaler_params"]
    intercept = res["intercept"]
    weights = res["weights"]
    feature_importance = res["feature_importance"]
    train_predictions = res["train_predictions"]

            
    safe_append_markdown(RECORD_PATH, f"## 全局评估结果\n**性能指标:** {performance}\n**逻辑回归公式:** {formula}\n**特征重要性:** {feature_importance}\n")
    p = 0
    for idx in range(len(dataset)):
        if idx not in error_idxs:
            sample = dataset[idx]
            label = train_predictions[p]
            p+=1
            ground_truth = sample['ground_truth']
            id = sample['id']
            # try:
            #     # namespace = {}
            #     # exec(current_code, {}, namespace)
            #     # label = namespace['classify_meme'](scores)

            # except Exception as e:
            #     print(f"代码执行出错 (ID={sample['id']}): {e}")
            #     # current_code = code_fix(current_code,str(scores),e)
            #     # namespace = {}
            #     # exec(current_code, {}, namespace)
            #     label = namespace['classify_meme'](scores)
            #     continue
            if label==1 and ground_truth == 'harmless':
                if id not in pre1l0:  # 避免重复
                    pre1l0.append(id)
            if label==0 and ground_truth == 'harmful':
                if id not in pre0l1:  # 避免重复
                    pre0l1.append(id)
            label_str = 'harmful' if label==1 else 'harmless'
            print(f"{id}: 当前预测与真实值：")
            print(f"  Predict: {label}")
            print(f"  GroundTruth: {ground_truth}")
            print("-" * 50)
            predictions[sample["id"]] = {'label': label_str, "scores": scores}
        
    # 根据当前阶段决定返回的键名
    current_phase = state.get("phase", "global_eval")
    if current_phase == "global_verify":
        return {
            "current_code":formula,
            "global_predictions": predictions,
            "pre1l0": pre1l0,
            "pre0l1": pre0l1,
            "performance":performance,
            "formula":formula,
            "scaler_params":scaler_params,
            "intercept":intercept,
            "weights":weights,
            "feature_importance":feature_importance,
            "iteration":iteration+1
        }
    else:
        return {
            "current_code":formula,
            "predictions": predictions,
            "pre1l0": pre1l0,
            "pre0l1": pre0l1,
            "performance":performance,
            "formula":formula,
            "scaler_params":scaler_params,
            "intercept":intercept,
            "weights":weights,
            "feature_importance":feature_importance,
            "iteration":iteration+1
        }

def evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局评估agent"""
    current_phase = state.get("phase", "global_eval")
    
    if current_phase == "global_eval":
        return _global_evaluator(state)
    elif current_phase == "global_verify":
        return _global_verify_evaluator(state)
    else:
        print(f"⚠️ 未知阶段: {current_phase}")
        return {"phase": "end"}

def _global_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """首次全局评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    predictions = state.get("predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    # 计算错误
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
    accuracy = (len(predictions) - len(errors)) / len(predictions) if predictions else 0.0
    performance = state.get("performance",{})
    accuracy,f1 = performance["accuracy"],performance["f1"]
    print(f"\n{'='*60}")
    print(f"首次全局评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"accuracy:{accuracy},f1:{f1}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新最佳全局模型
    best_global_accuracy = state.get("best_global_accuracy", 0.0)
    best_global_prompt = state.get("best_global_prompt", "")
    best_global_code = state.get("best_global_code", "")
    
    if accuracy >= best_global_accuracy:
        best_global_accuracy = accuracy
        best_global_prompt = state["current_prompt"]
        best_global_code = state["formula"]
        # 保存最佳模型
        output_dir = DATASET_NAME
        os.makedirs(output_dir, exist_ok=True)
        prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(best_global_prompt)
        save_model_minimal(state)
        safe_append_markdown(RECORD_PATH, f"## 首次全局评估结果\n**准确率:** {accuracy:.2%},f1:{f1}\n**错误样本数:** {len(errors)}\n**将无害模因误判为有害数量:** {len(pre1l0)}\n**将有害模因误判为无害数量:** {len(pre0l1)}\n")
        print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
    
    converged = accuracy >= THRESHOLD or len(errors) == 0
    
    if converged:
        print("🎉 首次评估即达到阈值，任务完成！")
        return {
            "global_predictions": predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": True,
            "phase": "end",
            "error_iteration": 0,  # 开始错误聚焦，初始化错误迭代
        }
    else:
        # 创建固定错误样本集
        fixed_error_dataset = [sample for sample in state["dataset"] if sample["id"] in errors]
        print(f"📊 创建错误样本集，包含 {len(fixed_error_dataset)} 个样本")
        
        return {
            "global_predictions": predictions,
            "error_predictions":error_predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": False,
            "phase": "error_focus",
            "fixed_error_dataset": fixed_error_dataset,
            "error_accuracy": 0.0,
            "best_error_prompt": state["current_prompt"],
            "best_error_code": state["current_code"],
            "error_iteration": 0,  # 开始错误聚焦，初始化错误迭代
        }

def _global_verify_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局验证评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    predictions = state.get("global_predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    iteration = state.get("iteration")
    # 计算错误
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
    accuracy = (len(predictions) - len(errors)) / len(predictions) if predictions else 0.0
    
    print(f"\n{'='*60}")
    print(f"全局验证评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"准确率: {accuracy:.2%}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新最佳全局模型
    best_global_accuracy = state.get("best_global_accuracy", 0.0)
    best_global_prompt = state.get("best_global_prompt", "")
    best_global_code = state.get("best_global_code", "")
    
    if accuracy >= best_global_accuracy:
        best_global_accuracy = accuracy
        best_global_prompt = state["current_prompt"]
        best_global_code = state["current_code"]
        # 保存最佳模型
        output_dir = DATASET_NAME
        os.makedirs(output_dir, exist_ok=True)
        prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(best_global_prompt)
        save_model_minimal(state)
        print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
    
    converged = accuracy >= THRESHOLD or len(errors) == 0
    
    if converged:
        print("🎉 全局验证通过，任务完成！")
        return {
            "global_predictions": predictions,
            "global_accuracy": accuracy,
            "converged": True,
            "phase": "end"
        }
    else:
        # 未收敛，准备新的错误集
        fixed_error_dataset = [sample for sample in state["dataset"] if sample["id"] in errors]
        print(f"📊 创建新的错误样本集，包含 {len(fixed_error_dataset)} 个样本")
        
        return {
            "global_predictions": predictions,
            "error_predictions":error_predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": False,
            "phase": "error_focus",
            "fixed_error_dataset": fixed_error_dataset,
            "error_accuracy": 0.0,
            "best_error_prompt": state["current_prompt"],
            "best_error_code": state["current_code"],
            "error_iteration": 0,  # 重置错误迭代，开始新一轮错误聚焦
        }

def error_scorer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本打分agent - 只使用固定的错误样本集"""
    current_code = state["current_code"]  
    current_prompt = state["current_prompt"]
    error_iteration = state.get("error_iteration",0)
    dataset: List[Dict] = state["fixed_error_dataset"]
    predictions = {}
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    iteration = state["iteration"]
    print(f"\n{'='*60}")
    print(f"开始错误样本集评估，样本数: {len(dataset)}")
    print(f"{'='*60}\n")
    safe_append_markdown(RECORD_PATH, f"## 错误样本集评估:\n样本数: {len(dataset)}\n")
    l = 0
    error_idx = []
    try:
        labels,data,h_n_data,feature_names = [],[],[],[]
        for idx,sample in enumerate(dataset):
            system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
            user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
            id = sample['id']
            ground_truth = sample['ground_truth']
            ground_truth_label = [1] if ground_truth == "harmful" else [0]
            response = prediction_saver.get(iteration,f"{iteration}_{error_iteration}_{id}")
            if response == None:
                response = llm_tool.call_llm(
                    system_prompt=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                    meme_src=sample.get("meme_src", None),
                    max_tokens=2048
                )
                prediction_saver.save(iteration,f"{iteration}_{error_iteration}_{id}",response)
            safe_append_markdown(RECORD_PATH, f"### 错误样本ID: {id}\n**打分结果:** {response}\n")
            try:
                scores = json_repair.loads(response)
            except Exception as e:
                print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
                print(f"原始响应: {response[:200]}...")
                continue
            harmful_scores = scores["harmful_scores"] 
            harmless_scores = scores["harmless_scores"] 
            if idx == 0:
                l = len(harmful_scores) + len(harmless_scores)
                data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
                labels.append(ground_truth)
                h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
            else:
                if len(harmful_scores) + len(harmless_scores) == l:
                    labels.append(ground_truth)
                    h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
                    data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
                else:
                    error_idx.append[idx]
            print(f"{id}: 错误样本集打分：")
            print(f"  harmful_scores: {scores.get('harmful_scores', {})}")
            print(f"  harmless_scores: {scores.get('harmless_scores', {})}")
            print("-" * 50)
        feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
        res = train_logistic_regression(data=data,feature_names=feature_names)  
        error_performance,train_predictions = caculate_acc(labels,h_n_data)
        error_formula = res["formula"]
        error_scaler_params = res["scaler_params"]
        error_intercept = res["intercept"]
        error_weights = res["weights"]
        error_feature_importance = res["feature_importance"]
        safe_append_markdown(RECORD_PATH, f"## 错误样本集评估结果\n**性能指标:** {error_performance}\n**逻辑回归公式:** {error_formula}\n**特征重要性:** {error_feature_importance}\n")
        p = 0
        for idx in range(len(dataset)):
            if idx not in error_idx:
                sample = dataset[idx]
                label = train_predictions[p]
                p+=1
                ground_truth = sample['ground_truth']
                id = sample['id']
                # try:
                #     namespace = {}
                #     exec(current_code, {}, namespace)
                #     classify_func = namespace.get('classify_meme')
                #     label = classify_func(scores)

                # except Exception as e:
                #     print(f"代码执行出错 (ID={sample['id']}): {e}")
                #     current_code = code_fix(current_code,str(scores),e)
                #     namespace = {}
                #     exec(current_code, {}, namespace)
                #     label = namespace['classify_meme'](scores)
                # if isinstance(label, str):
                #     label = label.lower()
                # else:
                #     label = "review"

                # 记录错误类型
                if label==1 and ground_truth == 'harmless':
                    if id not in pre1l0:  # 避免重复
                        pre1l0.append(id)
                if label==0 and ground_truth == 'harmful':
                    if id not in pre0l1:  # 避免重复
                        pre0l1.append(id)
                label_str = 'harmful' if label==1 else 'harmless'
                print(f"{id}: 预测结果：")
                print(f"  Predict: {label}")
                print(f"  GroundTruth: {ground_truth}")
                print("-" * 50)

                predictions[sample["id"]] = {'label': label_str, "scores": scores}                
    except Exception as e:
        print(f"⚠️ 模型调用异常: {e}")
    
    return {
        "error_predictions": predictions,
        "pre1l0": pre1l0,
        "pre0l1": pre0l1,
        "error_performance":error_performance if error_performance else None,
        "error_formula":error_formula if error_formula else None,
        "error_scaler_params": error_scaler_params if error_scaler_params else None,
        "error_intercept":error_intercept,
        "error_weights":error_weights,
        "error_feature_importance":error_feature_importance
    }
    # return {}

def error_evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本评估agent"""
    error_preds = state["error_predictions"]
    error_dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    # 计算错误子集的错误
    error_errors = [
        sid for sid, pred in error_preds.items()
        if pred['label'].lower() != error_dataset_map[sid]["ground_truth"].lower()
    ]
    
    error_performance = state["error_performance"]
    error_accuracy,f1 = error_performance["accuracy"],error_performance["f1"]
    print(f"\n{'='*60}")
    print(f"错误样本集评估结果:")
    print(f"错误样本总数: {len(error_preds)}")
    print(f"错误样本集准确率: {error_accuracy:.2%},f1：{f1}")
    print(f"仍然错误的样本数: {len(error_errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新错误子集最优模型
    best_error_accuracy = state.get("best_error_accuracy", 0.0)
    best_error_prompt = state.get("best_error_prompt", "")
    best_error_code = state.get("best_error_code", "")
    
    if error_accuracy >= best_error_accuracy:
        best_error_accuracy = error_accuracy
        best_error_prompt = state["current_prompt"]
        best_error_code = state["current_code"]
        print(f"✅ 更新错误样本集最佳模型，准确率: {error_accuracy:.2%}")
    else:
        print(f"⚠️ 错误样本集准确率未提升，当前: {error_accuracy:.2%}, 最佳: {best_error_accuracy:.2%}")
    
    # 判断是否达到阈值或最大迭代次数
    iteration = state.get("iteration", 0)  # 全局迭代
    error_iteration = state.get("error_iteration", 0)  # 错误聚焦迭代
    
    if error_accuracy >= error_focus_threshold or len(error_errors) == 0:
        print(f"✅ 错误样本集收敛，准确率: {error_accuracy:.2%} >= 阈值 {error_focus_threshold}")
        print(f"🔍 进入全局验证阶段")
        # 使用错误子集上的最佳模型
        return {
            "current_prompt": best_error_prompt,
            "current_code": best_error_code,
            "error_errors": error_errors,
            "error_accuracy": error_accuracy,
            "best_error_accuracy": best_error_accuracy,
            "best_error_prompt": best_error_prompt,
            "best_error_code": best_error_code,
            "phase": "global_verify",
            "error_iteration": 0,  # 重置错误迭代
        }
    elif iteration >= MAX_ITERATIONS:
        print(f"⚠️ 达到最大迭代次数 {MAX_ITERATIONS}，任务结束")
        return {
            "phase": "end"
        }
    else:
        print(f"🔄 错误样本集未收敛，继续优化")
        return {
            "error_errors": error_errors,
            "error_accuracy": error_accuracy,
            "best_error_accuracy": best_error_accuracy,
            "best_error_prompt": best_error_prompt,
            "best_error_code": best_error_code,
            "phase": "error_focus",
            "error_iteration": error_iteration + 1,  # 增加错误迭代
        }
    # return {
    #         "phase": "global_verify",
    #         "error_iteration": 0,  # 重置错误迭代
    #     }
def error_summarizer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误分析agent - 基于固定的错误样本集"""
    current_phase = state.get("phase", "error_focus")
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    iteration = state.get("iteration",0)
    errors_to_analyze = []
    error_iteration = state.get("error_iteration", 0)
    if current_phase == "error_focus":
        if error_iteration == 0:
            # 第一次错误聚焦：使用全局错误（首次评估后的错误）
            errors_to_analyze = state.get("global_errors", [])
            feature_importance = state.get("feature_importance")
            print(f"第一次错误聚焦：分析全局错误 {len(errors_to_analyze)} 个")
        else:
            # 后续错误聚焦：只分析错误集中仍然出错的样本
            feature_importance = state.get("error_performance")
            errors_to_analyze = state.get("error_errors", [])
            print(f"第{error_iteration+1}次错误聚焦：分析错误集中仍错误的样本 {len(errors_to_analyze)} 个")
    # 如果没有要分析的错误
    if not errors_to_analyze:
        print("✅ 无错误样本需要分析")
        # 返回必要的空数据结构，保持向后兼容
        return {
            "error_summary": "No errors.",
            "pre1l0_summary": "",
            "pre0l1_summary": ""
        }
    # 使用 fixed_error_dataset
    dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    predictions = state.get("error_predictions", {})
    current_prompt = state["current_prompt"]
    current_code = state["current_code"]
    paper_text = state.get('paper_text', '')
    pre1l0_summary = []
    pre0l1_summary = []
    summary = []
    print(f"\n{'='*60}")
    print(f"开始错误分析，需要分析的错误样本数: {len(errors_to_analyze)}")
    print(f"{'='*60}\n")
    random_pre1l0 = random.sample(pre1l0, min(len(pre1l0),3))
    random_pre0l1 = random.sample(pre0l1, min(len(pre0l1),3))
    selected_sids = set(random_pre1l0) | set(random_pre0l1)
    safe_append_markdown(RECORD_PATH, f"## 错误分析:\n需要分析的错误样本数: {len(errors_to_analyze)}\n随机选择的预1l0样本ID: {random_pre1l0}\n随机选择的预0l1样本ID: {random_pre0l1}\n")
    for sid in errors_to_analyze:
        if sid not in predictions or sid not in dataset_map or sid not in selected_sids:
             continue
        sample = dataset_map[sid]
        pred_info = predictions[sid]
        context = (
            f"[ID: {sid}]\n"
            f"Meme Text: {sample['meme_text']}\n"
            f"Predicted: {pred_info['label']}, Ground_truth: {sample['ground_truth']}\n"
            f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
            f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}\n"
            f"Reasoning: {pred_info['scores'].get('reasoning', '')}"
        )
        direct = f"注意：在当前共{len(errors_to_analyze)}错误样本集中，将无害模因误判为有害数量为 {len(pre1l0)}个，将有害模因误判为无害的数量为{len(pre0l1)}个，错误样本集准确率为 {state.get('error_accuracy', 0):.2%}。请据此调整你的判别策略，重点关注降低两类错误的不平衡性。"
        system_prompt = f"""# Role: 多模态有害内容检测指令审计专家 (LMM Safety Auditor)
## 1. 任务背景与目标
你是一位专门从事多模态大模型（LMM）指令工程与有害内容检测（Hateful Memes Detection）的顶级科研专家。你的核心任务是基于提供的【当前 Prompt】、【量化特征评价】及【权威准则】，深度审计模型在有害内容检测任务中的表现。
你需要通过分析模型的“误判案例”与“打分分布”，精准识别底层 Prompt 在逻辑一致性、维度耦合度及分值极化上的缺陷，并给出具备鲁棒性的优化方案。
其中，H维度（Harmful Dimensions）代表模型对模因有害性的判别分数，分数越高表明该模因越可能包含有害内容（如歧视、误导、恶意讽刺等）；N维度（Non-harmful Dimensions）则代表模型对模因无害性的判别分数，分数越高表明该模因越倾向于良性表达（如幽默调侃、正向共鸣、无害玩梗等）。
## 2. 输入数据 (Input Data)
请基于以下信息进行审计（若缺失请基于通用经验推断）：
- **[权威准则]**: HarMeme (ACL-IJCNLP 2021) 等学术界公认的标注指南。
- **[当前 Prompt]**: {{current_prompt_content}}
- **[量化特征评价]**: 当前各维度的特征重要性分数 (Importance Score) 及误报/漏报统计。
- **[阈值设定]**: 
  - 维度重要性阈值：{dim_importance_threshold}
  - 误报倾向标识：{direct} (例如：FP >> FN 或 FN >> FP)
## 3. 核心审计原则 (Core Principles)
在执行审计时，你必须严格遵守以下决策逻辑：
### 3.1 异常维度清理 (Dimension Cleaning)
- **高频误标清理机制**: 当判别维度出现方向性误判（即真实标签与高分判别维度相悖）时，需依据分值采取分级治理：对于得分集中在 5 至 7 分 的维度，表明其定义存在歧义或边界模糊，必须重构描述以消除偏激打分倾向；对于误判得分高于 7 分 的维度，则视为具有严重误导性，必须直接剔除。
- **噪声维度剔除**: 若某维度的重要性分数低于阈值{dim_importance_threshold}，视其为噪声，予以删除。
- **识别盲区加固（防漏）**: 当判别维度出现方向性误判,针对得分应高实低（<4分）的维度，需通过扩容隐喻语义以消除有害识别盲区，或通过细化分值阶梯以激活无害维度的梯度分辨力。
### 3.2 判别倾向性对冲 (Bias Counteraction)
- **GT 绝对权威**: 所有修正必须以 Ground Truth 为北极星指标，解释为何现有维度背离了 GT。
- **误报 (FP) 过高**: 若 FP 远大于 FN，说明模型过于敏感。必须在 "Harmless" 体系下挖掘并 #新增隐含的防御性维度# （例如：社会评论属性、非针对性幽默、流行文化致敬等）。
- **漏报 (FN) 过高**: 若 FN 远大于 FP，需强化隐喻与仇恨符号的权重，增加对隐含恶意的识别力度。
## 4. 执行 workflow (Execution Workflow)
### 阶段二：修正决策 (Correction Strategy)
1. **维度独立性校准 (Decoupling)**: 强制模型建立**“独立推理路径”**。在 Prompt 中要求模型为每个维度寻找专属证据，严禁在 H2 的打分中引用 H1 的结论。
2. **中间态锚点 (Middle-Ground Anchoring)**: 针对极化严重的维度，必须定义 4-6 分的触发特征（如：轻微讽刺但无恶意诋毁）。禁止在缺乏极端证据的情况下打出 9 分。
3. **排除项重写 (Must_NOT Refinement)**: 重写在无害样本上频繁触发虚警（Score > 7）维度的排除项。
4. **案例补充** ：在案例补充时，请彻底摒弃“模因ID代表讽刺”或“卡通滤镜、自嘲语气属于无害信号”这类笼统概括，必须将标准锚定在可被文字精确复现的具体内容组合上。这意味着您需要详细描述“文本+视觉”的联合特征及其对应的维度打分逻辑：例如，不应只说“自嘲语气”，而应写明“当文案出现‘我又菜又爱玩，队友别骂了🥲’配合游戏角色倒地截图，且图片角落带有‘菜鸡日常’手写体水印时”，这种具体的“示弱文案+失败场景+趣味水印”组合体现了自我调侃意图，因此应在 N2（幽默表达） 维度给高分，同时在 H1（人身攻击） 维度给低分。
请确保每一条标准都遵循“具体文案原句+视觉元素细节+排版/风格特征→维度高低分判定”的完整链条，让从未见过原图的读者仅凭您的文字描述就能准确复现判别过程。
## 5. 输出规范 (Output Format)
请将你的完整回答以 **JSON 格式** 返回，不要包含任何 Markdown 代码块标记（```json），确保可直接被程序解析。结构如下：
{{
  "判别出错原因分析": "字符串，简述核心病灶及归类",
  "维度调整建议": {{
    "action": "字符串，如：新增/删除/重构",
    "dimension_name": "字符串，涉及的维度名称",
    "reason": "字符串，基于重要性分数或误报率的调整理由",
    "details": "字符串，具体的修改描述，这里需要尽量具体详细"
  }},
  "各维度标准优化建议": {{
    "维度名称 1": {{
      "着重强调": "字符串，需要模型特别注意的特征",
      "补充": "字符串，新增的判断依据",
      "完善": "字符串，具体的定义修正说明"
    }},
    "维度名称 2": {{
      "着重强调": "...",
      "补充": "...",
      "完善": "..."
    }}
  }}，
“额外建议”:"对维度建议之外的新prompt的建议的补充"
}}
"""
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
        if USE_LMCL:
            messages1=[{"role": "user", "content": f"参考标准:{paper_text}\n\n当前大模型打分使用的模因判别标准prompt：{current_prompt}\n\n当前被错误判别打分结果:{context}\n\n,当前由数据分析得到的特征重要性排序以及重要性分数：{feature_importance},请给出你的总结：\n\n"}]

        else:
            messages1=[{"role": "user", "content": f"参考标准:{paper_text}\n\n当前大模型打分使用的模因判别标准prompt：{current_prompt}\n\n当前被错误判别打分结果:{context}\n\n请给出你的总结：\n\n"}]
        response =  prediction_saver.get(round_id=iteration,meme_id=f"{error_iteration}_{sid}_advice")
        if response == None:
            response = llm_tool.call_llm(
                system_prompt=system_prompt,
                messages=messages1
            )
            prediction_saver.save(iteration,f"{error_iteration}_{sid}_advice",response)
        safe_append_markdown(RECORD_PATH, f"### 错误样本ID: {sid}\n**错误原因分析:** {response}\n")
        if sid in pre1l0:
            pre1l0_summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        if sid in pre0l1:
            pre0l1_summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        print(f"--- 模因id: {sid} ---")
        print(f"错误原因分析: {response[:200]}...")
        print("-" * 50)
    return {"error_summary": "\n\n".join(summary),"pre1l0_summary":"\n\n".join(pre1l0_summary),"pre0l1_summary":pre0l1_summary}

def prompt_improver_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """prompt改进agent"""
    pre1l0 = state.get('pre1l0', [])
    pre0l1 = state.get('pre0l1', [])
    pre1l0_memory = state.get("pre1l0_memory","")
    pre0l1_memory = state.get("pre0l1_memory","")
    pre1l0_summary = state.get('pre1l0_summary',"")
    pre0l1_summary = state.get('pre0l1_summary',"")
    old_prompt = state["current_prompt"]
    old_code = state["current_code"]
    error_summary = state["error_summary"]
    iteration = state["iteration"]
    error_iteration = state.get("error_iteration",0)
    # 获取错误样本上下文
    pre1l0_context_list = []
    pre0l1_context_list = []
    context_list = []
    dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    predictions = state.get("error_predictions", {})
    feature_importance = ""
    if state["error_iteration"]==0:
        error_errors = state.get("global_errors", [])
        feature_importance = state.get("feature_importance")
    else:
        error_errors = state.get("error_errors", [])
        feature_importance = state.get("error_feature_importance")
    for sid in error_errors:
        if sid in predictions and sid in dataset_map:
            sample = dataset_map[sid]
            pred_info = predictions[sid]
            context = (
                f"[ID: {sid}]\n"
                f"Meme Text: {sample['meme_text']}\n"
                f"Predicted: {pred_info['label']}, Ground_truth: {sample['ground_truth']}\n"
                f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
                f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}"
            )
            if sid in pre1l0:
                pre1l0_context_list.append(context)
            if sid in pre0l1:
                pre0l1_context_list.append(context)
            context_list.append(context)
    
    combined_context = "\n\n".join(context_list) if context_list else "No specific errors to analyze."
    pre1l0_context = "\n\n".join(pre1l0_context_list) if pre1l0_context_list else "No specific errors to analyze."
    pre0l1_context = "\n\n".join(pre0l1_context_list) if pre0l1_context_list else "No specific errors to analyze."
    pre1l0_prompt = f"""你是一个专注于纠正将无害模因误判为有害的模因有害性判别经验记忆系统，旨在持续演进与优化判别知识库。请基于以下输入进行经验更新：已有历史经验（包括过往判别规则、误判案例及对应评分逻辑）和当前专家提出的新建议（可能包含与旧经验一致、冲突或全新场景的见解）。执行以下操作：融合共识，保留新旧一致的有效规则；修正冲突，当新建议与旧经验矛盾时，优先采纳经验证更可靠的判断依据；补充空白，对历史经验未覆盖的模因类型或边界情况，新增判别准则。输出应形成一套自洽、完整且可执行的更新后判别经验，用于指导后续有害/无害判定
注意，你需要根据经验以及新建议进行经验更新，经验格式以json格式保存，主要内容包括：
#原因分析：用一段话总结当前判别出错的可能原因，需结合上述四类信息进行综合推断。
#维度调整：评估是否需要在“有害”或“无害”判别体系中新增、删除或合并打分维度。维度数量不固定，应根据实际判别需求灵活调整。
#标准优化：针对现有每个判别维度中的具体标准，逐项说明哪些内容需要：
--着重强调（如关键但被弱化的要素），
--补充（如缺失的判别情形），
--合并（如语义重叠或可泛化的条目）。
#**案例补充**:可以增加一些案例以优化模糊判别边界
#请将你的完整回答以 JSON 格式返回，结构如下：
  "判别出错原因分析": "字符串，简述核心病灶及归类",
  "维度调整建议": {{
    "action": "字符串，如：新增/删除/重构",
    "dimension_name": "字符串，涉及的维度名称",
    "reason": "字符串，基于重要性分数或误报率的调整理由",
    "details": "字符串，具体的修改描述，这里需要尽量具体详细"
  }},
  "各维度标准优化建议": {{
    "维度名称 1": {{
      "着重强调": "字符串，需要模型特别注意的特征",
      "补充": "字符串，新增的判断依据",
      "完善": "字符串，具体的定义修正说明"
    }},
    "维度名称 2": {{
      "着重强调": "...",
      "补充": "...",
      "完善": "..."
    }}
  }},
  "额外建议":"对维度建议之外的新prompt的建议的补充"
"""
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
# --合并（如语义重叠或可泛化的条目）。
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
    pre0l1_prompt = f"""你是一个专注于纠正将有害模因误判为无害的模因有害性判别经验记忆系统，旨在持续演进与优化判别知识库。请基于以下输入进行经验更新：已有历史经验（包括过往判别规则、误判案例及对应评分逻辑）和当前专家提出的新建议（可能包含与旧经验一致、冲突或全新场景的见解）。执行以下操作：融合共识，保留新旧一致的有效规则；修正冲突，当新建议与旧经验矛盾时，优先采纳经验证更可靠的判断依据；补充空白，对历史经验未覆盖的模因类型或边界情况，新增判别准则。输出应形成一套自洽、完整且可执行的更新后判别经验，用于指导后续有害/无害判定
注意，你需要根据经验以及新建议进行经验更新，经验格式以json格式保存，主要内容包括：
#原因分析：用一段话总结当前判别出错的可能原因，需结合上述四类信息进行综合推断。
#维度调整：评估是否需要在“有害”或“无害”判别体系中新增、完善打分维度。维度数量不固定，应根据实际判别需求灵活调整。
#标准优化：针对现有每个判别维度中的具体标准，逐项说明哪些内容需要：
--着重强调（如关键但被弱化的要素），
--补充（如缺失的判别情形），
--合并（如语义重叠或可泛化的条目）。
#**案例补充**:可以增加一些案例以优化模糊判别边界
#请将你的完整回答以 JSON 格式返回，结构如下：
  "判别出错原因分析": "字符串，简述核心病灶及归类",
  "维度调整建议": {{
    "action": "字符串，如：新增/删除/重构",
    "dimension_name": "字符串，涉及的维度名称",
    "reason": "字符串，基于重要性分数或误报率的调整理由",
    "details": "字符串，具体的修改描述，这里需要尽量具体详细"
  }},
  "各维度标准优化建议": {{
    "维度名称 1": {{
      "着重强调": "字符串，需要模型特别注意的特征",
      "补充": "字符串，新增的判断依据",
      "完善": "字符串，具体的定义修正说明"
    }},
    "维度名称 2": {{
      "着重强调": "...",
      "补充": "...",
      "完善": "..."
    }}
  }},
  "额外建议":"对维度建议之外的新prompt的建议的补充"
"""
    print(f"\n{'='*60}")
    print(f"记忆整合更新")
    print(f"{'='*60}\n")
    if pre1l0_context_list:
        user_msg = (
            f"已有历史经验:\n{pre1l0_memory}\n\n"
            f"各个专家的新错误分析:\n{pre1l0_summary}\n\n"
            # f"具体错误样例上下文:\n{pre1l0_context}"
        )
        pre1l0_memory = prediction_saver.get(iteration,f"{error_iteration}_pre1l0_memory")
        if pre1l0_memory == None:
            pre1l0_memory = llm_tool.call_llm(
                system_prompt=pre1l0_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            prediction_saver.save(iteration,f"{error_iteration}_pre1l0_memory",pre1l0_memory)
        safe_append_markdown(RECORD_PATH, f"## pre1l0记忆更新\n**输出:**\n{pre1l0_memory}\n")
    if pre0l1_context_list:
        user_msg = (
            f"已有历史经验:\n{pre0l1_memory}\n\n"
            f"各个专家的新错误分析:\n{pre0l1_summary}\n\n"
            # f"具体错误样例上下文:\n{pre0l1_context}"
        )
        pre0l1_memory = prediction_saver.get(iteration,f"{error_iteration}_pre0l1_memory")
        if pre0l1_memory == None:
            pre0l1_memory = llm_tool.call_llm(
                system_prompt=pre0l1_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            prediction_saver.save(iteration,f"{error_iteration}_pre0l1_memory",pre0l1_memory)
        safe_append_markdown(RECORD_PATH, f"## pre0l1记忆更新\n**输出:**\n{pre0l1_memory}\n")
    print(f"\n{'='*60}")
    print(f"开始prompt改进")
    print(f"{'='*60}\n")
    
    direct = f"注意：在当前错误样本集中，将无害模因误判为有害数量为 {len(pre1l0)}个，将有害模因误判为无害的数量为{len(pre0l1)}个，错误样本集准确率为 {state.get('error_accuracy', 0):.2%}。请据此调整你的判别策略，重点关注降低两类错误的不平衡性。"
    # 第二步：生成新的prompt
    system_prompt = """
You are a prompt engineer specializing in harmful meme detection.  
Your ONLY task is to **rewrite the original evaluation prompt** based on the following aspects.  
a.The revision suggestions from various experts;
-Specifically:
-1. Integrate revision suggestions from domain experts.
-2. If gaps are identified, **add new scoring dimensions** following the existing naming convention:
   - Harmful dimensions: `Hn`(e.g., H1, H2, ...)
   - Non-harmful dimensions: `Nm` (e.g., N1, N2, ...)
-3. For each new dimension, provide:
   - A clear definition
   - Concrete scoring criteria
b.The ranking of importance scores for the scoring features in the previous prompt after data analysis
c.Context of specific error examples
-4.Additionally, these contents need to be noted in the prompt
a.Extreme Scoring (Halo Effect/Polarization): The model tends to assign extreme scores across all dimensions (all 1s or all 9s) due to preconceived notions, resulting in a loss of discriminative power between dimensions.
b.Dimensional Logical Coupling: Improper Prompt instructions lead the model to assume that a high score in Dimension A necessitates a high score in Dimension B (e.g., mistakenly assuming that targeted content H1 necessarily implies high harm H2).
c.Instruction Attention Drift: Excessively long Prompts cause the model to overlook core constraints (e.g., H2.5 exclusion clauses).
d.Visual-Textual Logical Disconnection (Modality Gap): The model understands the image and text independently but fails to infer the "emergent" sarcastic intent arising from their combination.
#CRITICAL RULES:
1. You MUST output ONLY the new English prompt text — nothing else.
2. Note: Your task is to rewrite the prompt, not to supplement the original one. Keep the overall format consistent with the original prompt:
'Content
JSON Format Requirements'
3. DO NOT evaluate any meme, DO NOT generate JSON, DO NOT simulate scoring.
4. The new prompt must preserve the original output format: 
   {
     "harmful_scores": {"H1":int,"H2":int..},
     "harmless_scores": {"N1":int,"N2":int..},
     "reasoning": "string"
   }
5. Incorporate the updated criteria into the instructions.
6. Keep the tone authoritative, clear, and suitable for expert annotators.
JSON Schema Consistency: The dimensions defined in the scoring criteria of the rewritten prompt must exactly match the keys required in the final JSON output format. No extra or missing dimensions are allowed.
Naming Convention: All keys within harmful_scores must strictly follow the Hn format (e.g., "H1", "H2"), and all keys within harmless_scores must strictly follow the Nn format (e.g., "N1", "N2").
Remember: You are writing an instruction for OTHER evaluators — not acting as one.
"""
    #   Specific error example：
    #   #####\n{combined_context}\n#####
    if USE_LMCL:
        if USE_DMEE:
            messages1 = [{"role": "user", 
                       "content": f"""Original prompt:
    #####\n{old_prompt}\n#####
    Suggestions for rectifying the misjudgment of harmless memes as harmful:
    #####\n{pre1l0_memory}\n#####
    Suggestions for rectifying the misjudgment of harmful memes as harmless:
    #####\n{pre0l1_memory}\n#####
    Now, generate the NEW PROMPT (in English) that integrates the updated criteria while preserving the original structure and output format.
    OUTPUT ONLY THE NEW PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}]
        else:
            messages1 = [{"role": "user", 
                       "content": f"""Original prompt:
    #####\n{old_prompt}\n#####
    ranking of importance scores:
    #####\n{feature_importance}\n#####
    Now, generate the NEW PROMPT (in English) that integrates the updated criteria while preserving the original structure and output format.
    OUTPUT ONLY THE NEW PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}]
    else:
        messages1 = [{"role": "user", 
                   "content": f"""Original prompt:
#####\n{old_prompt}\n#####
Suggestions for rectifying the misjudgment of harmless memes as harmful:
#####\n{pre1l0_memory}\n#####
Suggestions for rectifying the misjudgment of harmful memes as harmless:
#####\n{pre0l1_memory}\n#####
Now, generate the NEW PROMPT (in English) that integrates the updated criteria while preserving the original structure and output format.
OUTPUT ONLY THE NEW PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}]
    
    system_prompt = system_prompt
    new_prompt = prediction_saver.get(iteration,f"{error_iteration}_new_prompt")
    if new_prompt==None:
        new_prompt = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=messages1,
        )
        prediction_saver.save(iteration,f"{error_iteration}_new_prompt",new_prompt)
    # para = extract_dict_from_string(new_prompt)
    print(f"🆕 新生成的prompt:")
    print(new_prompt[:500] + "..." if len(new_prompt) > 500 else new_prompt)
    print("\n" + "-"*50 + "\n")
    safe_append_markdown(RECORD_PATH, f"## 新生成的Prompt:\n{new_prompt}\n")
#     # 第三步：生成新的代码
#     system_prompt = f"""
# 你是一位模因判别代码逻辑生成专家，请根据更新后的判别标准与逻辑，编写一个用于从评分结果生成最终判别的函数。
# 要求如下：
# 代码必须完整而且直接可执行，这点很重要；
# 函数名为 def classify_meme(scores)；函数实现应自包含，不调用外部方法或变量，即所有逻辑都写在classify_meme中，不要出现其他方法名与调用关系；
# 输入 scores 为符合原始格式的字典，具体格式：\n\n{para}
# 函数必须返回字符串 'harmless' 或 'harmful'；
# 仅使用 Python 标准库，不得引入任何第三方依赖；
# 仅输出该函数的完整代码，不包含任何注释、解释或其他额外文本。
# """
    
#     new_code = llm_tool.call_llm(
#         system_prompt=system_prompt,
#         messages=[{"role": "user", "content": f"原code:\n{old_code}\n\n更新后的判别标准与逻辑:\n{improvement_summary}\n\n请输出新的classify_meme方法:"}],
#     )
    
#     new_code = extract_code_from_markdown(new_code)
#     print(f"💻 新生成的代码:")
#     print(new_code)
#     print("\n" + "-"*50 + "\n")
    
    return {
        "current_code": state["current_code"],
        "current_prompt": new_prompt,
        "prompt_history": state.get("prompt_history", []) + [{
            'errors': list(state.get("error_errors", [])),
            'error_accuracy': state.get("error_accuracy", 0),
            'error_summary': error_summary,
            "new_prompt": new_prompt,
            "new_code": state["current_code"]
        }],
        "pre1l0": [],  # 重置误判统计
        "pre0l1": [],
        "pre1l0_memory":pre1l0_memory,
        "pre0l1_memory":pre0l1_memory
    }

def increment_iteration(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能增加迭代次数"""
    current_phase = state.get("phase", "global_eval")
    iteration = state.get("iteration", 0)
    error_iteration = state.get("error_iteration", 0)
    
    print(f"\n{'='*60}")
    
    if current_phase == "global_verify":
        # 全局验证后：增加全局迭代
        new_iteration = iteration + 1
        print(f"全局迭代次数: {new_iteration} (增加全局)")
    elif current_phase == "error_focus" and error_iteration == 0:
        # 第一次进入错误聚焦：不增加全局迭代
        # print(f"进入错误聚焦，全局迭代保持: {iteration}")
        new_iteration = iteration
    else:
        # 错误聚焦内部：不增加全局迭代
        # print(f"错误聚焦内部循环，全局迭代保持: {iteration}")
        new_iteration = iteration
    print(f"错误聚焦迭代: {error_iteration}")
    print(f"{'='*60}\n")
    return {"iteration": new_iteration}