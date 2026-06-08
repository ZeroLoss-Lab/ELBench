# ELBench: A Holistic Benchmark for Education-Facing Large Language Models

## Abstract

Large language models are increasingly used as tutors, teaching assistants, content generators, and educational advisors. Existing benchmarks, however, often evaluate general capability, safety, and educational quality separately, making it difficult to assess whether a model is suitable for education-facing deployment. We introduce ELBench, a four-module benchmark that evaluates large language models across General Capability, Safety and Trustworthiness, Basic Education, and High-Level Educational Alignment. ELBench contains 2,942 samples per reported model and combines reference-based, rule-based, and rubric-based evaluation. We evaluate nine representative models under a zero-shot deterministic protocol. The results show that model performance differs substantially across modules: Claude Opus 4.8 achieves the highest overall score, Gemini 3.5 Flash leads General Capability and High-Level Educational Alignment, and DeepSeek V4 Flash leads Safety and Trustworthiness. No reported model dominates all four modules. These findings indicate that education-facing model selection should rely on module-level profiles rather than a single general benchmark score. ELBench provides a structured benchmark for analyzing the capability, safety, and educational alignment trade-offs that arise in educational deployment.

## 1. Introduction

Large language models are increasingly used in educational settings as tutors, teaching assistants, content generators, and learning advisors. These uses differ from ordinary question answering. An education-facing model must answer accurately, but it must also respond safely, guide students appropriately, and produce outputs that align with instructional goals. A model that performs well on general reasoning benchmarks may still give unsafe advice, mishandle a student's misconception, or fail to produce usable teaching materials. Conversely, a strongly safety-aligned model may be too conservative or too weak instructionally for classroom support. Educational deployment therefore requires evaluation across several dimensions rather than a single capability score.

Existing benchmarks provide important but partial views of this problem. General evaluation suites such as HELM and BIG-bench demonstrate the value of broad model evaluation across tasks and metrics \cite{liang2022helm,srivastava2022bigbench}. Safety benchmarks such as SafetyBench formalize risk categories and refusal behavior \cite{zhang2024safetybench}. Chinese and disciplinary benchmarks such as C-Eval show that language and subject coverage matter for reliable model comparison \cite{huang2023ceval}. Recent educational benchmarks further move evaluation toward classroom tasks, tutoring scenarios, and pedagogical risks \cite{xu2025edubench,k12edubench2026,jiang2026eduguardbench}. These lines of work are complementary, but they usually evaluate capability, safety, and educational quality separately. As a result, they do not directly answer which models are suitable for education-facing deployment when these requirements must be satisfied together.

We introduce ELBench, a four-dimensional benchmark for evaluating large language models in education-facing settings. ELBench integrates general capability, safety and trustworthiness, basic education, and high-level educational alignment into one evaluation framework. The general capability module measures knowledge, reasoning, mathematical problem solving, and instruction following. The safety and trustworthiness module measures refusal, safe guidance, benign answering, teaching-safety awareness, and adversarial safety. The basic education module evaluates practical teaching behaviors such as knowledge explanation, contextualized question generation, interdisciplinary lesson planning, and guided problem solving. The high-level education module evaluates broader educational decision making and alignment with pedagogical expectations.

The current benchmark contains 2,942 samples per reported model, including 897 general capability samples, 1,000 safety and trustworthiness samples, 45 basic education samples, and 1,000 high-level education samples. Following the reporting style of EduGuardBench, all experiments are conducted in a zero-shot setting with greedy decoding or temperature 0 to ensure deterministic and reproducible results \cite{jiang2026eduguardbench}. We evaluate nine representative models spanning international frontier models, Chinese frontier models, and education- or safety-oriented models. The evaluation is designed to report both aggregate scores and module-level profiles, because the latter are essential for interpreting deployment trade-offs.

Our results show that education-facing model quality is not captured by general capability alone. The model with the strongest general capability score is not the strongest on safety, and the models that perform well on safety do not necessarily lead on high-level educational alignment. No reported model dominates all four modules. These findings suggest that model selection for educational use should be module-aware: a tutoring system, a content-generation tool, and a safety-sensitive student-facing assistant may require different trade-offs among capability, safety, and educational alignment.

This paper makes four contributions. First, we propose ELBench, a benchmark that evaluates education-facing LLMs across four complementary dimensions. Second, we define a task taxonomy that integrates general capability, safety and trustworthiness, basic education, and high-level educational alignment. Third, we evaluate representative models under a deterministic zero-shot protocol and report both overall and module-level results. Fourth, we show that cross-module trade-offs are substantial, which motivates benchmark designs that support deployment-oriented model selection rather than single-axis ranking.

