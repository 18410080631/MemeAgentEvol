
---

## 论文文本提取:
```json
{
  "有害标准": {
    "标准1": {
      "内容": "有害的模因可能会对个人、组织、社区或社会造成心理虐待、诽谤、心理生理伤害、财产损害、情感困扰和公众形象受损。",
      "对应原文": "Here, we deﬁne harmful memes as follows: multi-modal units consisting of an image and a piece of text embedded that has the potential to cause harm to an individual, an organization, a community, or the society more generally. Here, harm includes mental abuse, defamation, psycho-physiological injury, proprietary damage, emotional disturbance, and compensated public image."
    },
    "标准2": {
      "内容": "有害的模因可能会以隐晦的方式表达攻击，可能需要批判性判断来确定其造成伤害的潜力。",
      "对应原文": "The harmful content in a harmful meme is often camouﬂaged and might require critical judgment to establish its potential to do harm."
    },
    "标准3": {
      "内容": "有害的模因可以针对多个个体、组织和/或社区，评估时应根据最佳个人判断进行。",
      "对应原文": "One harmful meme can target multiple individuals, organizations, and/or communities at the same time. In that case, we asked the annotators to go with the best personal judgment."
    },
    "标准4": {
      "内容": "有害的模因可能会以讽刺或政治讽刺的形式表达伤害。",
      "对应原文": "Harm can be expressed in the form of sarcasm and/or political satire."
    }
  },
  "无害标准": {
    "标准1": {
      "内容": "无害的模因通常是幽默的，旨在引发笑声，而不针对任何特定的个体或群体。",
      "对应原文": "Memes are typically innocent and designed to look funny."
    },
    "标准2": {
      "内容": "无害的模因不包含任何明显的攻击性内容，且不意图造成心理或情感上的伤害。",
      "对应原文": "Harmful is a more general term than offensive and hateful: offensive and hateful memes are harmful, but not all harmful memes are offensive or hateful."
    },
    "标准3": {
      "内容": "无害的模因不涉及对社会实体的嘲讽或贬低。",
      "对应原文": "For instance, the memes in Figures 1b and 1c are neither offensive nor hateful, but harmful to Donald Trump and to news media such as CNN, respectively."
    },
    "标准4": {
      "内容": "无害的模因不涉及对社会或文化信仰的攻击或贬低。",
      "对应原文": "The harm caused by a meme can be in the form of mental abuse, psycho-physiological injury, proprietary damage, emotional disturbance, compensated public image."
    }
  }
}
```

---

## 全局评估打分:


---

### 样本ID: covid_memes_187
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets the concept of the coronavirus by associating it with a derogatory term ('China Virus'), which implies a specific blame and can be interpreted as harmful. This indicates a high score for H1 due to the direct targeting of a real-world issue. H2 is also high as it promotes stigma and could lead to emotional disturbance. H3 receives a moderate score since the harm is somewhat dependent on both the image and text. For harmless criteria, N1 is low because the meme does target a real entity, and N3 is limited due to the derogatory nature of the term used, which prevents a higher score despite the lack of specific individual targeting."
}


---

### 样本ID: covid_memes_2667
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target a specific individual with derogatory language or factual claims, thus scoring low on harmful dimensions. It uses a general expression of frustration related to the year 2020, which is a common sentiment and does not directly demean anyone. The content is not surreal or fantastical, but it critiques a general situation without naming individuals, allowing for a higher score in harmless dimensions."
}


---

### 样本ID: covid_memes_30
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target a specific individual with derogatory language or factual claims, as it humorously depicts a dog in a fictional scenario. It does not meet the conditions for H2.5 since it does not involve any real person or derogatory terms. The humor is clearly fantastical, focusing on a dog rather than a human, which supports a higher N3 score. Overall, the content is light-hearted and does not promote harm."
}


---

### 样本ID: covid_memes_3856
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 9,
    "N3": 8
  },
  "reasoning": "The meme does not target any specific individual and uses a humorous analogy related to washing hands, which is a general health tip. It does not contain derogatory language or factual claims about any person. The content is clearly fantastical and humorous, focusing on a horse rather than a real person, thus meeting the criteria for satire rather than sarcasm. H2.5 does not apply as there are no derogatory labels or factual claims. The N3 score is high because the content critiques behavior (handwashing) without naming or depicting specific individuals negatively."
}


