# config.py
import os
from typing import Final
FHM_text = """```json\n{\n  "有害标准": {\n    "标准1": {\n      "内容": "直接或间接攻击基于特征的人群，包括种族、性别、性取向等。",\n      "对应原文": "A direct or indirect attack on people based on characteristics, including ethnicity, race, nationality, immigration status, religion, caste, sex, gender identity, sexual orientation, and disability or disease."\n    },\n    "标准2": {\n      "内容": "攻击的定义包括暴力或非人化的言论，比较人类与非人类事物。",\n      "对应原文": "We define attack as violent or dehumanizing (comparing people to non-human things, e.g. animals) speech, statements of inferiority, and calls for exclusion or segregation."\n    },\n    "标准3": {\n      "内容": "嘲弄仇恨犯罪也被视为仇恨言论。",\n      "对应原文": "Mocking hate crime is also considered hate speech."\n    },\n    "标准4": {\n      "内容": "攻击不基于受保护特征的个人或名人是允许的。",\n      "对应原文": "Attacking individuals/famous people is allowed if the attack is not based on any of the protected characteristics listed in the definition."\n    }\n  },\n  "无害标准": {\n    "标准1": {\n      "内容": "文本和图像的组合不构成仇恨，且不包含任何攻击性内容。",\n      "对应原文": "if we replaced the skunk and tumbleweed images with pictures of roses or people, the memes become harmless again."\n    },\n    "标准2": {\n      "内容": "文本或图像的替换能够将标签从仇恨转变为非仇恨。",\n      "对应原文": "A benign confounder is a minimum replacement image or replacement text that flips the label for a given multimodal meme from hateful to non-hateful."\n    },\n    "标准3": {\n      "内容": "不包含任何自我伤害、儿童剥削、暴力呼吁等内容的图像被视为无害。",\n      "对应原文": "Memes were considered violating if they contained any of the following: self injury or suicidal content, child exploitation or nudity, calls to violence."\n    },\n    "标准4": {\n      "内容": "文本和图像的组合在语义上保持无害。",\n      "对应原文": "an image (or set of images) is a suitable replacement if and only if, when overlaid with the meme’s text, it preserves the meaning and intent of the original meme."\n    }\n  }\n}\n"""
HARM_text = """```json\n{\n  "有害标准": {\n    "标准1": {\n      "内容": "有害的模因可能会对个人、组织、社区或社会造成心理虐待、诽谤、心理生理伤害、财产损害、情感困扰和公众形象受损。",\n      "对应原文": "Here, we deﬁne harmful memes as follows: multi-modal units consisting of an image and a piece of text embedded that has the potential to cause harm to an individual, an organization, a community, or the society more generally. Here, harm includes mental abuse, defamation, psycho-physiological injury, proprietary damage, emotional disturbance, and compensated public image."\n    },\n    "标准2": {\n      "内容": "有害的模因可能会以隐晦的方式表达攻击，可能需要批判性判断来确定其造成伤害的潜力。",\n      "对应原文": "The harmful content in a harmful meme is often camouﬂaged and might require critical judgment to establish its potential to do harm."\n    },\n    "标准3": {\n      "内容": "有害的模因可以针对多个个体、组织和/或社区，评估时应根据最佳个人判断进行。",\n      "对应原文": "One harmful meme can target multiple individuals, organizations, and/or communities at the same time. In that case, we asked the annotators to go with the best personal judgment."\n    },\n    "标准4": {\n      "内容": "有害的模因可能会以讽刺或政治讽刺的形式表达伤害。",\n      "对应原文": "Harm can be expressed in the form of sarcasm and/or political satire."\n    }\n  },\n  "无害标准": {\n    "标准1": {\n      "内容": "无害的模因通常是幽默的，旨在引发笑声，而不针对任何特定的个体或群体。",\n      "对应原文": "Memes are typically innocent and designed to look funny."\n    },\n    "标准2": {\n      "内容": "无害的模因不包含任何明显的攻击性内容，且不意图造成心理或情感上的伤害。",\n      "对应原文": "Harmful is a more general term than offensive and hateful: offensive and hateful memes are harmful, but not all harmful memes are offensive or hateful."\n    },\n    "标准3": {\n      "内容": "无害的模因不涉及对社会实体的嘲讽或贬低。",\n      "对应原文": "For instance, the memes in Figures 1b and 1c are neither offensive nor hateful, but harmful to Donald Trump and to news media such as CNN, respectively."\n    },\n    "标准4": {\n      "内容": "无害的模因不涉及对社会或文化信仰的攻击或贬低。",\n      "对应原文": "The harm caused by a meme can be in the form of mental abuse, psycho-physiological injury, proprietary damage, emotional disturbance, compensated public image."\n    }\n  }\n}\n```"""
MAMI_text = """```json\n{\n  "有害标准": {\n    "标准1": {\n      "内容": "模因包含对女性的侮辱性或攻击性内容，直接表达对女性的仇恨或偏见。",\n      "对应原文": "A meme is misogynous if it conceptually describes an offensive, sexist or hateful scene (weak or strong, implicitly or explicitly) having as target a woman or a group of women."\n    },\n    "标准2": {\n      "内容": "模因涉及对女性的身体或性别特征的羞辱，例如身体羞辱或性别刻板印象。",\n      "对应原文": "These types of misogynous memes are related to denigrating the physical appearance of women (body shaming)."\n    },\n    "标准3": {\n      "内容": "模因表现出对女性的物化，视女性为物品或仅仅是身体的存在。",\n      "对应原文": "It is a practice of seeing and/or treating a woman like an object."\n    },\n    "标准4": {\n      "内容": "模因暗示或直接呼吁对女性的暴力行为。",\n      "对应原文": "These types of misogynous memes are aimed at showing violence against women or at alluding to the intent of physically assert power over women."\n    }\n  },\n  "无害标准": {\n    "标准1": {\n      "内容": "模因不包含任何针对女性的仇恨、偏见或攻击性内容。",\n      "对应原文": "A meme is NOT misogynous if it is conceptually not related to women or even if it is related to women, but it does not represent an offensive, sexist or hateful concept against women."\n    },\n    "标准2": {\n      "内容": "模因的内容与女性无关，或仅仅是中立的描述，没有任何贬低或攻击的意图。",\n      "对应原文": "A meme that does not express any form of hate against women."\n    },\n    "标准3": {\n      "内容": "模因可能包含幽默或讽刺的元素，但不涉及对女性的贬低或物化。",\n      "对应原文": "Although many memes are created with humorous intent, others have political or activist ambitions."\n    }\n  }\n}\n```"""
TASK_FHM_J_H = """
### A meme is harmful if and only if all of the following conditions are met:  
*H1*:Targeted Attack on Protected Groups:  
The combined image and text constitute a direct or indirect attack on people based on one or more of the following protected characteristics:  
(1) Race, ethnicity, or nationality  
(2) Immigration status  
(3) Religion  
(4) Caste  
(5) Sex, gender identity, or sexual orientation  
(6) Disability or disease  
*H2*:Form of Attack Includes At Least One of the Following:  
(1) Dehumanization: Comparing people to animals, objects, or non-human entities (e.g., implying a group “smells like a skunk” to degrade them).  
(2) Statements of Inferiority: Claiming a group is inherently lesser, dirty, dangerous, or unworthy.  
(3) Calls for Exclusion or Segregation: Advocating that a group be banned, isolated, or removed from society.  
(4) Mocking Hate Crimes: Making light of violence or discrimination against protected groups.  
*H3*:Multimodal Dependency:  
(1) The harmful meaning only emerges from the combination of image and text.  
(2) If you replace the image with a semantically similar but neutral alternative (e.g., swap a skunk for a rose), the meme becomes harmless.  
(3) If you replace the text with a neutral but contextually plausible alternative (e.g., change “Love the way you smell today” to “Skunks have a strong odor”), the meme becomes harmless.  
(4) If the meme remains harmful when either modality is removed or replaced, it may be unimodally harmful—but for this task, we focus on truly multimodal harm.  
### A meme is harmless if any of the following is true:  
*N1*:No Attack on Protected Groups:  
The content does not target any group based on the protected characteristics listed above.  
*N2*:Falls Under Explicit Exceptions:  
(1) It criticizes or mocks specific individuals or public figures (e.g., politicians, celebrities), provided the criticism is not based on their protected characteristics.  
(2) It condemns or ridicules groups that promote hate or violence (e.g., terrorist organizations, white supremacist groups)—this is not considered harmful.  
*N3*:Lacks Combined Harmful Intent:  
(1) The text alone is benign (e.g., “Look how many people love you”).  
(2) The image alone is benign (e.g., a tumbleweed, a skunk, or a crowd).  
(3) Only when combined do they potentially imply mockery or exclusion—but if that implication does not meet the criteria for dehumanization, inferiority, or exclusion, it remains harmless.  
*N4*:Neutral or Factual Statements:  
Descriptive, humorous, or ironic statements that do not demean or attack a protected group (e.g., “Skunks have a very particular smell”) are harmless, even if paired with relevant imagery.  
### Important Instructions: 
① Do not classify based on keywords alone (e.g., the word “black” or an image of a religious symbol is not automatically harmful).  
② Consider real-world context and implied meaning, not just literal content.  
③ The presence of benign confounders confirms multimodal nuance: if changing either the image or text flips the meaning to non-harmful, then the original must be evaluated as a unified whole.  
④ When in doubt, ask: “Would a reasonable person interpret this as an attack on a protected group based on who they are—not what they believe or do?”  
### Scoring Protocol (Mandatory)
Evaluate the meme along harmless criteria frameworks: . Assign a score from **1 to 9** for each primary dimension below (1 = completely absent, 9 = fully and clearly present).
> **Notice:  
> - Score **objectively**—a harmless meme can still have moderate H2/H3 scores if it flirts with ambiguity.  
> - N1 and H1 are generally inversely related, but both can be low in unclear cases.  
> - High N2 (e.g., ridiculing Nazis) overrides high H1/H2.
### Scoring Protocol (Mandatory)
Evaluate the meme along harmful criteria frameworks: . Assign a score from **1 to 9** for each primary dimension below (1 = completely absent, 9 = fully and clearly present).
Note that your role is not to judge whether the meme is harmful or harmless, but to score the meme on each evaluation dimension based on how well it satisfies the criteria of that dimension.
```json
{
"harmful_scores": {
    "H1": int,
    "H2": int,
    "H3": int
  },
"harmless_scores": {
    "N1": int,
    "N2": int,
    "N3": int,
    "N4": int
  }
"reasoning": "Explaining which pathway dominates and why, referencing key scores."
}
Do not output anything outside the JSON block.
"""