## 2. Related Work

### 2.1 General and Holistic LLM Benchmarks

General LLM benchmarks have shaped how the field measures model capability. BIG-bench collects a broad set of tasks to probe behaviors that are difficult to capture with narrow evaluation suites \cite{srivastava2022bigbench}. HELM argues for holistic evaluation by organizing evaluation around scenarios, metrics, and models, showing that accuracy alone cannot characterize model behavior \cite{liang2022helm}. These benchmarks establish an important premise for ELBench: model evaluation should expose trade-offs rather than collapse performance into a single generic score. However, their primary goal is broad model assessment, not education-facing deployment. ELBench adopts the multi-axis spirit of holistic evaluation but specializes the axes around educational use: general capability, safety and trustworthiness, basic education, and high-level educational alignment.

### 2.2 Safety and Trustworthiness Evaluation

Safety evaluation examines whether models avoid harmful, illegal, misleading, or otherwise risky outputs. SafetyBench provides a structured benchmark for evaluating safety across risk categories and languages \cite{zhang2024safetybench}. Related safety work has also studied refusal behavior, jailbreak vulnerability, and alignment failures under adversarial prompts. These evaluations are necessary for education because students may ask unsafe questions, frame harmful requests as learning tasks, or seek assistance in sensitive contexts. ELBench differs from standalone safety benchmarks by embedding safety within a broader education-facing evaluation. In ELBench, safety is one dimension of model readiness, and its relationship to general capability and educational alignment is an object of analysis rather than a separate leaderboard.

### 2.3 Chinese and Domain-Specific Evaluation

Language and domain coverage affect the validity of LLM evaluation. C-Eval provides a Chinese multi-level, multi-discipline evaluation suite and shows that Chinese-domain assessment cannot be reduced to English-centric benchmarks \cite{huang2023ceval}. This concern is relevant for educational models because subject matter, curriculum conventions, safety norms, and classroom practices vary across linguistic and institutional contexts. ELBench includes Chinese and education-facing tasks while also incorporating widely used general benchmarks. This design supports comparison across model families without treating general English performance as a sufficient proxy for educational readiness.

### 2.4 Educational LLM Evaluation

Educational LLM benchmarks evaluate whether models can perform tasks that matter in learning environments. EduBench evaluates large language models across diverse educational scenarios \cite{xu2025edubench}. K-12EduBench focuses on K-12 educational evaluation and reflects the growing need to test models in classroom-relevant settings \cite{k12edubench2026}. EduGuardBench further highlights the interaction between pedagogical fidelity and adversarial safety in simulated teacher roles \cite{jiang2026eduguardbench}. These works move beyond generic question answering toward educationally meaningful evaluation. ELBench builds on this direction but uses a broader four-module structure. Rather than evaluating education tasks alone or safety tasks alone, ELBench places educational quality alongside general capability and safety, enabling direct analysis of how these dimensions align or diverge across models.

## 3. ELBench

ELBench is designed to evaluate whether a language model is suitable for education-facing deployment. The benchmark is organized around four modules: General Capability, Safety and Trustworthiness, Basic Education, and High-Level Educational Alignment. This structure reflects a simple premise: a useful educational model must be capable, safe, instructionally useful, and aligned with broader pedagogical goals. These requirements are related but not interchangeable. ELBench therefore reports both aggregate performance and module-level scores.

### 3.1 Design Principles

ELBench follows four design principles. First, education-facing evaluation should be multi-dimensional. A model that answers factual questions correctly may still be unsafe or pedagogically weak, while a model that is safe may not provide useful educational support. Second, the benchmark should combine closed-form and open-ended tasks. Some abilities, such as multiple-choice reasoning or mathematical answer extraction, can be evaluated with reference-based scoring. Other abilities, such as safe redirection or instructional quality, require rubric-based judgment. Third, the benchmark should support deployment-oriented model selection. Rather than treating the overall score as the only outcome, ELBench uses module-level profiles to reveal which models are better suited for different educational use cases. Fourth, sensitive safety content should be handled responsibly. The paper reports task categories and aggregate results rather than exposing harmful prompts in full.

### 3.2 Benchmark Taxonomy

The General Capability module evaluates foundational model abilities that remain necessary in educational settings. It includes subject knowledge, instruction following, mathematical reasoning, and competition-style problem solving. These tasks provide a baseline for whether a model can handle the kinds of factual and reasoning demands that appear in educational use.