---

### 样本ID: covid_memes_3832
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 2,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 9,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, thus scoring low on H1. The humor is based on a fictional ranking of social greetings and their chance of infection, which is clearly fantastical and not asserting factual claims about real people, allowing for a higher N3 score. H2 is low as it does not promote real conspiracies or cause significant emotional disturbance. Overall, the content critiques general behavior without naming specific individuals, aligning with satire rather than sarcasm."
}


---

### 样本ID: covid_memes_1506
**打分结果:** {
  "harmful_scores": {
    "H1": 3,
    "H2": 4,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme does not directly target a specific individual with derogatory language, but it does imply a critique of COVID-19 responses, which could be interpreted as harmful. The exaggeration in the meme is not clearly fantastical, and while it critiques behavior, it does not name specific individuals derogatorily. Therefore, H2 is moderate due to the potential for emotional disturbance regarding the topic. N3 is scored moderately high as the content critiques general behavior without naming individuals with derogatory terms."
}


---

### 样本ID: covid_memes_4293
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 3,
    "H2": 4,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme references the COVID-19 pandemic and uses humor to critique misinformation about the virus. It does not directly target a specific individual with derogatory language, but it does imply a critique of the situation. H2.5 does not apply as the content does not meet all conditions. The N3 score reflects that while it critiques behavior related to the pandemic, it does not label any real person derogatorily."
}
```


---

### 样本ID: covid_memes_3922
**打分结果:** {
  "harmful_scores": {
    "H1": 3,
    "H2": 4,
    "H3": 3
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not directly target a specific individual with derogatory language, but it does use a real person's image in a humorous context related to COVID-19 masks. The humor appears to be satirical rather than sarcastic, as it critiques the absurdity of DIY masks during a pandemic. H2.5 does not fully apply because the content does not meet all conditions; while it is exaggerated, it does not completely avoid implications about the target. N3 is scored high because the content is fantastical and critiques general behavior without derogatory terms."
}


---

### 样本ID: covid_memes_1106
**打分结果:** {
  "harmful_scores": {
    "H1": 5,
    "H2": 4,
    "H3": 3
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme targets a specific individual by implying they are no longer young, which can be seen as derogatory, thus scoring H1 moderately high. H2 is also moderate as it could cause emotional disturbance but does not promote real conspiracies. H3 is lower because the harm relies on both image and text. N1 is scored low since a real person is identifiable, and N3 is moderate as it critiques age without using explicit derogatory terms, but it does not meet the conditions for H2.5."
}


---

### 样本ID: covid_memes_3814
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 3,
    "H2": 4,
    "H3": 3
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 9,
    "N3": 6
  },
  "reasoning": "The meme uses a well-known phrase in a humorous context related to COVID-19, which can be interpreted as a critique of behavior during the pandemic rather than a direct attack on an individual. While it does reference a real issue, it does not target a specific person with derogatory language. H2.5 does not apply as the content does not use fantastical elements or exaggeration. The N3 score reflects that the humor is based on a general commentary rather than a specific individual."
}
```


---

### 样本ID: covid_memes_3440
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 7,
    "N2": 1,
    "N3": 6
  },
  "reasoning": "The meme does not target a specific individual but rather comments on a collective experience related to the pandemic. It uses a cartoonish representation of the virus, which aligns with the H2.5 exception, as it does not make factual claims or use derogatory terms. The humor is based on shared frustration rather than sarcasm aimed at individuals, making it more satirical than harmful."
}


---

### 样本ID: covid_memes_432
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 3,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme uses Godzilla, a fictional character, in a hyperbolic scenario to comment on the relative dangers of different threats, which aligns with satire rather than sarcasm. It does not target a specific individual with derogatory language, thus H1 is low. H2 is moderate due to the mention of death statistics, but it does not promote real-world stigma or conspiracy theories. N3 is high because the content is clearly fantastical and critiques general behavior without naming specific individuals derogatorily."
}


---

