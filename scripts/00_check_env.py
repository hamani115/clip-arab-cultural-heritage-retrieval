#!/usr/bin/env python3
import torch
import open_clip

print('PyTorch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('CUDA device:', torch.cuda.get_device_name(0))
print('OpenCLIP available models sample:')
print(open_clip.list_pretrained()[:5])
