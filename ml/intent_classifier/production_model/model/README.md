---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:23944
- loss:CosineSimilarityLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: Modify the schedule
  sentences:
  - restructure
  - Add graduation ceremony to my schedule
  - Query overdue items
- source_sentence: Contact IT about wifi password
  sentences:
  - make a task to review chapter 5
  - Nope
  - What's my streak?
- source_sentence: optimize my plan to prioritize urgent items
  sentences:
  - I need assistance
  - Draft message declining invitation
  - disable notifications
- source_sentence: Reserve time for gym workout this evening
  sentences:
  - update notification preferences
  - add birthday party saturday 7pm with location at main st
  - Grateful
- source_sentence: come again?
  sentences:
  - what can this app do?
  - Demo please
  - Show me everything due Friday
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- cosine_accuracy@1
- cosine_accuracy@3
- cosine_accuracy@5
- cosine_accuracy@10
- cosine_precision@1
- cosine_precision@3
- cosine_precision@5
- cosine_precision@10
- cosine_recall@1
- cosine_recall@3
- cosine_recall@5
- cosine_recall@10
- cosine_ndcg@10
- cosine_mrr@10
- cosine_map@100
model-index:
- name: SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2
  results:
  - task:
      type: information-retrieval
      name: Information Retrieval
    dataset:
      name: intent classification eval
      type: intent_classification_eval
    metrics:
    - type: cosine_accuracy@1
      value: 0.9545454545454546
      name: Cosine Accuracy@1
    - type: cosine_accuracy@3
      value: 0.9848484848484849
      name: Cosine Accuracy@3
    - type: cosine_accuracy@5
      value: 1.0
      name: Cosine Accuracy@5
    - type: cosine_accuracy@10
      value: 1.0
      name: Cosine Accuracy@10
    - type: cosine_precision@1
      value: 0.9545454545454546
      name: Cosine Precision@1
    - type: cosine_precision@3
      value: 0.32828282828282823
      name: Cosine Precision@3
    - type: cosine_precision@5
      value: 0.19999999999999996
      name: Cosine Precision@5
    - type: cosine_precision@10
      value: 0.09999999999999998
      name: Cosine Precision@10
    - type: cosine_recall@1
      value: 0.9545454545454546
      name: Cosine Recall@1
    - type: cosine_recall@3
      value: 0.9848484848484849
      name: Cosine Recall@3
    - type: cosine_recall@5
      value: 1.0
      name: Cosine Recall@5
    - type: cosine_recall@10
      value: 1.0
      name: Cosine Recall@10
    - type: cosine_ndcg@10
      value: 0.9795259441572343
      name: Cosine Ndcg@10
    - type: cosine_mrr@10
      value: 0.9727272727272728
      name: Cosine Mrr@10
    - type: cosine_map@100
      value: 0.9727272727272728
      name: Cosine Map@100
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 256, 'do_lower_case': False, 'architecture': 'BertModel'})
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'come again?',
    'what can this app do?',
    'Demo please',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[ 1.0000, -0.0306, -0.0248],
#         [-0.0306,  1.0000, -0.0076],
#         [-0.0248, -0.0076,  1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Information Retrieval

* Dataset: `intent_classification_eval`
* Evaluated with [<code>InformationRetrievalEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.evaluation.InformationRetrievalEvaluator)

| Metric              | Value      |
|:--------------------|:-----------|
| cosine_accuracy@1   | 0.9545     |
| cosine_accuracy@3   | 0.9848     |
| cosine_accuracy@5   | 1.0        |
| cosine_accuracy@10  | 1.0        |
| cosine_precision@1  | 0.9545     |
| cosine_precision@3  | 0.3283     |
| cosine_precision@5  | 0.2        |
| cosine_precision@10 | 0.1        |
| cosine_recall@1     | 0.9545     |
| cosine_recall@3     | 0.9848     |
| cosine_recall@5     | 1.0        |
| cosine_recall@10    | 1.0        |
| **cosine_ndcg@10**  | **0.9795** |
| cosine_mrr@10       | 0.9727     |
| cosine_map@100      | 0.9727     |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 23,944 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                      | sentence_1                                                                       | label                                                          |
  |:--------|:--------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                          | string                                                                           | float                                                          |
  | details | <ul><li>min: 3 tokens</li><li>mean: 7.2 tokens</li><li>max: 36 tokens</li></ul> | <ul><li>min: 3 tokens</li><li>mean: 6.91 tokens</li><li>max: 36 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.27</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                             | sentence_1                                                  | label            |
  |:-------------------------------------------------------|:------------------------------------------------------------|:-----------------|
  | <code>Book a consultation with the professor</code>    | <code>i need to block out my mornings next week</code>      | <code>1.0</code> |
  | <code>Good afternoon</code>                            | <code>Forget it</code>                                      | <code>0.0</code> |
  | <code>Set up weekly review session every Monday</code> | <code>Book conference room for presentation practice</code> | <code>1.0</code> |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `eval_strategy`: steps
- `per_device_train_batch_size`: 32
- `per_device_eval_batch_size`: 32
- `num_train_epochs`: 10
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: steps
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 32
- `per_device_eval_batch_size`: 32
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 10
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `project`: huggingface
- `trackio_space_id`: trackio
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: no
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: True
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step | Training Loss | intent_classification_eval_cosine_ndcg@10 |
|:------:|:----:|:-------------:|:-----------------------------------------:|
| 0.2670 | 200  | -             | 0.8995                                    |
| 0.5340 | 400  | -             | 0.9589                                    |
| 0.6676 | 500  | 0.0875        | -                                         |
| 0.8011 | 600  | -             | 0.9563                                    |
| 1.0    | 749  | -             | 0.9613                                    |
| 1.0681 | 800  | -             | 0.9625                                    |
| 1.3351 | 1000 | 0.0222        | 0.9731                                    |
| 1.6021 | 1200 | -             | 0.9787                                    |
| 1.8692 | 1400 | -             | 0.9784                                    |
| 2.0    | 1498 | -             | 0.9745                                    |
| 2.0027 | 1500 | 0.0088        | -                                         |
| 2.1362 | 1600 | -             | 0.9782                                    |
| 2.4032 | 1800 | -             | 0.9782                                    |
| 2.6702 | 2000 | 0.0041        | 0.9687                                    |
| 2.9372 | 2200 | -             | 0.9784                                    |
| 3.0    | 2247 | -             | 0.9687                                    |
| 3.2043 | 2400 | -             | 0.9687                                    |
| 3.3378 | 2500 | 0.0029        | -                                         |
| 3.4713 | 2600 | -             | 0.9782                                    |
| 3.7383 | 2800 | -             | 0.9782                                    |
| 4.0    | 2996 | -             | 0.9784                                    |
| 4.0053 | 3000 | 0.0023        | 0.9782                                    |
| 4.2724 | 3200 | -             | 0.9787                                    |
| 4.5394 | 3400 | -             | 0.9687                                    |
| 4.6729 | 3500 | 0.0019        | -                                         |
| 4.8064 | 3600 | -             | 0.9791                                    |
| 5.0    | 3745 | -             | 0.9692                                    |
| 5.0734 | 3800 | -             | 0.9784                                    |
| 5.3405 | 4000 | 0.0017        | 0.9795                                    |


### Framework Versions
- Python: 3.11.13
- Sentence Transformers: 5.1.2
- Transformers: 4.57.1
- PyTorch: 2.2.2
- Accelerate: 1.11.0
- Datasets: 4.3.0
- Tokenizers: 0.22.1

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->