### 样本ID: covid_memes_419
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets specific individuals (Trump and a Chinese official) by referencing a controversial tweet, which implies factual claims about their actions and reactions. This constitutes direct targeting, leading to a high H1 score. The content promotes a narrative that could cause emotional disturbance, particularly in the context of racial and political tensions, justifying a high H2 score. The multimodal nature of the meme, combining text and images to convey its message, supports a moderate H3 score. The N3 score is low because while the content critiques behavior, it does so by depicting real individuals in a potentially derogatory context, failing to meet the criteria for harmlessness." 
}


---

### 样本ID: covid_memes_262
**打分结果:** {
  "harmful_scores": {
    "H1": 6,
    "H2": 7,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 2
  },
  "reasoning": "The meme targets the concepts of climate change and the pandemic, suggesting they are both fake, which can be interpreted as promoting misinformation. This indicates a moderate level of targeted harm (H1 = 6) and a high level of potential emotional disturbance or defamation (H2 = 7). The multimodal nature of harm is present as the text and image work together to convey the message (H3 = 5). The meme does not meet the criteria for being harmless, as it directly addresses real-world issues without a fantastical or surreal element, leading to low scores in the harmless dimensions."
}


---

### 样本ID: covid_memes_4143
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets individuals by depicting them in a before-and-after format related to a serious health issue, which can be interpreted as derogatory and distressing. This indicates a high score for H1 due to the implicit targeting of real individuals. H2 is also high as it could cause emotional disturbance by trivializing a health crisis. H3 receives a moderate score since the harm is somewhat dependent on both the image and text. N1 is low because real individuals are identifiable, and N3 is limited due to the serious nature of the subject matter, despite the lack of explicit derogatory terms."
}


---

### 样本ID: covid_memes_4276
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 7,
    "N2": 1,
    "N3": 6
  },
  "reasoning": "The meme does not target a specific individual but rather comments on a general behavior (panic buying) during the coronavirus pandemic. It uses humor to critique this behavior without derogatory labels directed at individuals. H2.5 does not apply as the content does not use fictional or exaggerated elements targeting a specific person. The N3 score is appropriate as the content critiques behavior without naming individuals, and it is not presented as factual."
}


---

### 样本ID: covid_memes_576
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 9,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, thus scoring low on harmful dimensions. It depicts a relatable scenario of trying to stay awake during a meeting, which is a common experience and does not involve sarcasm or satire aimed at a specific person. The content is humorous and fantastical in nature, allowing for a higher score in the harmless dimensions, particularly N3, as it critiques a general behavior without naming or depicting specific individuals negatively."
}


---

### 样本ID: covid_memes_422
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets Germany as a personification of the country, implying a malicious intent through the context of historical events. This indicates a high score for H1 due to the direct association with Germany's past. H2 is also high as it suggests a negative connotation regarding current global issues, which could lead to emotional disturbance. H3 scores moderately since the image and text work together to convey a message. N1 is low because Germany is identifiable, and N3 is limited due to the serious nature of the content, despite it being presented in a humorous format."
}


---

### 样本ID: covid_memes_563
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 5,
    "H3": 6
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets a specific individual, Scott Morrison, implying a negative connotation about hygiene through the phrase 'wash your hands like you just shook hands with.' This suggests a derogatory implication, thus scoring high on H1. H2 is also elevated due to the potential emotional disturbance caused by the implication of uncleanliness associated with the individual. H3 is scored moderately high as the image and text work together to convey the message. N1 is low because a specific individual is identifiable, and N3 is limited due to the negative implication directed at the individual."
}


---

### 样本ID: covid_memes_5219
**打分结果:** {
  "harmful_scores": {
    "H1": 6,
    "H2": 5,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 4
  },
  "reasoning": "The meme appears to target a specific individual, suggesting a situation where they cannot travel, which implies a negative context. This indicates a moderate level of harmfulness (H1 = 6). The form of harm (H2) is present as it could cause emotional disturbance, but it does not promote real conspiracies, leading to a score of 5. The multimodal nature of harm (H3) is also moderate, as the image and text work together to convey a negative implication. For harmless criteria, N1 is low because a real individual is identifiable, and N3 is moderate as it critiques behavior without using derogatory terms, but it does not meet the conditions for high scores due to the identifiable nature of the target."
}