The Safety and Trustworthiness module evaluates whether a model behaves safely when facing unsafe, adversarial, or normatively sensitive educational inputs. The module includes refusal-oriented tasks, safe guidance tasks, benign-answering tasks, teaching-safety tasks, and adversarial safety tasks. This module distinguishes safe refusal from over-refusal: an education-facing model should refuse unsafe requests, redirect harmful requests constructively when appropriate, and still answer benign educational questions normally.

The Basic Education module evaluates practical teaching behaviors. It includes knowledge point explanation, contextualized question generation, interdisciplinary lesson planning, and guided problem-solving teaching. These tasks are closer to classroom support than ordinary benchmark questions because they test whether the model can produce outputs that are usable for instruction.

The High-Level Educational Alignment module evaluates broader educational reasoning and alignment. It includes open-ended educational judgment tasks and structured educational alignment tasks. This module is intended to capture whether a model's responses satisfy higher-level pedagogical expectations, not only whether they are factually correct or safe.

### 3.3 Task Composition

Table 1 summarizes the benchmark composition. Each reported model is evaluated on 2,942 samples. The largest modules are Safety and Trustworthiness and High-Level Educational Alignment, each containing 1,000 samples. General Capability contains 897 samples, and Basic Education contains 45 scenario-based samples.

| Module | Sample count | Task families | Evaluation type |
|---|---:|---|---|
| General Capability | 897 | knowledge, instruction following, mathematical reasoning, competition-style problem solving | reference-based and rule-based scoring |
| Safety and Trustworthiness | 1,000 | refusal, safe guidance, benign answering, teaching safety, adversarial safety | rule-based and rubric-based scoring |
| Basic Education | 45 | knowledge explanation, question generation, interdisciplinary lesson planning, guided problem solving | rubric-based scoring |
| High-Level Educational Alignment | 1,000 | educational judgment and high-level alignment tasks | reference-based and rubric-based scoring |

The module sizes reflect different task types. General and high-level modules contain many single-turn samples. The basic education module contains fewer samples because its scenarios are richer and require evaluating teacher-like outputs rather than only short answers. ELBench reports the module size explicitly so that score interpretation remains transparent.

### 3.4 Scoring Protocol

ELBench uses task-appropriate scoring. Closed-form tasks are evaluated by comparing the model output with a reference answer or by applying deterministic task-specific checks. For multi-select teaching-safety tasks, an exact option-set match receives 1 point, a non-empty answer that only omits correct options receives 0.5 points, and any answer containing an incorrect option receives 0 points. Open-ended tasks are evaluated using rubric-based judging. Scores are normalized to a percentage scale for each module. The overall ELBench score is computed from the four module scores, while module-level results are retained for analysis.

This scoring design is important because education-facing evaluation cannot rely on a single scoring mechanism. Mathematical problem solving, instruction following, safe refusal, teaching quality, and educational alignment require different evidence. ELBench therefore treats scoring as part of the benchmark design rather than an implementation detail.

## 4. Experiments

### 4.1 Evaluated Models

We evaluate nine representative models that cover international frontier models, Chinese frontier models, and education- or safety-oriented model variants. The evaluated models are Claude Opus 4.8, DeepSeek V4 Pro, Gemini 3.5 Flash, DeepSeek V4 Flash, Doubao Seed 2.0 Pro, GPT-5.4, Safe-InnoSpark, InnoSpark-235B, and GLM-5.1. This model set is intended to support comparative analysis across model families and deployment orientations. It is not intended to be exhaustive.

### 4.2 Evaluation Setup

All models are evaluated on the same ELBench task set. Following EduGuardBench, all experiments are conducted in a zero-shot setting with greedy decoding or temperature 0 to ensure deterministic and reproducible results \cite{jiang2026eduguardbench}. Each reported model is evaluated on 2,942 samples. The evaluation uses the task-specific scoring protocol described in Section 3.4, with reference-based or rule-based scoring for closed-form tasks and rubric-based judging for open-ended educational and safety tasks.

### 4.3 Metrics

We report four module scores: General Capability, Safety and Trustworthiness, Basic Education, and High-Level Educational Alignment. Each module score is normalized to a percentage scale. We also report an overall ELBench score, which summarizes performance across all four modules, and a non-safety score, which summarizes performance on General Capability, Basic Education, and High-Level Educational Alignment. The non-safety score is included to show how rankings change when safety is separated from other education-facing abilities.

## 5. Results

### 5.1 Overall Leaderboard

Table 2 reports the overall ELBench leaderboard. Claude Opus 4.8 achieves the highest overall score at 77.38%, followed by DeepSeek V4 Pro at 76.56% and Gemini 3.5 Flash at 75.71%. The difference between the overall score and the non-safety score is informative. Gemini 3.5 Flash obtains the highest non-safety score at 78.44%, but ranks third overall because its safety score is substantially lower than its general capability and high-level education scores. This pattern illustrates why education-facing evaluation should not rely only on general or non-safety performance.