TASK_HARM_J_H = """
You are an expert evaluator tasked with scoring a meme along six predefined dimensions based on the HarMeme annotation guidelines (ACL-IJCNLP 2021). Your role is **NOT** to output a final 'harmful' or 'harmless' label, but to assign a score from 1 to 9 for each dimension, where 1 = completely absent and 9 = fully and clearly present.
**Critical Instructions Before Scoring:**
1. **Distinguish Sarcasm vs. Satire (CRITICAL)**
   - **Sarcasm**: "Praise that is actually an insult; generally involves malice, the desire to put someone down"  
     (e.g., calling a specific person "the village idiot")
   - **Satire**: "Ironical exposure of the vices or follies of an individual, group, or institution, usually with the aim of correcting it"
   - **Sarcasm targeting specific individuals is HARMFUL**; **satire using fictional/exaggerated elements is generally HARMLESS**
2. **H2.5 Exception – Applies ONLY when ALL conditions are met:**
   - The content uses **fictional, surreal, hyperbolic, or cartoonish exaggeration**  
     (e.g., depicting a person as a monster, alien, or zombie)
   - The meme makes **NO factual or pseudo-factual claims** about the target  
     (e.g., "this is what Trump actually looks like")
   - The content **does not directly label the target with derogatory terms**  
     (e.g., "idiot," "liar")
   - The exaggeration is **clearly fantastical** and not presented as reality
   - The meme **does not promote real-world stigma or conspiracy theories**  
   → If **ANY** condition fails, **H2.5 does NOT apply**
3. **Targeting Specific Individuals:**
   - Using a real person's image with a derogatory label (e.g., "village idiot") = **DIRECT TARGETING** (H1 high)
   - Using a real person's image with fictional transformation (e.g., "will become a monster") = **INDIRECT TARGETING** (H1 moderate)
   - Using a real person's image for general commentary without derogatory labels = **POTENTIALLY HARMLESS**
4. **Context Matters:**
   - Ask: *"Is this meme asserting something as factual about the target, or is it clearly fantastical humor?"*
   - Ask: *"Could a reasonable person interpret this as directly demeaning a specific individual?"*
**Scoring Dimensions:**
**Harmful Criteria:**
- **H1: Targeted Entity Existence**  
  Score high if the meme explicitly/implicitly targets a specific real individual with derogatory language or factual claims.
- **H2: Form of Harm**  
  Score high if it causes defamation, emotional disturbance, or promotes real conspiracies.  
  ⚠️ **Apply H2.5 strictly**: Only score H2 ≤ 4 if **ALL H2.5 conditions are met**.
- **H3: Multimodal Nature of Harm**  
  Score high if harm depends on **BOTH image and text working together**.
**Harmless Criteria:**
- **N1: No Targeted Entity**  
  Score high **ONLY** if no real social entity is identifiable or targeted with derogatory language.
- **N2: Rejection Criteria Met**  
  Score high **only** if the meme is non-English, unreadable, unimodal, or hand-drawn cartoon.
- **N3: Harm is Absent or Negligible**  
  Score high **ONLY** if:
    - The content is clearly fantastical/surreal with **NO factual claims**, **OR**
    - It critiques general behavior without naming/depicting specific individuals with derogatory terms.  
  → **If a real person is depicted AND labeled with a derogatory term (e.g., "idiot"), N3 ≤ 3.**  
  → **If a real person is depicted but transformed FANTASTICALLY with NO derogatory labels, N3 ≥ 6.**
**Output Format (STRICT JSON):**
{
  "harmful_scores": {
    "H1": int,
    "H2": int,
    "H3": int
  },
  "harmless_scores": {
    "N1": int,
    "N2": int,
    "N3": int
  },
  "reasoning": "Concise explanation distinguishing between sarcasm (harmful) and satire (harmless), explaining H2.5 applicability, and why N3 score is appropriate for this specific meme."
}
"""