---

### 样本ID: covid_memes_2226
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets a specific individual, Donald Trump, and makes factual claims about his actions regarding the military draft, which qualifies as direct targeting (H1 score of 7). The content could cause emotional disturbance and is likely to be interpreted as derogatory, leading to a moderate score for H2. The multimodal nature of harm is present as both the image and text work together to convey the message (H3 score of 5). For harmless criteria, N1 is low because a real individual is targeted, and N3 is also low due to the factual claims made about Trump, which do not meet the criteria for being fantastical or surreal."
}
```


---

### 样本ID: covid_memes_3330
**打分结果:** {
  "harmful_scores": {
    "H1": 5,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 4
  },
  "reasoning": "The meme references historical plague outbreaks and connects them to the COVID-19 pandemic, which could be interpreted as targeting the pandemic itself rather than a specific individual. However, the mention of 'Chinese Coronavirus' introduces a derogatory element that could be seen as harmful. The humor relies on historical context and exaggeration, but it does imply a factual claim about the virus's origin, which affects the H2 score. The surreal imagery of the plague doctor mask adds a layer of satire, but the derogatory label prevents a higher N3 score."
}


---

### 样本ID: covid_memes_1960
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, thus scoring low on harmful dimensions. It uses humor related to the concept of quarantine, which is a general commentary rather than a personal attack. The content is fantastical in nature, as it humorously reflects on lifestyle changes without making factual claims about any real person, allowing for a higher score in the harmless dimensions."
}


---

### 样本ID: covid_memes_4960
**打分结果:** {
  "harmful_scores": {
    "H1": 3,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 6
  },
  "reasoning": "The meme humorously contrasts two states of being while working from home, depicting a transformation that is exaggerated and fantastical. It does not use derogatory language or factual claims about the individuals depicted. Therefore, it does not meet the criteria for high harmful scores. H2.5 applies as the content is clearly fantastical and does not promote real-world stigma. The N3 score is appropriate as it critiques general behavior without naming or depicting specific individuals with derogatory terms."
}


---

### 样本ID: covid_memes_265
**打分结果:** {
  "harmful_scores": {
    "H1": 7,
    "H2": 6,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets a specific situation related to the COVID-19 pandemic, implying harm to individuals in China, which aligns with harmful criteria. It uses derogatory implications about the impact of the virus on businesses, thus scoring high on H1 and H2. The multimodal nature of the meme, combining text and imagery, contributes to the overall harmfulness, reflected in H3. N3 is low because it critiques a specific situation without naming individuals, but it still carries a negative connotation. The meme does not meet the H2.5 exception as it does not use fantastical elements and makes a factual claim about the virus's impact." 
}


---

### 样本ID: covid_memes_2658
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 2,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not directly target a specific individual with derogatory language, but it does reference a common parenting scenario, which could imply a critique of parenting behavior. The humor is based on a relatable situation rather than sarcasm aimed at a specific person, making it more satirical. H2.5 does not apply as the content does not use fantastical elements or exaggeration. The N3 score is high because the content critiques general behavior without naming or depicting specific individuals derogatorily."
}
```


---

### 样本ID: covid_memes_4879
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, making H1 score low. H2 is also low as there is no defamation or emotional disturbance present. The humor is based on a relatable work-from-home scenario, which does not assert anything factual about a specific person. N1 scores high since no identifiable social entity is targeted. N3 is scored moderately high as the content is humorous and critiques general behavior without naming or depicting specific individuals derogatorily."
}


---

### 样本ID: covid_memes_2945
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 9,
    "N3": 9
  },
  "reasoning": "The meme uses a humorous comparison of expectations versus reality regarding working from home, featuring dogs in both scenarios. It does not target any specific individual, nor does it use derogatory language. The content is clearly fantastical and light-hearted, making it harmless. H2.5 does not apply as there are no factual claims or derogatory labels. The N3 score is high because the meme critiques a general situation without naming or depicting specific individuals negatively."
}


---

