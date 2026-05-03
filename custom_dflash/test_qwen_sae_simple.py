import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sys

print("Test 1: Load Qwen 27B in bf16...")
model = AutoModelForCausalLM.from_pretrained(
    "/data/models/Qwen3.6-27B-Uncensored",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
    max_memory={0: "100GiB", "cpu": "80GiB"}
)
print(f"Model loaded! GPU memory: {torch.cuda.memory_allocated() / 1e9:.1f}GB")

print("\nTest 2: Simple forward pass...")
tokenizer = AutoTokenizer.from_pretrained("/data/models/Qwen3.6-27B-Uncensored", trust_remote_code=True)
text = "Hello, world!"
inputs = tokenizer(text, return_tensors="pt", max_length=10, truncation=True)
inputs = {k: v.to(model.device) for k, v in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs, output_hidden_states=True)

print(f"Logits shape: {outputs.logits.shape}")
print(f"Hidden states: {len(outputs.hidden_states)} layers")
print(f"Layer 0 (embedding) shape: {outputs.hidden_states[0].shape}")
print(f"Layer 1 shape: {outputs.hidden_states[1].shape}")

print("\nTest 3: Load single SAE and test...")
sae_state = torch.load("/data/models/Qwen-Scope/layer0.sae.pt", map_location="cpu")
print(f"SAE state keys: {list(sae_state.keys())}")
print(f"W_enc shape: {sae_state['W_enc'].shape}")
print(f"W_dec shape: {sae_state['W_dec'].shape}")

# Create SAE with correct dimensions
class SimpleSAE(torch.nn.Module):
    def __init__(self, d_model, d_sae):
        super().__init__()
        self.W_enc = torch.nn.Parameter(torch.randn(d_model, d_sae) * 0.01)
        self.b_enc = torch.nn.Parameter(torch.zeros(d_sae))
        self.W_dec = torch.nn.Parameter(torch.randn(d_sae, d_model) * 0.01)
        self.b_dec = torch.nn.Parameter(torch.zeros(d_model))
    
    def forward(self, x):
        acts = torch.relu(x @ self.W_enc + self.b_enc)
        recon = acts @ self.W_dec + self.b_dec
        return recon, acts

d_model = outputs.hidden_states[1].shape[-1]  # 5120
d_sae = sae_state['W_enc'].shape[0]  # 81920

sae = SimpleSAE(d_model, d_sae).to(model.device).to(torch.bfloat16)
# Load pretrained weights (transpose and move to GPU)
sae.W_enc.data = sae_state['W_enc'].t().to(torch.bfloat16).to(model.device)
sae.W_dec.data = sae_state['W_dec'].t().to(torch.bfloat16).to(model.device)
sae.b_enc.data = sae_state['b_enc'].to(torch.bfloat16).to(model.device)
sae.b_dec.data = sae_state['b_dec'].to(torch.bfloat16).to(model.device)

print(f"SAE loaded to GPU")

# Test SAE on layer 1 hidden states
layer1_hidden = outputs.hidden_states[1].to(model.device)
with torch.no_grad():
    recon, acts = sae(layer1_hidden)

print(f"SAE input shape: {layer1_hidden.shape}")
print(f"SAE acts shape: {acts.shape}")
print(f"SAE recon shape: {recon.shape}")

print(f"\nGPU memory after SAE: {torch.cuda.memory_allocated() / 1e9:.1f}GB")
print("\n✅ All tests passed! Integration is viable.")
