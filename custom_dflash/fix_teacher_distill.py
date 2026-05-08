#!/usr/bin/env python3
import torch, torch.nn.functional as F

# Test vocab mismatch fix
student_vocab = 248077
teacher_vocab = 248320

# Load a teacher output
t_data = torch.load('/data/SpecForge/custom_dflash/teacher_outputs/teacher_logits_0000.pt', map_location='cpu')
teacher_logits = t_data['logits']  # [1, 256, 248320]

print('Teacher logits shape:', teacher_logits.shape)
print('Student vocab:', student_vocab)
print('Teacher vocab:', teacher_vocab)

# Fix: truncate teacher logits to student vocab size
if teacher_logits.shape[-1] > student_vocab:
    teacher_logits = teacher_logits[:, :, :student_vocab]
    print('Truncated teacher logits to:', teacher_logits.shape)
elif teacher_logits.shape[-1] < student_vocab:
    # Pad with zeros
    pad_size = student_vocab - teacher_logits.shape[-1]
    padding = torch.zeros(*teacher_logits.shape[:-1], pad_size)
    teacher_logits = torch.cat([teacher_logits, padding], dim=-1)
    print('Padded teacher logits to:', teacher_logits.shape)

# Test temperature scaling
TEMP = 2.0
student_logits = torch.randn(1, 256, student_vocab)

student_probs = F.log_softmax(student_logits / TEMP, dim=-1)
teacher_probs = F.softmax(teacher_logits / TEMP, dim=-1)

# Add epsilon to prevent log(0)
teacher_probs = teacher_probs + 1e-10
teacher_probs = teacher_probs / teacher_probs.sum(dim=-1, keepdim=True)

kl_loss = F.kl_div(student_probs, teacher_probs, reduction='batchmean') * (TEMP ** 2)
print('KL loss:', kl_loss.item())
print('Fix works!')