### 样本ID: covid_memes_2461
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 7,
    "H2": 5,
    "H3": 6
  },
  "harmless_scores": {
    "N1": 2,
    "N2": 1,
    "N3": 3
  },
  "reasoning": "The meme targets a specific individual (President Trump) and uses derogatory language, which aligns with H1 scoring high. H2 is moderate due to the potential for emotional disturbance related to the political context. H3 is scored moderately high as the image and text work together to convey a message. N1 is low because a real individual is identifiable, and N3 is also low due to the presence of a real person depicted with a derogatory sentiment."
}
```


---

### 样本ID: covid_memes_874
**打分结果:** {
  "harmful_scores": {
    "H1": 3,
    "H2": 4,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme uses a play on words involving 'Corona Virus' and a beer brand, which can be interpreted as a humorous take rather than a direct insult. It does not target a specific individual with derogatory language, but it does reference a real-world issue (the pandemic) in a lighthearted manner. H2.5 does not apply as the content does not meet all conditions; it references a real virus, which could be seen as promoting stigma. The N3 score reflects that while it critiques a general behavior (associating a virus with a location), it does so in a fantastical manner without derogatory labels, hence a moderate score." 
}


---

### 样本ID: covid_memes_3277
**打分结果:** {
  "harmful_scores": {
    "H1": 5,
    "H2": 4,
    "H3": 3
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme targets a specific individual ('Karen from Facebook') in a way that implies ridicule, which aligns with sarcasm rather than satire. While it does not use overtly derogatory language, it suggests that the individual is not a credible expert, which can be harmful. H2.5 does not apply as the conditions are not fully met; the content does not use fantastical exaggeration and does imply a factual claim about the individual's expertise. The N3 score reflects that while there is some harm, it critiques a general behavior (misinformation) without labeling the individual with derogatory terms."
}


---

### 样本ID: covid_memes_2899
**打分结果:** {
  "harmful_scores": {
    "H1": 2,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme uses humor to critique the concept of working from home, particularly in the context of archeologists, without targeting a specific individual with derogatory language. It does not assert factual claims about any real person, making it more satirical than sarcastic. H2.5 does not apply as the content does not meet all conditions. The N3 score is high because the humor is clearly fantastical and critiques a general behavior rather than targeting an individual."
}


---

### 样本ID: covid_memes_775
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 5,
    "H2": 4,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 4
  },
  "reasoning": "The meme targets a political group (Democrats) and implies a negative outcome regarding their assumption of office, which can be interpreted as a critique of their effectiveness. This suggests a moderate level of harmfulness (H1 = 5) due to the direct targeting of a political entity. H2 is scored as 4 because it implies emotional disturbance regarding the pandemic's end, but does not promote real conspiracies. H3 is scored as 5 since the image and text work together to convey the message. For harmless criteria, N1 is 3 as it targets a group rather than an individual, N2 is 1 since the text is readable, and N3 is 4 because it critiques behavior without using derogatory terms."
}
```


---

### 样本ID: covid_memes_2870
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, making it harmless in that regard. It humorously depicts the experience of working from home without any malice or insult, aligning more with satire than sarcasm. The content is relatable and critiques a general behavior (working from home) without naming or depicting specific individuals. Therefore, H2.5 does not apply, and the N3 score reflects the absence of harm due to the fantastical and humorous nature of the meme."
}


---