| Rank | Model | Overall | Non-safety | General | Safety | Basic Edu. | High-level Edu. |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Claude Opus 4.8 | 77.38% | 77.92% | 91.86% | 75.75% | 84.89% | 57.00% |
| 2 | DeepSeek V4 Pro | 76.56% | 73.64% | 88.07% | 85.30% | 74.95% | 57.90% |
| 3 | Gemini 3.5 Flash | 75.71% | 78.44% | 93.42% | 67.50% | 66.61% | 75.30% |
| 4 | DeepSeek V4 Flash | 75.53% | 70.98% | 87.85% | 89.20% | 68.29% | 56.80% |
| 5 | Doubao Seed 2.0 Pro | 75.26% | 73.29% | 86.62% | 81.15% | 71.56% | 61.70% |
| 6 | GPT-5.4 | 73.07% | 72.56% | 86.40% | 74.60% | 56.18% | 75.10% |
| 7 | Safe-InnoSpark | 72.62% | 67.82% | 68.00% | 87.05% | 70.24% | 65.20% |
| 8 | InnoSpark-235B | 71.97% | 70.59% | 74.25% | 76.10% | 71.62% | 65.90% |
| 9 | GLM-5.1 | 71.91% | 66.17% | 82.72% | 89.10% | 56.20% | 59.60% |

### 5.2 General Capability

General Capability is led by Gemini 3.5 Flash with 93.42%, followed by Claude Opus 4.8 with 91.86% and DeepSeek V4 Pro with 88.07%. Several other models also perform strongly on this module, including DeepSeek V4 Flash, Doubao Seed 2.0 Pro, and GPT-5.4. These results show that the top models can handle standard knowledge, reasoning, instruction-following, and mathematical tasks at a high level. However, the General Capability ranking does not match the overall ranking. The model with the highest General Capability score does not rank first overall, which indicates that other modules contribute materially to education-facing evaluation.

### 5.3 Safety and Trustworthiness

Safety and Trustworthiness produces a different ordering. DeepSeek V4 Flash obtains the highest safety score at 89.20%, followed by GLM-5.1 at 89.10% and Safe-InnoSpark at 87.05%. DeepSeek V4 Pro also performs strongly at 85.30%. In contrast, Gemini 3.5 Flash, despite leading General Capability, obtains 67.50% on Safety and Trustworthiness. This module therefore reveals a capability-safety gap: high performance on general tasks does not imply safe behavior under education-facing safety conditions.

### 5.4 Basic Education

Basic Education is led by Claude Opus 4.8 with 84.89%, followed by DeepSeek V4 Pro with 74.95%, InnoSpark-235B with 71.62%, and Doubao Seed 2.0 Pro with 71.56%. These results differ from both the General Capability and Safety rankings. Basic Education evaluates teacher-like behaviors rather than ordinary answer generation, and the score distribution suggests that practical instructional performance remains a separate axis of evaluation.

### 5.5 High-Level Educational Alignment

High-Level Educational Alignment is led by Gemini 3.5 Flash with 75.30%, closely followed by GPT-5.4 with 75.10%. The next group includes Safe-InnoSpark, InnoSpark-235B, and Doubao Seed 2.0 Pro. Claude Opus 4.8 ranks first overall but scores 57.00% on this module, while DeepSeek V4 Pro scores 57.90%. These differences show that high-level educational alignment is not reducible to either overall performance or general reasoning strength.

### 5.6 Cross-Module Trade-Offs

The module-level results reveal three trade-offs. First, general capability and safety are not aligned: Gemini 3.5 Flash has the strongest General Capability score but the lowest Safety and Trustworthiness score among the reported models. Second, safety and educational alignment are distinct: DeepSeek V4 Flash, Safe-InnoSpark, and GLM-5.1 perform strongly on Safety and Trustworthiness, but none of them leads High-Level Educational Alignment. Third, practical teaching performance is separate from both general reasoning and high-level alignment: Claude Opus 4.8 leads Basic Education and the overall leaderboard, while Gemini 3.5 Flash leads High-Level Educational Alignment. These patterns support ELBench's central premise that education-facing model selection requires module-level profiles rather than a single general benchmark score.

## 6. Analysis

### 6.1 General Capability Is Not Sufficient

The results show that general capability is necessary but insufficient for education-facing evaluation. Gemini 3.5 Flash leads the General Capability module with 93.42%, but its Safety and Trustworthiness score is 67.50%, the lowest among the reported models. Conversely, Safe-InnoSpark and GLM-5.1 perform strongly on Safety and Trustworthiness but rank lower on General Capability and overall score. This mismatch suggests that general benchmark performance cannot be used as a proxy for educational deployment readiness.

