import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os

os.makedirs('data/weights/models', exist_ok=True)
    os.makedirs('data/weights/sector_weights', exist_ok=True)
    #, exist_ok=True)

# ---------------------------------------------------------
# 1. DATA PREPARATION
# ---------------------------------------------------------
print("Loading datasets...")
brsr_df = pd.read_csv('data/processed/consolidated/brsr_consolidated.csv', low_memory=False)
scores_df = pd.read_csv('data/reference/scores/nsral_scores_full.csv')

brsr_df['clean_name'] = brsr_df['CompanyName'].astype(str).str.strip().str.lower()
scores_df['clean_name'] = scores_df['Company Name'].astype(str).str.strip().str.lower()

merged_df = pd.merge(brsr_df, scores_df, on='clean_name', how='inner')
print(f"Merged Data: {len(merged_df)} companies.")

exclude_cols = ['clean_name', 'CompanyName', 'Company Name', 'Sector', 'Basic Industry', 'ESG Ratings', 'Last Updated on']
numeric_cols = [c for c in brsr_df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(brsr_df[c])]

X_numeric = merged_df[numeric_cols].fillna(0).values

# Scale numeric inputs before gating
scaler = StandardScaler()
X_numeric = scaler.fit_transform(X_numeric)

# Extract One-Hot Industry array
industry_dummies = pd.get_dummies(merged_df['Basic Industry'], dummy_na=False).values
num_industries = industry_dummies.shape[1]

y = merged_df['ESG Ratings'].values.astype(np.float32).reshape(-1, 1)

# Split indices instead of data directly so we can separate X and Industry inputs
indices = np.arange(len(merged_df))
train_idx, test_idx = train_test_split(indices, test_size=0.15, random_state=42)

X_train_num = torch.tensor(X_numeric[train_idx], dtype=torch.float32)
X_test_num = torch.tensor(X_numeric[test_idx], dtype=torch.float32)

X_train_ind = torch.tensor(industry_dummies[train_idx], dtype=torch.float32)
X_test_ind = torch.tensor(industry_dummies[test_idx], dtype=torch.float32)

y_train = torch.tensor(y[train_idx], dtype=torch.float32)
y_test = torch.tensor(y[test_idx], dtype=torch.float32)

# ---------------------------------------------------------
# 2. ARCHITECTURE: Low-Rank Industry Gating (FiLM)
# ---------------------------------------------------------
class GatedHighDimPredictor(nn.Module):
    def __init__(self, num_features, num_industries, rank=8):
        super(GatedHighDimPredictor, self).__init__()
        
        # Industry Router with Low-Rank Bottleneck
        self.router_U = nn.Linear(num_industries, rank, bias=False)
        self.router_V = nn.Linear(rank, num_features, bias=True)
        
        # Soft-bounding parameters
        self.alpha = 2.0  # Controls the shift of the softplus
        
        # Main Predictive Network
        self.layer1 = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(p=0.4)
        )
        
        self.layer2 = nn.Sequential(
            nn.Linear(512, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(p=0.3)
        )
        
        self.output = nn.Linear(128, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x_num, x_ind):
        # 1. Generate Gating Multipliers
        latent_industry = self.router_U(x_ind)
        raw_gate = self.router_V(latent_industry)
        
        # Log-Normal Weight Soft-Bounding: 1 + softplus(x - alpha)
        # This keeps multipliers safely hovering around 1.0
        gate = 1.0 + F.softplus(raw_gate - self.alpha)
        
        # 2. Element-wise Multiplicative Gating
        x_gated = x_num * gate
        
        # 3. Main Network processing
        h1 = self.layer1(x_gated)
        h2 = self.layer2(h1)
        out = self.output(h2)
        
        final_score = self.sigmoid(out) * 100.0
        return final_score, h2, gate

num_features = X_numeric.shape[1]
model = GatedHighDimPredictor(num_features=num_features, num_industries=num_industries, rank=8)

# ---------------------------------------------------------
# 3. REGULARIZATION & OPTIMIZATION
# ---------------------------------------------------------
def decov_loss(hidden_activations):
    h = hidden_activations - hidden_activations.mean(dim=0, keepdim=True)
    cov = torch.mm(h.t(), h) / (h.size(0) - 1)
    diag = torch.diag(cov)
    cov_squared = torch.pow(cov, 2)
    diag_squared = torch.pow(diag, 2)
    return 0.5 * (torch.sum(cov_squared) - torch.sum(diag_squared))

# AdamW decoupled weight decay
optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
mse_criterion = nn.MSELoss()
decov_lambda = 0.1

# ---------------------------------------------------------
# 4. TRAINING LOOP
# ---------------------------------------------------------
epochs = 200
print(f"Beginning training on {len(X_train_num)} samples with {num_features} gated features...")

for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    
    predictions, hidden, gates = model(X_train_num, X_train_ind)
    
    # Calculate dual loss
    loss_mse = mse_criterion(predictions, y_train)
    loss_decov = decov_loss(hidden)
    
    # Optional: L2 penalty on the raw gate outputs to encourage 1.0 multipliers
    # handled implicitly by weight decay in AdamW, but we can add an anchor
    gate_anchor_loss = torch.mean((gates - 1.0)**2) * 0.05
    
    total_loss = loss_mse + (decov_lambda * loss_decov) + gate_anchor_loss
    
    total_loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 50 == 0:
        model.eval()
        with torch.no_grad():
            test_preds, _, _ = model(X_test_num, X_test_ind)
            test_mse = mse_criterion(test_preds, y_test)
            print(f"Epoch [{epoch+1}/{epochs}] | Train MSE: {loss_mse.item():.2f} | Test MSE: {test_mse.item():.2f}")

# ---------------------------------------------------------
# 5. SAVING & VALIDATION
# ---------------------------------------------------------
torch.save(model.state_dict(), 'data/weights/models/esg_network_gated.pt')
print("✅ Advanced Gated Model successfully saved to 'data/weights/models/esg_network_gated.pt'")

model.eval()
with torch.no_grad():
    sample_preds, _, sample_gates = model(X_test_num[:5], X_test_ind[:5])
    actuals = y_test[:5]
    print("\nSample Validation Results:")
    for i in range(5):
        print(f"Predicted Score: {sample_preds[i].item():.1f} | Actual Official Score: {actuals[i].item():.1f}")
        
    print(f"\nAverage Multiplier Value: {sample_gates.mean().item():.3f} (Expected ~1.0)")
