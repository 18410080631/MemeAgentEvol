# agents.py
from typing import Dict, Any, List
from tools import LLMTool,train_logistic_regression, extract_pdf_text, extract_code_from_markdown,code_fix,extract_dict_from_string,caculate_acc,analyze_score_features
from config import MODEL_NAME, TEMPERATURE, THRESHOLD, error_focus_threshold, MAX_ITERATIONS,DATASET_NAME,RECORD_PATH,USE_LMCL,USE_DMEE,USE_DEEP,dim_importance_threshold,HARM_text,FHM_text,MAMI_text,USE_ERROR_REF
from tools import safe_append_markdown,save_model_minimal,PredictionSaver
import json_repair
import os
import random
random.seed(33)
from tqdm import tqdm
RECORD_PATH = f"{DATASET_NAME}/{RECORD_PATH}"
llm_tool = LLMTool(model_name=MODEL_NAME, temperature=TEMPERATURE)
prediction_saver = PredictionSaver(DATASET_NAME)
import json
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

    current_prompt = state["current_prompt"]
    dataset: List[Dict] = state["dataset"]
    pre1l0 = []
    pre0l1 = []
    predictions = {}
    iteration = state.get("iteration",0)
    pre1l0_memory = state.get('pre1l0_memory',[])
    pre0l1_memory = state.get('pre0l1_memory',[])
    data,feature_names = [],[]
    safe_append_markdown(RECORD_PATH, f"## 全局评估打分:\n")
    error_idxs = []
    labels,data,h_n_data,feature_names = [],[],[],[]
    h_titles,h_scores,n_scores,n_titles = [],[],[],[]
    all_scores = []
    for idx,sample in enumerate(tqdm(dataset)):
        system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
        # user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']} \n\nOnly Provide your scoring results for the current meme in JSON format:"
        user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}\n\nThe description of the image:{sample['meme_content']}\n\nOnly Provide your scoring results for the current meme in JSON format:{{'harmful_scores':{{..}},'harmless_scores':{{...}},'reason':'...'}}"

        id = sample['id']
        ground_truth = sample['ground_truth']
        ground_truth_label = [1] if ground_truth == "harmful" else [0]
        try:
            response = prediction_saver.get(iteration,id)
            if response == None:
                response = llm_tool.call_llm(
                    system_prompt=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                    # meme_src=sample.get("meme_src", None),
                    max_tokens=2048
                )
                prediction_saver.save(round_id=iteration,meme_id=id,response=response)
            safe_append_markdown(RECORD_PATH, f"### 样本ID: {id}\n**打分结果:** {response}\n")
            scores = json_repair.loads(response)
        except Exception as e:
            print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
            # print(f"原始响应: {response[:200]}...")
            continue  
        harmful_scores = scores[list(scores.keys())[0]]
        harmless_scores = scores[list(scores.keys())[1]]
        if idx == 0:
            l = len(harmful_scores) + len(harmless_scores)
            data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
            labels.append(ground_truth)
            h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
            h_titles = list(harmful_scores.keys())
            n_titles = list(harmless_scores.keys())
            h_scores.append(list(harmful_scores.values()))
            n_scores.append(list(harmless_scores.values()))
            all_scores.append(scores)
        else:
            if len(harmful_scores) + len(harmless_scores) == l:
                labels.append(ground_truth)
                h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
                data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
                h_scores.append(list(harmful_scores.values()))
                n_scores.append(list(harmless_scores.values()))
                all_scores.append(scores)
            else:
                error_idxs.append(idx)
        print(f"{id}: 当前打分： ")
        print(f"  harmful_scores: {scores[list(scores.keys())[0]]}")
        print(f"  harmless_scores: {scores[list(scores.keys())[1]]}")
        print("-" * 50)
    feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
    res = train_logistic_regression(data=data,feature_names=feature_names)  
    performance,train_predictions = caculate_acc(labels,h_n_data)
    report,report1,report2 = analyze_score_features(labels,h_titles=h_titles,h_scores=h_scores,s_titles=n_titles,s_scores=n_scores)
    formula = res["formula"]
    scaler_params = res["scaler_params"]
    intercept = res["intercept"]
    weights = res["weights"]
    feature_importance = res["feature_importance"]         
    safe_append_markdown(RECORD_PATH, f"## 全局评估结果\n**性能指标:** {performance}\n**逻辑回归公式:** {formula}\n**特征重要性:** {feature_importance}\n")
    p = 0
    for idx in range(len(dataset)):
        if idx not in error_idxs:
            sample = dataset[idx]
            label = train_predictions[p]
            t_scores = all_scores[p]
            p+=1
            ground_truth = sample['ground_truth']
            id = sample['id']
            if label==1 and ground_truth == 'harmless':
                if id not in pre1l0:  # 避免重复
                    pre1l0.append(id)
            if label==0 and ground_truth == 'harmful':
                if id not in pre0l1:  # 避免重复
                    pre0l1.append(id)
            label_str = 'harmful' if label==1 else 'harmless'
            if (label==1 and ground_truth == 'harmless') or (label==0 and ground_truth == 'harmful'):
                print(f"{id}: 当前预测与真实值：")
                print(f"  Predict: {label}")
                print(f"  GroundTruth: {ground_truth}")
                print("-" * 50)
            predictions[sample["id"]] = {'label': label_str, "scores": t_scores}
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
            "iteration":iteration+1,
            "report":[report,report1,report2]
        }
    else:
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
            "iteration":iteration+1,
            "report":[report,report1,report2]
        }

def evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局评估agent"""
    current_phase = state.get("phase", "global_eval")
    performance = state["performance"]
    acc = performance["accuracy"]
    f1 = performance["f1"]
    res = state["res"]
    scores = list(list(state["global_predictions"].values())[0]["scores"].values())
    dim_len = len(scores[0])+len(scores[1])
    res["acc"].append(acc)
    res["f1"].append(f1)
    res["dims"].append(dim_len)
    if current_phase == "global_eval":
        return _global_evaluator(state)
    elif current_phase == "global_verify":
        return _global_verify_evaluator(state)
    else:
        print(f"⚠️ 未知阶段: {current_phase}")
        return {"phase": "end","res":res}

def _global_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """首次全局评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    predictions = state.get("global_predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    performance = state.get("performance",{})
    accuracy,f1 = performance["accuracy"],performance["f1"]
    best_global_accuracy = accuracy
    best_global_prompt = state["current_prompt"]
    best_global_code = state["current_code"]
    output_dir = DATASET_NAME
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    # 计算错误
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"首次全局评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"accuracy:{accuracy},f1:{f1}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(best_global_prompt)
    # save_model_minimal(state)
    safe_append_markdown(RECORD_PATH, f"## 首次全局评估结果\n**准确率:** {accuracy:.2%},f1:{f1}\n**错误样本数:** {len(errors)}\n**将无害模因误判为有害数量:** {len(pre1l0)}\n**将有害模因误判为无害数量:** {len(pre0l1)}\n")
    print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
    
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
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
        best_global_info = {
            "best_global_prompt":best_global_prompt,
            "best_global_code":best_global_code,
            "best_global_report":state["report"],
            "best_global_predictions":predictions,
            "best_global_performance":performance,
            "best_fixed_error_dataset":fixed_error_dataset,
            "best_global_pre1l0":pre1l0,
            "best_global_pre0l1":pre0l1
        }
        return {
            "best_global_info":best_global_info,
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
            "best_error_accuracy":0.0,
            "current_prompt":best_global_prompt
        }
    

def _global_verify_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局验证评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    iteration = state.get("iteration")
    performance = state.get("performance",{})
    accuracy,f1 = performance["accuracy"],performance["f1"]
    best_global_info = state.get("best_global_info")
    predictions = state.get("global_predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    report = state["report"]
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    print(f"\n{'='*60}")
    print(f"全局验证评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"准确率: {accuracy:.2%}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    if accuracy < best_global_info["best_global_performance"]["accuracy"]:
        print("新prompt不如best_prompt，退回原best_prompt")
        predictions = best_global_info["best_global_predictions"]
        current_code = best_global_info["best_global_code"]
        report = best_global_info["best_global_report"]
        current_prompt = best_global_info["best_global_prompt"]
        fixed_error_dataset = best_global_info["best_fixed_error_dataset"]
        pre1l0 = best_global_info["best_global_pre1l0"]
        pre0l1 = best_global_info["best_global_pre0l1"]
        print(f"📊 使用best错误样本集，包含 {len(fixed_error_dataset)} 个样本")
    else:
        fixed_error_dataset = [sample for sample in state["dataset"] if sample["id"] in errors]
        best_global_info = {
            "best_global_prompt":state["current_prompt"],
            "best_global_code":state["current_code"],
            "best_global_report":state["report"],
            "best_global_predictions":predictions,
            "best_global_performance":performance,
            "best_fixed_error_dataset":fixed_error_dataset,
            "best_global_pre1l0":pre1l0,
            "best_global_pre0l1":pre0l1
        }
        current_prompt = state["current_prompt"]
        current_code = state["current_code"]
        output_dir = DATASET_NAME
        os.makedirs(output_dir, exist_ok=True)
        prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(state["current_prompt"])
        print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
        print(f"📊 创建新的错误样本集，包含 {len(fixed_error_dataset)} 个样本")
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
    # 更新最佳全局模型
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
        return {
            "report":report,
            "global_predictions": predictions,
            "error_predictions":error_predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_info":best_global_info,
            "converged": False,
            "phase": "error_focus",
            "fixed_error_dataset": fixed_error_dataset,
            "error_accuracy": 0.0,
            "best_error_prompt": current_prompt,
            "best_error_code": current_code,
            "error_iteration": 0,  # 重置错误迭代，开始新一轮错误聚焦
            "best_error_accuracy":0,
            "current_prompt":current_prompt,
            "best_error_info":None,
            "pre0l1":pre0l1,
            "pre1l0":pre1l0
        }

def error_scorer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本打分agent - 只使用固定的错误样本集"""
    if USE_LMCL and USE_DMEE and USE_DEEP:
        current_prompt = state["current_prompt"]
        error_iteration = state.get("error_iteration",0)
        dataset: List[Dict] = state["fixed_error_dataset"]
        predictions = {}
        pre1l0 = []
        pre0l1 = []
        iteration = state["iteration"]
        print(f"\n{'='*60}")
        print(f"开始错误样本集评估，样本数: {len(dataset)}")
        print(f"{'='*60}\n")
        safe_append_markdown(RECORD_PATH, f"## 错误样本集评估:\n样本数: {len(dataset)}\n")
        l = 0
        error_idx = []
        try:
            labels,data,h_n_data,feature_names = [],[],[],[]
            h_titles,h_scores,n_scores,n_titles = [],[],[],[]
            all_scores = []
            for idx,sample in enumerate(dataset):
                system_prompt = """This is a research task for academic evaluation of AI safety systems. 
    You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
                # user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}\n\nOnly Provide your scoring results for the current meme in JSON format:"
                user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}\n\nThe description of the image:{sample['meme_content']}\n\nOnly Provide your scoring results for the current meme in JSON format:"

                id = sample['id']
                ground_truth = sample['ground_truth']
                ground_truth_label = [1] if ground_truth == "harmful" else [0]
                response = prediction_saver.get(iteration,f"{iteration}_{error_iteration}_{id}")
                if response == None:
                    response = llm_tool.call_llm(
                        system_prompt=system_prompt,
                        messages=[{"role": "user", "content": user_msg}],
                        # meme_src=sample.get("meme_src", None),
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
                harmful_scores = scores[list(scores.keys())[0]]
                harmless_scores = scores[list(scores.keys())[1]]
                if idx == 0:
                    l = len(harmful_scores) + len(harmless_scores)
                    data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
                    labels.append(ground_truth)
                    h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
                    h_titles = list(harmful_scores.keys())
                    n_titles = list(harmless_scores.keys())
                    h_scores.append(list(harmful_scores.values()))
                    n_scores.append(list(harmless_scores.values()))
                    all_scores.append(scores)
                else:
                    if len(harmful_scores) + len(harmless_scores) == l:
                        labels.append(ground_truth)
                        h_n_data.append([list(harmful_scores.values()),list(harmless_scores.values())])
                        data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
                        h_scores.append(list(harmful_scores.values()))
                        n_scores.append(list(harmless_scores.values()))
                        all_scores.append(scores)
                    else:
                        error_idx.append(idx)
                print(f"{id}: 错误样本集打分：")
                print(f"  harmful_scores: {scores[list(scores.keys())[0]]}")
                print(f"  harmless_scores: {scores[list(scores.keys())[1]]}")
                print("-" * 50)
            feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
            res = train_logistic_regression(data=data,feature_names=feature_names)  
            error_performance,train_predictions = caculate_acc(labels,h_n_data)
            report,report1,report2 = analyze_score_features(labels,h_titles=h_titles,h_scores=h_scores,s_titles=n_titles,s_scores=n_scores)
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
                    t_scores = all_scores[p]
                    p+=1
                    ground_truth = sample['ground_truth']
                    id = sample['id']
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

                    predictions[sample["id"]] = {'label': label_str, "scores": t_scores}                
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
            "error_feature_importance":error_feature_importance,
            "report":[report,report1,report2]
        }
    else:
        return {}

def error_evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本评估agent"""
    if USE_DMEE and USE_LMCL and USE_DEEP:
        best_error_info = state.get("best_error_info",None)
        if best_error_info==None:
            best_error_info = {
                "best_error_prompt":state["current_prompt"],
                "best_error_report":state["report"],
                "best_error_predictions":state["error_predictions"],
                "best_error_performance":state["error_performance"],
                "best_error_pre1l0":state.get("pre1l0", []),
                "best_error_pre0l1":state.get("pre0l1", [])
            }
        error_preds = state["error_predictions"]
        error_dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
        pre1l0 = state.get("pre1l0", [])
        pre0l1 = state.get("pre0l1", [])
        report = state["report"]
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
        if error_accuracy>=best_error_info["best_error_performance"]["accuracy"]:
            current_prompt = state["current_prompt"]
            best_error_info = {
            "best_error_prompt":current_prompt,
            "best_error_report":state["report"],
            "best_error_predictions":state["error_predictions"],
            "best_error_performance":state["error_performance"],
            "best_error_pre1l0":pre1l0,
            "best_error_pre0l1":pre0l1
            }
            print(f"✅ 更新错误样本集最佳模型，准确率: {error_accuracy:.2%}")
        else:
            current_prompt = best_error_info["best_error_prompt"]
            report = best_error_info["best_error_report"]
            error_preds = best_error_info["best_error_predictions"]
            error_performance = best_error_info["best_error_performance"]
            pre0l1 = best_error_info["best_error_pre0l1"]
            pre1l0 = best_error_info["best_error_pre1l0"]
            print(f"⚠️ 错误样本集准确率未提升，当前: {error_accuracy:.2%}, 最佳: {best_error_info["best_error_performance"]["accuracy"]:.2%}")
        # 更新错误子集最优模型
        error_errors = [
            sid for sid, pred in error_preds.items()
            if pred['label'].lower() != error_dataset_map[sid]["ground_truth"].lower()
        ]
        # 判断是否达到阈值或最大迭代次数
        error_iteration = state.get("error_iteration", 0)  # 错误聚焦迭代
        if error_iteration>MAX_ITERATIONS or error_accuracy >= error_focus_threshold or len(error_errors) == 0:
            print(f"✅ 错误样本集收敛，准确率: {error_accuracy:.2%} >= 阈值 {error_focus_threshold}")
            print(f"🔍 进入全局验证阶段")
            # 使用错误子集上的最佳模型
            return {
                "current_prompt": current_prompt,
                "error_errors": error_errors,
                "error_accuracy": error_accuracy,
                "best_error_info": best_error_info,
                "phase": "global_verify",
                "error_iteration": 0,  # 重置错误迭代
            }
        else:
            print(f"🔄 错误样本集未收敛，继续优化")
            return {
                "current_prompt":current_prompt,
                "pre0l1":pre0l1,
                "pre1l0":pre1l0,
                "error_errors": error_errors,
                "error_accuracy": error_accuracy,
                "best_error_info":best_error_info,
                "phase": "error_focus",
                "error_iteration": error_iteration + 1,  # 增加错误迭代
                "report":report
            }
    else:
        return {
                "phase": "global_verify",
                "error_iteration": 0,  # 重置错误迭代
            }
def error_summarizer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误分析agent - 基于固定的错误样本集"""
    current_phase = state.get("phase", "error_focus")
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    iteration = state.get("iteration",0)
    errors_to_analyze = []
    error_iteration = state.get("error_iteration", 0)
    formula = state.get("current_code")
    feature_importance = state.get("feature_importance")
    reports = state.get("report")

    if current_phase == "error_focus":
        if error_iteration == 0:
            # 第一次错误聚焦：使用全局错误（首次评估后的错误）
            errors_to_analyze = state.get("global_errors", [])
            feature_importance = state.get("feature_importance")
            current_prompt = state["current_prompt"]
            print(f"第一次错误聚焦：分析全局错误 {len(errors_to_analyze)} 个")
        else:
            # 后续错误聚焦：只分析错误集中仍然出错的样本
            formula = ""
            feature_importance = ""
            current_prompt = state["current_prompt"]
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
    paper_text = state.get('paper_text', '')
    pre1l0_summary = []
    pre0l1_summary = []
    summary = []
    print(f"\n{'='*60}")
    print(f"开始错误分析，需要分析的错误样本数: {len(errors_to_analyze)}")
    print(f"{'='*60}\n")
    random_pre1l0 = random.sample(pre1l0, min(len(pre1l0),2))
    random_pre0l1 = random.sample(pre0l1, min(len(pre0l1),2))
    selected_sids = set(random_pre1l0) | set(random_pre0l1)
    safe_append_markdown(RECORD_PATH, f"## 错误分析:\n需要分析的错误样本数: {len(errors_to_analyze)}\n随机选择的预1l0样本ID: {random_pre1l0}\n随机选择的预0l1样本ID: {random_pre0l1}\n")
    for sid in errors_to_analyze:
        if sid not in predictions or sid not in dataset_map or sid not in selected_sids:
             continue
        sample = dataset_map[sid]
        pred_info = predictions[sid]
        len_h,len_n = len(pred_info['scores']["harmful_scores"]),len(pred_info['scores']["harmless_scores"])


        context = (
            f"[ID: {sid}]\n"
            f"Meme Text: {sample['meme_text']}\n The description of the image:{sample['meme_content']}\n"
            f"The Meme was predicted: {pred_info['label']} \n"
            f"The Ground Truth of the meme is: {sample['ground_truth']}\n"
            f"The wrong LLM scores:\n"
            f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
            f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}\n"
            f"其中，H维度（Harmful Scores）代表模型对模因有害性的判别分数，分数越高表明该模因越可能包含有害内容（如歧视、误导、恶意讽刺等）；N维度（Harmless Scores）则代表模型对模因无害性的判别分数，分数越高表明该模因越倾向于良性表达（如幽默调侃、正向共鸣、无害玩梗等）。\n" 
            f"计算方法：Predict = Harmful if Aver(Harmful Scores) > Aver(Harmless Scores) else Harmless"
        )
        system_prompt_add_dimension = f"""你是一位专门从事多模态大模型（LMM）指令工程与有害内容检测（Hateful Memes Detection）的维度内容补充专家。
你的核心任务是基于以下信息：
- **[权威准则]**: HarMeme (ACL-IJCNLP 2021) 等学术界公认的标注指南。
{paper_text}
- **[当前 Prompt]**: {current_prompt} \n
- **[当前被错误判别的打分结果]**：{context} \n
你需要通过分析模型的“误判案例”精准识别评估 [当前 Prompt] 各个打分维度的内容中存在的问题，并给出详细优化方案。

- **GT 绝对权威**: 所有修正必须以 Ground Truth 为北极星指标。
【评判标准】
如果Ground Truth 为 Harmful 则正确表现应该为 Harmful Scores 高 Harmless Scores 低
如果Ground Truth 为 Harmless 则正确表现应该为 Harmful Scores 低 Harmless Scores 高

## 1.建议类型 *为少于4个的评判方*（Harmful Scores or Harmless Scores）：
a.新增维度
b.额外建议 (在prompt维度评估以外需要特别强调的内容：例如 当前打分偏向极端（H全高分，N全地方），需要特别强调独立打分)

## 2.修正决策 (Correction Strategy)
1）.维度调整建议：为少于4个的评判方（Harmful Scores or Harmless Scores）新增1-2个维度（H or N）来增加分析面

## 3. 输出规范 (Output Format)

请将你的完整回答以 **JSON 格式** 返回，不要包含任何 Markdown 代码块标记（```json），确保可直接被程序解析。结构如下：
{{
  "判别出错原因分析": "详细说明当前分数出错的原因，包括需要调整的各个维度等。【核心原则】(注意你的分析不是纠正打分，而是纠正该评估维度的表达方式，不少于300words)",
  "满足修正决策的维度集合以及需要采取的操作"：
  "需要新增维度": {{ 
    "维度名称1":{{
        "action": "新增",
        "reason": "字符串(不少于200words)",
        "details": "字符串，具体的维度内容描述，这里需要尽量具体详细(不少于200words)"
    }},
    "维度名称2":{{
        ...
    }}...
  }}
}}
"""
        addition_cut_prompt = ""
        if len_h<4 or len_n<4:
            system_prompt = system_prompt_add_dimension
        else:

            addition_cut_prompt = "#现有操作：\n"+f"{reports[1]}\n+{reports[2]}\n""请在现有操作的基础上提出进一步建议:"
            if not USE_LMCL:
                addition_cut_prompt = ""
            system_prompt = f"""你是一位专门从事多模态大模型（LMM）指令工程与有害内容检测（Hateful Memes Detection）的顶级科研专家。
{addition_cut_prompt}
你的核心任务是基于以下信息：
- **[权威准则]**: HarMeme (ACL-IJCNLP 2021) 等学术界公认的标注指南。
{paper_text}
- **[当前 Prompt]**: {current_prompt} \n
- **[当前被错误判别的打分结果]**：{context} \n
- **[量化特征]**: （通过逻辑回归对四十个有害模因样本在[当前 Prompt]进行打分以后的各个维度分数进行评估得到的计算公式与权重分布）：
计算公式：
{formula}\n
（其正确表现应为H的参数为正数，N的参数为负数）
权重分布：
{feature_importance}\n
你需要通过分析模型的“误判案例”与“打分分布”，精准识别评估 [当前 Prompt] 各个打分维度的内容中存在的问题，并给出详细优化方案。

- **GT 绝对权威**: 所有修正必须以 Ground Truth 为北极星指标。
【评判标准】
如果Ground Truth 为 Harmful 则正确表现应该为 Harmful Scores 高 Harmless Scores 低
如果Ground Truth 为 Harmless 则正确表现应该为 Harmful Scores 低 Harmless Scores 高

## 1.建议类型：
a.对某个维度的具体内容进行重写或改写
b.额外建议 (在prompt维度评估以外需要特别强调的内容：例如 当前打分偏向极端（H全高分，N全地方），需要特别强调独立打分)

## 2.修正决策 (Correction Strategy)
整体思路：对本应该表现高的H or N一方 新增新的更敏感的维度内容来增加其分析权重，并使得在 #现有操作 基础上能将维度总数维持在4-6之间：
2）.（逻辑回归维度权重<{dim_importance_threshold} ）的不重要维度进行（维度调整建议:删除该维度或合并该维度）

## 4. 输出规范 (Output Format)

请将你的完整回答以 **JSON 格式** 返回，不要包含任何 Markdown 代码块标记（```json），确保可直接被程序解析。结构如下：
{{
  "判别出错原因分析": "详细说明当前分数出错的原因，包括需要调整的各个维度等。【核心原则】(注意你的分析不是纠正打分，而是纠正该评估维度的表达方式，不少于300words)",
  "满足修正决策的维度集合以及需要采取的操作"：
  "需要新增或删除或合并的维度": {{ 
    "维度名称1（如H1）":{{
        "action": "新增",
        "reason": "字符串，基于重要性分数或误报率的调整理由(不少于200words)",
        "details": "字符串，具体的修改描述，这里需要尽量具体详细(不少于200words)"
    }},
    "维度名称1（如H1）":{{
        "action": "新增",
        "reason": "字符串，基于重要性分数或误报率的调整理由(不少于200words)",
        "details": "字符串，具体的修改描述，这里需要尽量具体详细(不少于200words)"
    }}
  }},
    “额外建议”:"对维度建议之外的新prompt部分存在的问题的补充(比如，强调各个维度应独立打分，不可以根据主观偏见，出现一方分数全是1一方全是9的情况)"
}}
"""


#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
        messages=[{"role": "user", "content": f"请给出你的总结：\n\n"}]
        response =  prediction_saver.get(round_id=iteration,meme_id=f"{error_iteration}_{sid}_advice")
        if response == None:
            response = llm_tool.call_llm(
                system_prompt=system_prompt,
                messages=messages,
                # meme_src=sample.get("meme_src", None),
                temperature=1.0
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
    return {"error_summary": "\n\n".join(summary),"pre1l0_summary":"\n\n".join(pre1l0_summary),"pre0l1_summary":"\n\n".join(pre0l1_summary)}

def prompt_improver_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """prompt改进agent"""
    pre1l0 = state.get('pre1l0', [])
    pre0l1 = state.get('pre0l1', [])
    random_pre1l0 = random.sample(pre1l0, min(len(pre1l0),2))
    random_pre0l1 = random.sample(pre0l1, min(len(pre0l1),2))
    pre1l0_summary = state.get('pre1l0_summary',"")
    pre0l1_summary = state.get('pre0l1_summary',"")
    old_prompt = state["current_prompt"]
    error_summary = state["error_summary"]
    iteration = state["iteration"]
    error_iteration = state.get("error_iteration",0)
    reports = state["report"]
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
                f"Meme Text: {sample['meme_text']}\n The description of the image:{sample['meme_content']}\n"
                f"The Meme was predicted: {pred_info['label']} \n"
                f"The Ground Truth of the meme is: {sample['ground_truth']}\n"
                f"The wrong LLM scores:\n"
                f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
                f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}\n"
                f"其中，H维度（Harmful Scores）代表模型对模因有害性的判别分数，分数越高表明该模因越可能包含有害内容（如歧视、误导、恶意讽刺等）；N维度（Harmless Scores）则代表模型对模因无害性的判别分数，分数越高表明该模因越倾向于良性表达（如幽默调侃、正向共鸣、无害玩梗等）。\n" 
                f"计算方法：Predict = Harmful if Aver(Harmful Scores) > Aver(Harmless Scores) else Harmless"
            )
            if sid in random_pre1l0:
                pre1l0_context_list.append(context)
            if sid in random_pre0l1:
                pre0l1_context_list.append(context)
            context_list.append(context)
    
    combined_context = "\n\n".join(context_list) if context_list else "No specific errors to analyze."
    pre1l0_context = "\n\n".join(pre1l0_context_list) if pre1l0_context_list else "No specific errors to analyze."
    pre0l1_context = "\n\n".join(pre0l1_context_list) if pre0l1_context_list else "No specific errors to analyze."
    len_h,len_n = len(pred_info['scores']["harmful_scores"]),len(pred_info['scores']["harmless_scores"])
    additional_cut_prompt = "\n需要额外删除或者合并的维度"+reports[1]+f"\n{reports[2]}"