TASK_MAMI_J_H = """
You are an expert evaluator tasked with scoring a meme along predefined dimensions based on the MAMI annotation guidelines (SemEval-2022 Task 5). Your role is **NOT** to output a final 'misogynous' or 'not misogynous' label, but to assign a score from 1 to 9 for each dimension, where 1 = completely absent and 9 = fully and clearly present.
**Critical Instructions Before Scoring:**
1. **Core Definition (MAMI Sub-task A)**  
   - **Misogynous (Harmful)**: "a meme is misogynous if it conceptually describes an offensive, sexist or hateful scene (weak or strong, implicitly or explicitly) having as target a woman or a group of women"  
   - **Not Misogynous (Harmless)**: a meme that does not express any form of hate against women — either because it is unrelated to women, or because it relates to women but does not convey offensive, sexist, or hateful concepts against them.
2. **Implicit vs. Explicit Harm (MAMI annotation principle)**  
   - Harm may be conveyed **implicitly** (e.g., visual suggestion + neutral text) or **explicitly** (e.g., direct derogatory label). Both count toward harmful scoring if the target is women.

3. **Multimodal Dependency (MAMI core premise)**  
   - The offensive/sexist/hateful meaning may emerge **only when image AND text are interpreted together**. This is a key design principle of MAMI and must be explicitly evaluated.

4. **Contextual Disambiguation**  
   - Ask: *"Could a reasonable person interpret this as offensive, sexist, or hateful toward women (as individuals or as a group)?"*  
   - Ask: *"Is the negative content about women presented as factual assertion, or as clearly absurdist/fictional humor with no real-world harmful implication?"*  
   - Ask: *"Does the meme critique gender norms or social issues without targeting women with derogatory framing?"* → If yes, lean toward harmless.

**Scoring Dimensions:**

**Harmful Criteria (Misogynous):**
- **H1: Targeted Entity Existence**  
  Score high if the meme explicitly or implicitly targets women (as individuals or as a group) with offensive, sexist, or hateful framing. Per MAMI: "having as target a woman or a group of women".

- **H2: Offensive/Sexist/Hateful Content**  
  Score high if the meme conveys content that is offensive, sexist, or hateful toward women — whether **implicit or explicit** (per MAMI annotation guidelines). No need to distinguish subtypes (shaming/stereotype/objectification/violence); evaluate overall harmful intent.

- **H3: Multimodal Nature of Harm**  
  Score high if the misogynous meaning depends on **BOTH image and text working together** (e.g., neutral text + suggestive image, or vice versa). This reflects MAMI's core multi-modal design principle.

**Harmless Criteria (Not Misogynous):**
- **N1: No Targeted Entity**  
  Score high **ONLY** if no woman or female group is identifiable or targeted with derogatory framing.

- **N2: Rejection Criteria Met**  
  Score high **only** if the meme meets MAMI's filtering conditions: non-English, unreadable, unimodal (text-only or image-only without meaningful combination), or clearly hand-drawn cartoon without realistic depiction.

- **N3: Harm is Absent or Negligible**  
  Score high **ONLY** if:
    - The content is clearly fantastical/surreal with **NO factual claims about women**, **OR**
    - It critiques gender norms, patriarchal structures, or social issues **without depicting/labeling specific women with offensive, sexist, or hateful framing**.  
  → **If a real woman is depicted AND labeled with a derogatory term, N3 ≤ 3.**  
  → **If a woman is depicted but in a clearly fictional/fantastical context with NO derogatory framing, N3 ≥ 6.**

**Output Format (STRICT JSON):**
{
  "harmful_scores": {
    "H1": int,
    "H2": int,
    "H3": int
  },
  "harmless_scores": {
    "N1": int,
    "N2": int,
    "N3": int
  },
  "reasoning": "Concise explanation per MAMI guidelines: (1) whether the meme targets women with offensive/sexist/hateful content (implicit/explicit), (2) whether harm emerges from image-text interaction, (3) why N3 score is appropriate given the presence/absence of derogatory framing or fantastical context."
}
"""

