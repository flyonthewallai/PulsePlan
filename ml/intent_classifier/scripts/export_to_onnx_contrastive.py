"""
ONNX Export for Contrastive Intent Classifier

Exports the embedding model (without classification head) to ONNX format.
Inference uses cosine similarity with cached intent embeddings.
"""

import json
from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import onnx


def export_to_onnx(
    model_path: str,
    output_path: str,
    opset_version: int = 14
) -> None:
    """
    Export SentenceTransformer model to ONNX format.

    Args:
        model_path: Path to trained SentenceTransformer model
        output_path: Path to save ONNX model
        opset_version: ONNX opset version
    """
    print(f"Loading model from {model_path}")
    model = SentenceTransformer(model_path)

    # Get underlying transformers model
    transformer_model = model[0].auto_model
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    print("Converting to ONNX...")

    # Dummy input for export
    dummy_input = tokenizer(
        "This is a sample sentence",
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128
    )

    # Export to ONNX
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        transformer_model,
        args=(
            dummy_input["input_ids"],
            dummy_input["attention_mask"]
        ),
        f=output_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "last_hidden_state": {0: "batch_size", 1: "sequence_length"}
        },
        opset_version=opset_version,
        do_constant_folding=True
    )

    print(f"ONNX model exported to {output_path}")

    # Verify the model
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    print("ONNX model verified successfully")

    # Save tokenizer
    tokenizer.save_pretrained(output_dir)
    print(f"Tokenizer saved to {output_dir}")


def quantize_onnx(
    onnx_path: str,
    quantized_path: str
) -> None:
    """
    Quantize ONNX model for faster CPU inference.

    Args:
        onnx_path: Path to ONNX model
        quantized_path: Path to save quantized model
    """
    from onnxruntime.quantization import quantize_dynamic, QuantType

    print(f"Quantizing model from {onnx_path}")

    quantize_dynamic(
        model_input=onnx_path,
        model_output=quantized_path,
        weight_type=QuantType.QUInt8,
        optimize_model=True
    )

    print(f"Quantized model saved to {quantized_path}")

    # Compare file sizes
    original_size = Path(onnx_path).stat().st_size / (1024 * 1024)
    quantized_size = Path(quantized_path).stat().st_size / (1024 * 1024)

    print(f"Original size: {original_size:.2f} MB")
    print(f"Quantized size: {quantized_size:.2f} MB")
    print(f"Compression ratio: {original_size / quantized_size:.2f}x")


def create_inference_config(
    output_dir: str,
    intent_specs_path: str,
    model_path: str
) -> None:
    """
    Create inference configuration for ONNX model.

    Args:
        output_dir: Directory containing ONNX model
        intent_specs_path: Path to intent_specs_embedded.json
        model_path: Path to original model
    """
    config = {
        "model_type": "contrastive_embedding",
        "onnx_model_path": str(Path(output_dir) / "model.onnx"),
        "quantized_model_path": str(Path(output_dir) / "model_quantized.onnx"),
        "tokenizer_path": output_dir,
        "intent_specs_path": intent_specs_path,
        "confidence_threshold": 0.5,
        "max_sequence_length": 128,
        "execution_providers": ["CPUExecutionProvider"],
        "pooling_strategy": "mean",  # Mean pooling over token embeddings
        "similarity_metric": "cosine"
    }

    config_path = Path(output_dir) / "inference_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Inference config saved to {config_path}")


def main():
    """Export contrastive model to ONNX."""
    import argparse

    parser = argparse.ArgumentParser(description="Export contrastive model to ONNX")
    parser.add_argument(
        "--model",
        type=str,
        default="ml/intent_classifier/outputs/contrastive_model",
        help="Path to trained model"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="ml/intent_classifier/onnx",
        help="Output directory for ONNX model"
    )
    parser.add_argument(
        "--specs",
        type=str,
        default="ml/intent_classifier/data/intent_specs_embedded.json",
        help="Path to intent specs"
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Also create quantized version"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    onnx_path = output_dir / "model.onnx"

    # Export to ONNX
    export_to_onnx(
        model_path=args.model,
        output_path=str(onnx_path),
        opset_version=14
    )

    # Quantize if requested
    if args.quantize:
        quantized_path = output_dir / "model_quantized.onnx"
        quantize_onnx(
            onnx_path=str(onnx_path),
            quantized_path=str(quantized_path)
        )

    # Create inference config
    create_inference_config(
        output_dir=str(output_dir),
        intent_specs_path=args.specs,
        model_path=args.model
    )

    print("\n" + "=" * 60)
    print("ONNX export completed successfully!")
    print(f"Model ready for deployment at: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