# 已有历史经验误判案例
# {pre1l0_context}
    if not USE_LMCL:
        additional_cut_prompt = ''
    if USE_DMEE:
        pre1l0_prompt = f"""你是一个专注于纠正将无害模因误判为有害的模因有害性判别经验总结记忆系统，旨在持续演进与优化判别知识库。
    请基于以下输入进行经验更新：
    各个专家提出的不同建议：
    {pre1l0_summary}\n
    {additional_cut_prompt}
    执行以下操作：
    综合各个专家的意见形成最核心的两条操作建议：
    ##Note:
    1.建议类型：
    a.新增或删除或合并维度
    b.对某个维度的具体内容进行重写或改写
    c.额外建议 (在prompt维度评估以外需要特别强调的内容：例如 当前打分偏向极端（H全高分，N全低分），需要特别强调独立打分)

    2.维度数量限制：
    操作以后，最终H的维度和N的维度都保持在4-7之间

    3. 输出规范 (Output Format)
    将你的总结输出为一段内容（500字左右）：
    """
    #--消除（如冗余、误导或与 Ground Truth 冲突的表述），
    # --合并（如语义重叠或可泛化的条目）。
    #--消除（如冗余、误导或与 Ground Truth 冲突的表述），
    # 已有历史经验误判案例
    # {pre0l1_context}
        pre0l1_prompt = f"""你是一个专注于纠正将有害模因误判为无害的模因有害性判别经验总结记忆系统，旨在持续演进与优化判别知识库。
    请基于以下输入进行经验更新：
    各个专家提出的不同建议：
    {pre0l1_summary}
    {additional_cut_prompt}
    执行以下操作：
    综合各个专家的意见形成最核心的两条操作建议：
    ##Note:
    1.建议类型：
    a.新增或删除或合并维度
    b.对某个维度的具体内容进行重写或改写
    c.额外建议 (在prompt维度评估以外需要特别强调的内容：例如 当前打分偏向极端（H全高分，N全地方），需要特别强调独立打分)

    2.维度数量限制：
    操作以后，最终H的维度和N的维度都保持在3-7之间

    3. 输出规范 (Output Format)
    将你的总结输出为一段内容（500字左右）：
    """
        print(f"\n{'='*60}")
        print(f"记忆整合更新")
        print(f"{'='*60}\n")
        print(f"len(system_prompt):{len(pre1l0_prompt)}")
        pre1l0_memory,pre0l1_memory = "",""
        if pre1l0_context_list:
            pre1l0_memory = prediction_saver.get(iteration,f"{error_iteration}_pre1l0_memory")
            if pre1l0_memory == None:
                pre1l0_memory = llm_tool.call_llm(
                    system_prompt=pre1l0_prompt,
                    messages=[{"role": "user", "content": "给出你的总结："}],
                    temperature=1.0
                )
                prediction_saver.save(iteration,f"{error_iteration}_pre1l0_memory",pre1l0_memory)
            safe_append_markdown(RECORD_PATH, f"## pre1l0记忆更新\n**输出:**\n{pre1l0_memory}\n")
        if pre0l1_context_list:
            pre0l1_memory = prediction_saver.get(iteration,f"{error_iteration}_pre0l1_memory")
            if pre0l1_memory == None:
                pre0l1_memory = llm_tool.call_llm(
                    system_prompt=pre0l1_prompt,
                    messages=[{"role": "user", "content": "给出你的总结："}],
                    temperature=1.0
                )
                prediction_saver.save(iteration,f"{error_iteration}_pre0l1_memory",pre0l1_memory)
            safe_append_markdown(RECORD_PATH, f"## pre0l1记忆更新\n**输出:**\n{pre0l1_memory}\n")
        print(f"\n{'='*60}")
        print(f"开始prompt改进")
        print(f"{'='*60}\n")
    else:
        pre0l1_memory = pre0l1_summary
        pre1l0_memory = pre1l0_summary
    if not USE_ERROR_REF:
        pre0l1_memory = "Misclassified samples:\n"+pre0l1_context
        pre1l0_memory = "Misclassified samples:\n"+pre1l0_context
    # 第二步：生成新的prompt
    system_prompt = """
You are a Senior Prompt Optimization Engineer specializing in Harmful Meme Detection.
Your task is to **REWRITE** an existing evaluation prompt to fix specific classification errors identified in recent iterations.
### INPUT CONTEXT
You will receive:
1. The **Original Prompt** (which contains flaws).
2. **Error Analysis Memory** (Specific feedback on False Positives and False Negatives).
3. **Feature Importance** (Ranking of scoring dimensions).
### CRITICAL REWRITING RULES
1. **SUBSTANTIAL REVISION REQUIRED**: 
   - You MUST NOT simply copy-paste the Original Prompt. 
   - You must rephrase instructions, redefine dimensions, and restructure logic based on the Error Analysis.
   - If the Original Prompt says "Analyze X", and the Error Analysis says "X causes confusion", you MUST change how X is analyzed or remove it.
   - Target a text divergence rate of at least 40% from the original while maintaining core intent.
2. **INTEGRATE ERROR FEEDBACK (HIGHEST PRIORITY)**:
   - **False Positives (Harmless -> Harmful)**: Use `pre1l0_memory` to add constraints that prevent over-sensitivity. Clarify boundaries for "safe" content.
   - **False Negatives (Harmful -> Harmless)**: Use `pre0l1_memory` to sharpen criteria for detecting subtle harm, sarcasm, or implied threats.
   - Explicitly incorporate the "Revision Suggestions" from the memory into the new scoring criteria.
3. **DIMENSION MANAGEMENT (Hn / Nn)**:
   - **Do not blindly inherit dimensions.** You need to strictly follow the requirements in *Error Analysis Memory* to add, delete, or rewrite content in the corresponding dimensions.
   - Ensure `harmful_scores` keys strictly follow `H1, H2...` and `harmless_scores` follow `N1, N2...`.
   - The definitions of these dimensions in the prompt text MUST match the JSON output keys exactly.
4. **MITIGATE MODEL FAILURES**:
   - Embed instructions in the new prompt to prevent:
     - **Extreme Scoring**: Force the model to use the full score range (1-9), not just 1 or 9.
     - **Logical Coupling**: Explicitly state that high score in H1 does NOT imply high score in H2.
     - **Instruction Drift**: Keep core constraints concise and repeated at the end.
5. **OUTPUT FORMAT**:
   - Output **ONLY** the raw text of the NEW PROMPT.
   - Do NOT include markdown code blocks (```), explanations, or JSON examples of the meme evaluation.
   - The New Prompt must instruct the evaluator to output JSON with this exact structure:
     {
       "harmful_scores": {"H1": int, "H2": int, ...},
       "harmless_scores": {"N1": int, "N2": int, ...},
       "reasoning": "string"
     }
### TONE AND STYLE
- Authoritative, precise, and unambiguous.
- Use imperative verbs (e.g., "Must", "Verify", "Cross-check").
- Ensure the new prompt is self-contained and does not reference "the previous prompt".
"""
    #   Specific error example：
    #   #####\n{combined_context}\n#####
    if USE_DMEE:
        messages1 = [{"role": "user", 
                   "content": f"""Original prompt:
#####\n{old_prompt}\n#####
**False Positives (Harmless -> Harmful) Error Analysis Memory **:
#####\n{pre1l0_memory}\n#####
**False Negatives (Harmful -> Harmless) Error Analysis Memory** :
#####\n{pre0l1_memory}\n#####
OUTPUT ONLY THE NEW *REWRITE* PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}]
    else:
        messages1 = [{"role": "user", 
                   "content": f"""Original prompt:
analyse:\n\n{pre1l0_memory}\n\n{pre0l1_memory}
#####\n{old_prompt}\n#####
OUTPUT ONLY THE NEW *REWRITE* PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}]
    
    system_prompt = system_prompt
    new_prompt = prediction_saver.get(iteration,f"{error_iteration}_new_prompt")
    if new_prompt==None:
        new_prompt = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=messages1,
            temperature=1.0
        )
        prediction_saver.save(iteration,f"{error_iteration}_new_prompt",new_prompt)
    # para = extract_dict_from_string(new_prompt)
    print(f"🆕 新生成的prompt:")
    print(new_prompt[:500] + "..." if len(new_prompt) > 500 else new_prompt)
    print("\n" + "-"*50 + "\n")
    safe_append_markdown(RECORD_PATH, f"## 新生成的Prompt:\n{new_prompt}\n")
    return {

        "current_prompt": new_prompt,
        # "prompt_history": state.get("prompt_history", []) + [{
        #     'errors': list(state.get("error_errors", [])),
        #     'error_accuracy': state.get("error_accuracy", 0),
        #     'error_summary': error_summary,
        #     "new_prompt": new_prompt,
        #     "new_code": state["current_code"]
        # }],
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