### 样本ID: covid_memes_4780
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 3,
    "H2": 3,
    "H3": 4
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 9,
    "N3": 7
  },
  "reasoning": "The meme features a character known for saying 'MY PRECIOUS!' which is a fictional reference, thus it does not directly target a real individual with derogatory language. The use of a fictional character allows for a score of 6 in N1, as it does not identify a real social entity. H1 is scored lower due to the indirect nature of the reference, while H2 is also moderate as it does not promote real harm but could imply emotional disturbance. N3 is high because the content is fantastical and does not make factual claims about a real person."
}
```


---

### 样本ID: covid_memes_4930
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 9,
    "N3": 7
  },
  "reasoning": "The meme does not target a specific individual with derogatory language or factual claims, thus scoring low on harmful dimensions. It critiques a general behavior related to a restaurant's food presentation, which is humorous rather than malicious. The content is not surreal or fantastical, but it does not contain derogatory terms, allowing for a higher score in N3. Overall, it leans towards harmless satire rather than harmful sarcasm."
}


---

### 样本ID: covid_memes_4153
**打分结果:** ```json
{
  "harmful_scores": {
    "H1": 2,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not directly target a specific individual with derogatory language, thus scoring low on H1. H2 is moderate as it does not promote real conspiracies but may cause mild emotional disturbance. H3 is low since the harm does not rely heavily on the combination of image and text. N1 scores higher as it does not identify a real social entity. N3 is high because the content is humorous and critiques a general behavior without derogatory terms, fitting the criteria for fantastical humor."
}
```


---

### 样本ID: covid_memes_938
**打分结果:** {
  "harmful_scores": {
    "H1": 1,
    "H2": 1,
    "H3": 1
  },
  "harmless_scores": {
    "N1": 9,
    "N2": 1,
    "N3": 7
  },
  "reasoning": "The meme does not target any specific individual with derogatory language or factual claims, thus scoring low on harmful dimensions. It humorously discusses the pros of social distancing in a light-hearted manner, making it more of a satire than sarcasm. The content is fantastical in its exaggeration of social distancing benefits, and while it mentions personal grooming and habits, it does not label anyone negatively. Therefore, N3 is scored high as the harm is negligible and the content is not directed at any real person."
}


---

### 样本ID: covid_memes_2984
**打分结果:** {
  "harmful_scores": {
    "H1": 5,
    "H2": 4,
    "H3": 5
  },
  "harmless_scores": {
    "N1": 3,
    "N2": 1,
    "N3": 5
  },
  "reasoning": "The meme targets a specific group (rappers) in a potentially derogatory manner by implying incompetence in a serious context (virus screening). While it does not directly insult an identifiable individual, it uses a real-world scenario that could be interpreted as mocking. The humor appears to be satirical rather than sarcastic, as it critiques the absurdity of the situation rather than targeting a specific person with malice. H2.5 does not apply as the conditions are not fully met. The N3 score reflects that while there is some harm, it is not severe due to the lack of direct derogatory labeling."
}


---

### 样本ID: covid_memes_1708
**打分结果:** {
  "harmful_scores": {
    "H1": 2,
    "H2": 3,
    "H3": 2
  },
  "harmless_scores": {
    "N1": 6,
    "N2": 1,
    "N3": 6
  },
  "reasoning": "The meme does not directly target a specific individual with derogatory language, but it does imply a critique of horse enthusiasts in a humorous context. The use of a fictional character (Big Bird) adds a layer of absurdity, making it more satirical than sarcastic. H2.5 does not fully apply as the content does not meet all conditions, particularly regarding the absence of derogatory labels. The N3 score is appropriate as the content critiques behavior without naming specific individuals derogatorily, and the fantastical element of using a character contributes to its harmlessness."
}


---

## 全局评估结果
**性能指标:** {'accuracy': 0.75, 'f1': 0.7333333333333334}
**逻辑回归公式:** Logit = 0.304 * H1 - 0.034 * H2 - 0.205 * H3 - 0.087 * N1 - 0.033 * N2 - 0.272 * N3 + 1.231
**特征重要性:** [{'feature': 'H1', 'abs_weight': 0.712667082928559}, {'feature': 'H2', 'abs_weight': 0.061618023074065824}, {'feature': 'H3', 'abs_weight': 0.36437355440961977}, {'feature': 'N1', 'abs_weight': 0.23799641552339812}, {'feature': 'N2', 'abs_weight': 0.09897607886477525}, {'feature': 'N3', 'abs_weight': 0.4780482211328994}]


---

## 首次全局评估结果
**准确率:** 75.00%,f1:0.7333333333333334
**错误样本数:** 10
**将无害模因误判为有害数量:** 5
**将有害模因误判为无害数量:** 5


---

## 错误分析:
需要分析的错误样本数: 10
随机选择的预1l0样本ID: ['covid_memes_3330', 'covid_memes_775', 'covid_memes_1106']
随机选择的预0l1样本ID: ['covid_memes_4930', 'covid_memes_874', 'covid_memes_3922']