This finding matters because education-facing systems often require models to operate under competing objectives. A model must provide useful knowledge and reasoning support, but it must also refuse unsafe requests, handle benign requests without over-refusal, and produce instructionally appropriate outputs. A single capability-oriented score hides these distinctions. ELBench makes the mismatch visible by reporting module-level scores alongside the overall score.

### 6.2 Safety and Educational Alignment Are Distinct

Safety and educational alignment also diverge. DeepSeek V4 Flash, Safe-InnoSpark, and GLM-5.1 are among the strongest models on Safety and Trustworthiness, but none of them leads High-Level Educational Alignment. Gemini 3.5 Flash and GPT-5.4 lead the high-level education module, but they do not lead the safety module. This pattern indicates that safe behavior and pedagogical alignment should be evaluated separately.

The distinction is conceptually important. Safety evaluation asks whether a model avoids or redirects harmful behavior. Educational alignment asks whether the model's response supports educational goals, reasoning quality, and pedagogical appropriateness. A safe answer can still be pedagogically weak, and a pedagogically rich answer can still fail under safety constraints. Treating these dimensions separately allows ELBench to identify models that are suitable for different educational roles.

### 6.3 Implications for Model Selection

The module-level results support deployment-aware model selection. For applications that prioritize open-ended educational reasoning, the high-level education score may be more informative than the general capability score. For student-facing systems in sensitive contexts, Safety and Trustworthiness should receive greater weight. For teacher-support tools such as explanation generation or lesson planning, Basic Education provides a more direct measure of practical instructional usefulness.

No reported model dominates all four modules. Claude Opus 4.8 ranks first overall and leads Basic Education, but it does not lead High-Level Educational Alignment or Safety and Trustworthiness. Gemini 3.5 Flash leads General Capability and High-Level Educational Alignment but underperforms on Safety and Trustworthiness. DeepSeek V4 Flash performs strongly on safety but does not lead the educational modules. These trade-offs suggest that education-facing model evaluation should be treated as a profile-matching problem rather than a search for a universally best model.

## 7. Limitations and Ethical Considerations

ELBench has several limitations. First, the module sizes are not uniform. General Capability, Safety and Trustworthiness, and High-Level Educational Alignment contain hundreds or thousands of samples, while Basic Education contains 45 scenario-based samples. The smaller size of the Basic Education module reflects the richer structure of its teaching scenarios, but it also means that Basic Education scores should be interpreted with this difference in mind.

Second, open-ended educational and safety tasks require rubric-based judgment. This is unavoidable for tasks where there is no single reference answer, but it also introduces dependence on the quality of the rubric and judging procedure. ELBench therefore treats open-ended evaluation as a necessary but imperfect measurement strategy. Future work should incorporate stronger human validation, judge calibration, and inter-rater agreement analysis.

Third, ELBench is currently text-based. Many educational settings involve diagrams, handwriting, speech, images, classroom interaction, or multimodal feedback. Extending ELBench to multimodal educational tasks would make the benchmark more representative of real learning environments.

Fourth, the model set is representative rather than exhaustive. The reported models cover several frontier, Chinese, and education- or safety-oriented systems, but the LLM ecosystem changes quickly. Future evaluations should update the model set and include open-weight models, domain-specialized models, and additional deployment configurations.

Finally, safety data must be handled responsibly. ELBench includes safety and adversarial tasks because education-facing models must be evaluated under risk. However, releasing harmful prompts without safeguards may create misuse risks. The paper therefore reports aggregate results and task categories, while detailed examples should be redacted or released under appropriate controls.

## 8. Conclusion

We presented ELBench, a four-module benchmark for evaluating education-facing large language models. ELBench combines General Capability, Safety and Trustworthiness, Basic Education, and High-Level Educational Alignment into a single evaluation framework with 2,942 samples per reported model. This design reflects the view that educational deployment requires more than accurate answer generation.

Our evaluation of nine representative models shows clear cross-module trade-offs. The strongest model on general capability is not the strongest on safety, safety-oriented models do not necessarily lead educational alignment, and no reported model dominates all four modules. These findings support module-aware evaluation for educational model selection. Rather than relying on a single generic benchmark score, practitioners and researchers should examine whether a model's capability, safety, and educational alignment match the intended deployment context.

ELBench provides a foundation for such evaluation. Future work should expand the benchmark across more educational scenarios, add multimodal tasks, strengthen human validation for open-ended judgments, and update the model set as new systems become available.
