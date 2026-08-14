# Character-Level Language Model (Transformer, PyTorch)

A small GPT-style Transformer built from scratch in PyTorch, trained to generate
Shakespeare-style text one character at a time. This project focuses on
understanding *how* transformer-based language models work internally, not on
using a pre-built model.

## Objective

Build and train an autoregressive Transformer that predicts the next character
in a sequence, then use it to generate new, Shakespeare-style text — while
implementing every core Transformer component (embeddings, multi-head causal
self-attention, feed-forward layers) from first principles rather than using a
pre-built architecture.

## Dataset

- **Source:** *Tiny Shakespeare* — ~1.1 million characters of Shakespeare's plays
- **Vocabulary:** 65 unique characters (uppercase/lowercase letters, punctuation,
  spaces, newlines)
- **Split:** 90% train (~1,003,854 characters) / 10% validation (~111,540 characters)

## Why character-level, not word-level

Word-level models need a vocabulary of tens of thousands of words and large
embedding tables. Character-level models use a vocabulary of ~65 symbols,
which keeps the whole project small, fast to train, and easy to reason about —
while still using the exact same core architecture (attention, embeddings,
transformer blocks) that word/token-level models like GPT use.

## Architecture

| Component | Role |
|---|---|
| Token embedding | Converts each character ID into a learned vector |
| Position embedding | Tells the model *where* in the sequence each character sits |
| Multi-head causal self-attention | Each position looks back at earlier positions and learns which ones are relevant right now |
| Causal mask | Blocks every position from seeing future characters (upper-triangular mask set to `-inf` before softmax), so the model can only use past context — matching how it will actually be used at generation time |
| Feed-forward layer | Additional per-position processing after attention |
| Layer norm + residual connections | Stabilize training in a deep stack of blocks |
| LM head | Projects the final vector at each position into probabilities over the 65-character vocabulary |

**Model size:** 4 Transformer blocks, 4 attention heads, 64-dimensional embeddings,
32-character context window → **209,729 trainable parameters**.

*(For reference: production models like GPT-3 use the same core architecture at
~1,750x more layers and hundreds of billions of parameters, trained on
web-scale text for weeks on large GPU clusters.)*

## Training

- **Method:** standard supervised training loop — forward pass → compute
  cross-entropy loss → backward pass (compute gradients) → update weights (AdamW
  optimizer, learning rate 3e-3)
- **Steps:** 2,000 iterations, batch size 64, evaluated every 500 steps

| Step | Train loss | Val loss |
|---|---|---|
| 0 | 4.41 | 4.40 |
| 500 | 1.91 | 2.00 |
| 1,000 | 1.74 | 1.87 |
| 1,500 | 1.68 | 1.83 |
| 2,000 | **1.63** | **1.79** |

Loss dropped steadily and consistently on both train and validation sets, with
no sign of divergence between the two — indicating the model was learning
genuine patterns rather than memorizing the training text.

*(Reference point: a model that guesses uniformly at random over 65 characters
would have a loss of ln(65) ≈ 4.17 — matching our step-0 loss almost exactly,
confirming the model starts from a genuinely untrained state and improves from there.)*

## Sample output (after training)

```
Then, bods, and thought less? tive me! like hold as t;
Elongleat leypsal here Signt thee time, but ploovish their gracies:
Have I shall ind it mepence, and urther but this far roice heard with shap!

MENENIUS:
Ely man:
I will shem, to meadd, let
have, and will I now way they creep infided.
```

The model has learned:
- Play-script formatting (character names in capitals, followed by a colon —
  e.g. `MENENIUS:`), despite never being told this structure explicitly
- Plausible word shapes and common English letter patterns
- Sensible use of punctuation (colons, exclamation marks, line breaks) in
  contextually reasonable places

It has **not** yet learned full grammatical coherence or real vocabulary
consistency — expected for a model this small, trained this briefly, on CPU.

## Limitations

- **Scale:** 210K parameters and 2,000 training steps is tiny by modern
  standards; output is structurally plausible but not fluent
- **Character-level, not word-level:** the model has no concept of "words" as
  units — it only ever predicts one character at a time, which limits
  long-range coherence
- **No hyperparameter search:** learning rate, model size, and context window
  were chosen as reasonable defaults, not tuned for optimal performance
- **CPU-trained:** training was capped in duration to run practically on CPU;
  a GPU and longer training would substantially improve output quality

## How to run

```bash
# 1. Train the model (also generates a sample at the end)
python src/train.py

# Outputs:
#   outputs/char_transformer.pt   — saved model weights + tokenizer vocabulary
```

## Files

```
char_lm_project/
├── data/
│   └── input.txt              # Tiny Shakespeare training text
├── src/
│   ├── tokenizer.py           # Character <-> integer conversion, batching
│   ├── model.py                # Transformer architecture (attention, masking, etc.)
│   └── train.py                 # Training loop, loss tracking, text generation
└── outputs/
    └── char_transformer.pt    # Trained model weights
```