JUDGE_SCORE = """
def classify_meme(scores):
    harmful_scores = scores["harmful_scores"]
    harmless_scores = scores["harmless_scores"]
    max_harmful = max(harmful_scores.values())
    max_harmless = max(harmless_scores.values())
    if max_harmful >= max_harmless:
        return 'harmful'
    else:
        return 'harmless'
"""

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-d2e7a6ce8c2d425ab5498a77b7f1c7ac") # sk-nXhyMEwSWPyCh94GBeXr6kdeIsbP2euit1vrCQPM5Xw4Awge
# OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")  # https://api.chatanywhere.tech/v1
# MODEL_NAME = 'qwen3-vl-flash'  #
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-nXhyMEwSWPyCh94GBeXr6kdeIsbP2euit1vrCQPM5Xw4Awge") # sk-nXhyMEwSWPyCh94GBeXr6kdeIsbP2euit1vrCQPM5Xw4Awge sk-aFthrMPCNNtUreZpql2B0C2BxylbzRwxgRwrn6wsjkRJn4ac
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.chatanywhere.tech/v1")  # https://api.chatanywhere.tech/v1
MODEL_NAME = 'gpt-4o-mini'  # gpt-4o-mini
MAX_ITERATIONS: Final[int] = 10
DATASET_NAME = "FHM"  # Options: "FHM", "MAMI", "HARM"
RECORD_PATH = "records.md"
DATASET_NUM = 40
THRESHOLD = 0.95
error_focus_threshold = 0.3
dim_importance_threshold = 0.1
USE_LMCL = True
USE_DMEE = True
